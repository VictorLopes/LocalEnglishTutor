import sounddevice as sd
import numpy as np
import json
import os
from faster_whisper import WhisperModel


class AudioProcessor:
    def __init__(self, model_size="base"):
        # Run on CPU. 'base' is more accurate than 'tiny' with low overhead.
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.fs = 16000  # Whisper expects 16kHz
        self.recording = False
        self.audio_data = []
        self._stream = None
        self.config = self._load_config()

    def _load_config(self):
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config.json in AudioProcessor: {e}")
        return {}

    def _get_input_device(self):
        devices = sd.query_devices()
        return next((i for i, d in enumerate(devices) if d['max_input_channels'] > 0), None)

    def start_recording(self):
        self.audio_data = []
        input_device = self._get_input_device()
        if input_device is None:
            raise RuntimeError("No microphone detected. Please connect a microphone or check your permissions.")
            
        self.recording = True
        self._stream = sd.InputStream(
            device=input_device, samplerate=self.fs, channels=1, callback=self._callback
        )
        self._stream.start()

    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.audio_data.append(indata.copy())

    def stop_recording(self):
        self.recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()

        if not self.audio_data:
            return None

        # Concatenate all blocks and normalize
        audio_np = np.concatenate(self.audio_data, axis=0).flatten()
        return audio_np

    def transcribe(self, audio_np):
        if audio_np is None:
            return ""

        # Using initial_prompt to help with context and punctuation
        # vad_filter removes silence and noise
        segments, info = self.model.transcribe(
            audio_np,
            beam_size=5,
            language=self.config.get("lang_tts", "en"),
            vad_filter=True,
            initial_prompt="This is a conversation with an AI English tutor. The speaker is practicing their English.",
        )
        text = " ".join([segment.text for segment in segments])
        return text.strip()
