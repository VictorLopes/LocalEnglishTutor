"""Unit tests for TTSProcessor — Kokoro and sounddevice are mocked."""
import os
import pytest
from unittest.mock import patch, MagicMock, call
import numpy as np


@pytest.fixture
def processor(tmp_path):
    """TTSProcessor pointing at a temp models dir — no downloads."""
    with patch('tts_processor.sd'), \
         patch('tts_processor.Kokoro'):
        from tts_processor import TTSProcessor
        tp = TTSProcessor(models_dir=str(tmp_path / "models"))
        tp.kokoro = None
        return tp


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def test_config_loaded_on_init(processor):
    assert isinstance(processor.config, dict)


def test_config_has_tts_voice(processor):
    assert "tts_voice" in processor.config


def test_config_has_tts_speed(processor):
    assert "tts_speed" in processor.config


# ---------------------------------------------------------------------------
# Model paths
# ---------------------------------------------------------------------------

def test_model_path_ends_with_onnx(processor):
    assert processor.model_path.endswith(".onnx")


def test_voices_path_ends_with_bin(processor):
    assert processor.voices_path.endswith(".bin")


def test_models_dir_created(processor):
    assert os.path.isdir(processor.models_dir)


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------

def test_generate_returns_none_when_kokoro_unavailable(processor):
    # Simulate load_model silently failing: _ensure_models_exist does nothing,
    # Kokoro constructor raises internally → load_model catches it → kokoro stays None.
    with patch.object(processor, '_ensure_models_exist'), \
         patch('tts_processor.Kokoro', side_effect=Exception("init failed")):
        samples, rate = processor.generate("hello")
    assert samples is None
    assert rate is None


def test_generate_calls_kokoro_create(processor):
    mock_kokoro = MagicMock()
    mock_kokoro.create.return_value = (np.zeros(100), 24000)
    processor.kokoro = mock_kokoro

    samples, rate = processor.generate("Hello world")
    mock_kokoro.create.assert_called_once()
    assert rate == 24000


def test_generate_uses_config_voice(processor):
    mock_kokoro = MagicMock()
    mock_kokoro.create.return_value = (np.zeros(100), 24000)
    processor.kokoro = mock_kokoro
    processor.config["tts_voice"] = "af_sarah"

    processor.generate("test")
    _, kwargs = mock_kokoro.create.call_args
    assert kwargs.get("voice") == "af_sarah" or mock_kokoro.create.call_args[0][1] == "af_sarah"


# ---------------------------------------------------------------------------
# play_samples
# ---------------------------------------------------------------------------

def test_play_samples_calls_on_finish_when_samples_none(processor):
    finished = []
    processor.play_samples(None, 24000, on_finish=lambda: finished.append(True))
    assert finished == [True]


# ---------------------------------------------------------------------------
# speak
# ---------------------------------------------------------------------------

def test_speak_calls_generate_and_play(processor):
    with patch.object(processor, 'generate', return_value=(np.zeros(10), 22050)) as mock_gen, \
         patch.object(processor, 'play_samples') as mock_play:
        processor.speak("Hello")
    mock_gen.assert_called_once()
    mock_play.assert_called_once()
