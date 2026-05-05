import sounddevice as sd
from kokoro_onnx import Kokoro
import os
import requests
import numpy as np

class TTSProcessor:
    def __init__(self, model_path="kokoro-v1.0.onnx", voices_path="voices-v1.0.bin"):
        self.model_path = model_path
        self.voices_path = voices_path
        self.kokoro = None
        
        # Download models if they don't exist
        self._ensure_models_exist()
        
        try:
            self.kokoro = Kokoro(self.model_path, self.voices_path)
        except Exception as e:
            print(f"Error initializing Kokoro: {e}")

    def _ensure_models_exist(self):
        urls = {
            self.model_path: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
            self.voices_path: "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
        }
        
        for path, url in urls.items():
            if not os.path.exists(path):
                print(f"Downloading {path}...")
                response = requests.get(url, stream=True)
                with open(path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded {path}")

    def speak(self, text, voice="af_sarah"):
        if not self.kokoro:
            print("TTS not initialized.")
            return
        
        try:
            samples, sample_rate = self.kokoro.create(
                text,
                voice=voice,
                speed=1.0,
                lang="en-us"
            )
            # Play directly to speakers
            sd.play(samples, sample_rate)
            sd.wait()
        except Exception as e:
            print(f"Error in TTS: {e}")
