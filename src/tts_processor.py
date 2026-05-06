import sounddevice as sd
from kokoro_onnx import Kokoro
import os
import requests
import numpy as np
import threading
import json


class TTSProcessor:
    def __init__(self, model_path=None, voices_path=None):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = model_path or os.path.join(self.root_dir, "kokoro-v1.0.onnx")
        self.voices_path = voices_path or os.path.join(self.root_dir, "voices-v1.0.bin")
        self.kokoro = None
        self.config = self._load_config()

        self._ensure_models_exist()

        try:
            self.kokoro = Kokoro(self.model_path, self.voices_path)
        except Exception as e:
            print(f"Error initializing Kokoro: {e}")

    def _load_config(self):
        config_path = os.path.join(self.root_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config.json: {e}")
        return {}

    def _ensure_models_exist(self):
        urls = {
            self.model_path: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            self.voices_path: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
        }

        for path, url in urls.items():
            if not os.path.exists(path):
                print(f"Downloading {path}...")
                response = requests.get(url, stream=True)
                with open(path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded {path}")

    def is_playing(self):
        return sd.get_stream().active if sd.get_stream() else False

    def stop(self):
        sd.stop()

    def generate(self, text, voice=None):
        if not self.kokoro:
            print("TTS not initialized.")
            return None, None

        voice = voice or self.config.get("tts_voice", "af_sarah")
        speed = self.config.get("tts_speed", 1.0)
        lang = self.config.get("lang", "en-us")

        try:
            samples, sample_rate = self.kokoro.create(
                text, voice=voice, speed=speed, lang=lang
            )
            return samples, sample_rate
        except Exception as e:
            print(f"Error in TTS generation: {e}")
            return None, None

    def play_samples(self, samples, sample_rate, on_finish=None):
        if samples is None:
            if on_finish:
                on_finish()
            return

        try:
            self.stop()
            output_device = sd.default.device[1]
            if output_device < 0:
                devices = sd.query_devices()
                output_device = next(
                    (i for i, d in enumerate(devices) if d["max_output_channels"] > 0),
                    None,
                )

            if output_device is not None:
                sd.play(samples, sample_rate, device=output_device)
            else:
                print("No output device found.")

            if on_finish:

                def wait_and_call():
                    sd.wait()
                    on_finish()

                threading.Thread(target=wait_and_call, daemon=True).start()
        except Exception as e:
            print(f"Error in TTS playback: {e}")
            if on_finish:
                on_finish()

    def speak(self, text, voice="af_sarah", on_finish=None):
        samples, sample_rate = self.generate(text, voice)
        self.play_samples(samples, sample_rate, on_finish)
