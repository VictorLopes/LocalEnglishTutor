"""
Teste funcional completo do pipeline de voz:
  1. Detecção de dispositivos de áudio
  2. Carregamento do modelo Whisper (STT)
  3. Transcrição de áudio sintético e real
  4. Comunicação com Ollama (LLM)
  5. Geração de voz com Kokoro (TTS)
  6. Reprodução de áudio

Execute: .venv/bin/python tests/test_voice_pipeline.py
"""
import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Suprime prints de diagnóstico do constants.py durante o import
import io
_buf = io.StringIO()
_real_stdout = sys.stdout
sys.stdout = _buf
from constants import get_data_path, get_resource_path
sys.stdout = _real_stdout

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
INFO = "\033[94mℹ\033[0m"

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print('='*55)

def ok(msg):    print(f"  {PASS} {msg}")
def fail(msg):  print(f"  {FAIL} {msg}")
def warn(msg):  print(f"  {WARN} {msg}")
def info(msg):  print(f"  {INFO} {msg}")

results = {"passed": 0, "failed": 0, "skipped": 0}

def check(label, fn):
    try:
        fn()
        ok(label)
        results["passed"] += 1
        return True
    except AssertionError as e:
        fail(f"{label}: {e}")
        results["failed"] += 1
        return False
    except Exception as e:
        fail(f"{label}: {type(e).__name__}: {e}")
        results["failed"] += 1
        return False

# ──────────────────────────────────────────────
# 1. DISPOSITIVOS DE ÁUDIO
# ──────────────────────────────────────────────
section("1. Dispositivos de Áudio")

import sounddevice as sd

def _check_input_device():
    devices = sd.query_devices()
    inputs = [d for d in devices if d["max_input_channels"] > 0]
    assert inputs, "Nenhum microfone encontrado"
    info(f"Microfone: {inputs[0]['name']} ({inputs[0]['max_input_channels']}ch)")

def _check_output_device():
    devices = sd.query_devices()
    outputs = [d for d in devices if d["max_output_channels"] > 0]
    assert outputs, "Nenhum dispositivo de saída encontrado"
    info(f"Saída: {outputs[0]['name']}")

check("Microfone detectado", _check_input_device)
check("Saída de áudio detectada", _check_output_device)

# ──────────────────────────────────────────────
# 2. MODELO WHISPER (STT)
# ──────────────────────────────────────────────
section("2. Modelo Whisper (Speech-to-Text)")

whisper_model = None

def _load_whisper():
    global whisper_model
    from audio_processor import AudioProcessor
    models_dir = get_data_path("models")
    info(f"Carregando Whisper medium de: {models_dir}")
    info("(pode baixar ~1.4 GB na primeira vez — aguarde...)")
    t0 = time.time()
    ap = AudioProcessor(model_size="medium", download_root=models_dir)
    ap.load_model(download_root=models_dir)
    whisper_model = ap
    elapsed = time.time() - t0
    info(f"Carregado em {elapsed:.1f}s")

check("Carregamento do Whisper medium", _load_whisper)

def _transcribe_silence():
    assert whisper_model is not None, "Whisper não carregado"
    silent = np.zeros(16000, dtype=np.float32)
    result = whisper_model.transcribe(silent)
    assert result == "", f"Esperava string vazia para silêncio, recebeu: {repr(result)}"
    info("Áudio silencioso → vazio (correto)")

def _transcribe_sine_tone():
    """Tom de 440 Hz gerado sinteticamente — Whisper não transcreverá como texto real."""
    assert whisper_model is not None, "Whisper não carregado"
    t = np.linspace(0, 2, 2 * 16000, dtype=np.float32)
    tone = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    result = whisper_model.transcribe(tone)
    assert isinstance(result, str), "transcribe() deve retornar string"
    info(f"Tom sintético transcrito como: {repr(result) if result else '(vazio)'}")

check("Transcrição de silêncio retorna vazio", _transcribe_silence)
check("Transcrição de tom sintético retorna string", _transcribe_sine_tone)

# ──────────────────────────────────────────────
# 3. OLLAMA / LLM
# ──────────────────────────────────────────────
section("3. Ollama LLM (sam860/lfm2.5:1.2b)")

import ollama as _ollama

def _check_ollama_connection():
    result = _ollama.list()
    assert result is not None
    info("Ollama está rodando")

def _check_model_available():
    result = _ollama.list()
    models = result.models if hasattr(result, "models") else result.get("models", [])
    names = [m.model if hasattr(m, "model") else m.get("name","") for m in models]
    model_name = "sam860/lfm2.5:1.2b"
    assert any(model_name in n for n in names), f"Modelo não encontrado. Disponíveis: {names}"
    info(f"Modelo {model_name} disponível")

def _check_llm_response():
    from chat_client import ChatClient
    client = ChatClient()
    client.set_system_prompt("A1", "Greetings")
    t0 = time.time()
    reply = client.get_initial_greeting()
    elapsed = time.time() - t0
    assert reply and "Error" not in reply, f"Resposta inválida: {reply}"
    info(f"Resposta ({elapsed:.1f}s): {reply[:80]}{'...' if len(reply)>80 else ''}")

