import sys
import io
import threading
from datetime import datetime

class LogBuffer(io.StringIO):
    def __init__(self):
        super().__init__()
        self.logs = []
        self._lock = threading.Lock()

    def write(self, s):
        if s.strip():
            with self._lock:
                timestamp = datetime.now().strftime("%H:%M:%S")
                entry = f"[{timestamp}] {s.strip()}"
                self.logs.append(entry)
                # Keep only last 500 lines
                if len(self.logs) > 500:
                    self.logs.pop(0)
        return super().write(s)

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance.buffer = LogBuffer()
            cls._instance._stdout = sys.stdout
            cls._instance._stderr = sys.stderr
        return cls._instance

    def start_capturing(self):
        sys.stdout = self.buffer
        sys.stderr = self.buffer

    def stop_capturing(self):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

    def get_logs(self):
        return "\n".join(self.buffer.logs)

# Global instance
logger = Logger()
