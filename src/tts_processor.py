import sounddevice as sd
from kokoro_onnx import Kokoro
import os
import requests
import numpy as np
import threading
import json


class TTSProcessor:
    def __init__(self, models_dir=None):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.models_dir = models_dir or os.path.join(self.root_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)

        self.model_path = os.path.join(self.models_dir, "kokoro-v1.0.onnx")
        self.voices_path = os.path.join(self.models_dir, "voices-v1.0.bin")

        self.kokoro = None
        self._load_lock = threading.Lock()
        self.config = self._load_config()

    def load_model(self, progress_callback=None):
        with self._load_lock:
            if self.kokoro is None:
                self._ensure_models_exist(progress_callback)
                try:
                    if progress_callback:
                        progress_callback("Initializing speech engine...")
                    print(f"Initializing Kokoro with {self.model_path}...")
                    self.kokoro = Kokoro(self.model_path, self.voices_path)
                    print("Kokoro initialized.")
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

    def _ensure_models_exist(self, progress_callback=None):
        urls = {
            self.model_path: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            self.voices_path: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
        }

        for path, url in urls.items():
            if not os.path.exists(path):
                filename = os.path.basename(path)
                print(f"Downloading {filename}...")
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size > 0:
                                percent = int(downloaded / total_size * 100)
                                progress_callback(
                                    f"Downloading {filename}: {percent}%"
                                )
                print(f"Downloaded {path}")

    def is_playing(self):
        return sd.get_stream().active if sd.get_stream() else False

    def stop(self):
        sd.stop()

    def generate(self, text, voice=None, progress_callback=None):
        if self.kokoro is None:
            self.load_model(progress_callback)

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

    def speak(self, text, voice="af_sarah", on_finish=None, progress_callback=None):
        samples, sample_rate = self.generate(text, voice, progress_callback)
        self.play_samples(samples, sample_rate, on_finish)