check("Conexão com Ollama", _check_ollama_connection)
check("Modelo disponível localmente", _check_model_available)
check("LLM gera saudação inicial", _check_llm_response)

def _check_conversation_turn():
    from chat_client import ChatClient
    client = ChatClient(system_prompt="You are a concise English tutor.")
    t0 = time.time()
    reply = client.get_response("Say: hello in exactly one word.")
    elapsed = time.time() - t0
    assert reply and "Error" not in reply
    info(f"Resposta de conversa ({elapsed:.1f}s): {reply[:80]}")

check("LLM responde uma mensagem de texto", _check_conversation_turn)

# ──────────────────────────────────────────────
# 4. TTS (KOKORO)
# ──────────────────────────────────────────────
section("4. TTS Kokoro (Text-to-Speech)")

kokoro_models_dir = get_data_path("models")
model_onnx  = os.path.join(kokoro_models_dir, "kokoro-v1.0.onnx")
voices_bin  = os.path.join(kokoro_models_dir, "voices-v1.0.bin")

onnx_exists   = os.path.exists(model_onnx)
voices_exists = os.path.exists(voices_bin)

info(f"Pasta de modelos: {kokoro_models_dir}")
info(f"kokoro-v1.0.onnx : {'presente' if onnx_exists else 'AUSENTE'}")
info(f"voices-v1.0.bin  : {'presente' if voices_exists else 'AUSENTE'}")

tts = None

def _load_tts():
    global tts
    from tts_processor import TTSProcessor
    t = TTSProcessor(models_dir=kokoro_models_dir)
    if not onnx_exists or not voices_exists:
        info("Baixando modelos TTS (~300 MB + 11 MB)... aguarde...")
    t0 = time.time()
    t.load_model()
    elapsed = time.time() - t0
    assert t.kokoro is not None, "Kokoro não inicializou"
    tts = t
    info(f"Kokoro carregado em {elapsed:.1f}s")

check("Carregamento do Kokoro TTS", _load_tts)

def _generate_speech():
    assert tts is not None, "TTS não carregado"
    t0 = time.time()
    samples, rate = tts.generate("Hello! Let's practice English together.")
    elapsed = time.time() - t0
    assert samples is not None, "Geração retornou None"
    assert rate is not None and rate > 0
    assert len(samples) > 0
    duration = len(samples) / rate
    info(f"Áudio gerado em {elapsed:.1f}s | duração={duration:.2f}s | taxa={rate}Hz | amostras={len(samples)}")

def _play_generated_speech():
    assert tts is not None, "TTS não carregado"
    samples, rate = tts.generate("Great job! Keep practicing.")
    assert samples is not None
    finished = []
    tts.play_samples(samples, rate, on_finish=lambda: finished.append(True))
    # Aguarda reprodução terminar (max 10s)
    deadline = time.time() + 10
    while not finished and time.time() < deadline:
        time.sleep(0.1)
    assert finished, "Reprodução não finalizou em 10s"
    info("Áudio reproduzido com sucesso")

check("Geração de áudio TTS", _generate_speech)
check("Reprodução de áudio TTS", _play_generated_speech)

# ──────────────────────────────────────────────
# 5. PIPELINE COMPLETO: voz simulada → LLM → TTS
# ──────────────────────────────────────────────
section("5. Pipeline Completo (STT → LLM → TTS)")

def _full_pipeline():
    assert whisper_model is not None, "Whisper não carregado"
    assert tts is not None, "TTS não carregado"

    # Simula um texto transcrito (como se o usuário tivesse falado)
    simulated_transcription = "Can you tell me what I should say when I meet someone for the first time?"
    info(f"Texto simulado (STT): {simulated_transcription}")

    from chat_client import ChatClient
    client = ChatClient(system_prompt="You are a brief English tutor for A1 level.")

    t0 = time.time()
    llm_reply = client.get_response(simulated_transcription)
    llm_time = time.time() - t0
    assert llm_reply and "Error" not in llm_reply
    info(f"LLM ({llm_time:.1f}s): {llm_reply[:100]}{'...' if len(llm_reply)>100 else ''}")

    t0 = time.time()
    samples, rate = tts.generate(llm_reply)
    tts_time = time.time() - t0
    assert samples is not None
    duration = len(samples) / rate
    info(f"TTS ({tts_time:.1f}s): áudio de {duration:.2f}s gerado")
    info("Pipeline STT→LLM→TTS funcionando corretamente!")

check("Pipeline STT → LLM → TTS completo", _full_pipeline)

# ──────────────────────────────────────────────
# RESUMO
# ──────────────────────────────────────────────
section("RESUMO")
total = results["passed"] + results["failed"] + results["skipped"]
print(f"\n  {PASS} Passaram : {results['passed']}")
print(f"  {FAIL} Falharam : {results['failed']}")
print(f"  Total    : {total}")
if results["failed"] == 0:
    print(f"\n  \033[92mTodos os testes passaram! O pipeline de voz está funcionando.\033[0m")
else:
    print(f"\n  \033[91mAlguns testes falharam — verifique os detalhes acima.\033[0m")
print()
