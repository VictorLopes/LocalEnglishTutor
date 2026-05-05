import sounddevice as sd
import numpy as np
import io
from faster_whisper import WhisperModel
import threading
import queue

class AudioProcessor:
    def __init__(self, model_size="tiny"):
        # Run on CPU. 'tiny' is much faster than 'base'.
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.fs = 16000  # Whisper expects 16kHz
        self.recording = False
        self.audio_data = []
        self._stream = None

    def start_recording(self):
        self.audio_data = []
        self.recording = True
        self._stream = sd.InputStream(samplerate=self.fs, channels=1, callback=self._callback)
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
        
        segments, info = self.model.transcribe(audio_np, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
