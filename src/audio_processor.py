import sounddevice as sd
import numpy as np
import json
import os
import threading
import sys
from faster_whisper import WhisperModel
from constants import get_resource_path


class AudioProcessor:
    def __init__(self, model_size="medium", download_root=None):
        self.model_size = model_size
        self.download_root = download_root
        self.model = None
        self._load_lock = threading.Lock()
        self.fs = 16000  # Whisper expects 16kHz
        self.recording = False
        self.audio_data = []
        self._stream = None
        self.root_dir = get_resource_path("")
        self.config = self._load_config()

    def load_model(self, download_root=None):
        with self._load_lock:
            if self.model is None:
                path = download_root or self.download_root
                # Ensure path is absolute and exists
                path = os.path.abspath(path)
                os.makedirs(path, exist_ok=True)
                
                print(f"Loading Whisper model ({self.model_size}) from: {path}")
                try:
                    self.model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                        download_root=path,
                        num_workers=1,
                    )
                    print("Whisper model loaded successfully.")
                except Exception as e:
                    print(f"Error loading Whisper model from {path}: {e}")
                    raise e



    def _load_config(self):
        config_path = os.path.join(self.root_dir, "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config.json in AudioProcessor: {e}")
        return {}

    def _get_input_device(self):
        # Prefer the system default input (PipeWire/PulseAudio handles mixing and
        # sample-rate conversion). Raw hw: devices fail when PipeWire owns the hardware.
        default_idx = sd.default.device[0]
        if isinstance(default_idx, int) and default_idx >= 0:
            return default_idx

        devices = sd.query_devices()
        for keyword in ("pulse", "pipewire", "default"):
            for i, d in enumerate(devices):
                if d["max_input_channels"] > 0 and keyword in d["name"].lower():
                    return i

        return next(
            (i for i, d in enumerate(devices) if d["max_input_channels"] > 0), None
        )

    def start_recording(self):
        self.audio_data = []
        input_device = self._get_input_device()
        if input_device is None:
            raise RuntimeError(
                "No microphone detected. Please connect a microphone or check your permissions."
            )

        try:
            device_info = sd.query_devices(input_device)
            print(f"Recording: Starting on device '{device_info['name']}' at {self.fs}Hz")
        except Exception as e:
            print(f"Recording: Could not query device info: {e}")

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
            print("Transcription: Received None audio data.")
            return ""

        max_val = np.max(np.abs(audio_np)) if len(audio_np) > 0 else 0
        print(f"Transcription: Audio length={len(audio_np)}, Max amplitude={max_val:.5f}")

        if max_val < 0.001:
            print("Transcription: Audio level too low. This might be a microphone permission issue.")
            return ""

        if self.model is None:
            self.load_model()

        # Using initial_prompt to help with context and punctuation
        # vad_filter removes silence and noise
        segments, info = self.model.transcribe(
            audio_np,
            beam_size=5,
            language=self.config.get("lang_tts", "en"),
            vad_filter=True,
            initial_prompt="This is a conversation with an AI English tutor. The speaker is practicing their English.",
        )
        
        results = list(segments)
        print(f"Transcription: Found {len(results)} segments.")
        text = " ".join([segment.text for segment in results])
        return text.strip()

