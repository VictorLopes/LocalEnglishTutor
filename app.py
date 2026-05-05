import sys
import time
import threading
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QObject
from PySide6.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QIcon
from PIL import Image
from chat_client import ChatClient
from audio_processor import AudioProcessor
from tts_processor import TTSProcessor


# Signals class for thread safety
class WorkerSignals(QObject):
    add_message = Signal(str, str, object)  # text, sender, audio_data (tuple of samples, rate)
    update_indicator = Signal(str, bool)  # text, visible
    audio_started = Signal(object)  # bubble object
    audio_reset = Signal(object)  # bubble object
    set_inputs = Signal(bool)


# WhatsApp Colors
BG_COLOR = "#0b141a"
HEADER_COLOR = "#202c33"
USER_BUBBLE = "#005c4b"
AI_BUBBLE = "#202c33"
TEXT_COLOR = "#e9edef"
SECONDARY_TEXT = "#8696a0"
ACCENT_COLOR = "#00a884"


class MessageBubble(QFrame):
    def __init__(self, text, sender="user", tts_processor=None, signals=None, audio_data=None):
        super().__init__()
        self.tts_processor = tts_processor
        self.signals = signals
        self.audio_data = audio_data  # tuple of (samples, sample_rate)
        self.text = text
        self.sender = sender
        self.is_playing = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.bubble = QFrame()
        self.bubble.setObjectName("bubble")
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(10, 10, 10, 10)

        # Content layout for play button
        content_layout = QHBoxLayout()

        if sender == "ai":
            self.play_btn = QPushButton("▶")
            self.play_btn.setFixedSize(30, 30)
            self.play_btn.setCursor(Qt.PointingHandCursor)
            self.play_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT_COLOR};
                    color: white;
                    border-radius: 15px;
                    font-size: 14px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: #008f70; }}
            """)
            self.play_btn.clicked.connect(self.toggle_audio)
            content_layout.addWidget(self.play_btn)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 14px; border: none; background: transparent;"
        )
        self.label.setMaximumWidth(280)
        content_layout.addWidget(self.label)

        bubble_layout.addLayout(content_layout)

        # Timestamp
        self.time_label = QLabel(time.strftime("%H:%M"))
        self.time_label.setStyleSheet(
            f"color: {SECONDARY_TEXT}; font-size: 10px; border: none; background: transparent;"
        )
        self.time_label.setAlignment(Qt.AlignRight)
        bubble_layout.addWidget(self.time_label)

        if sender == "user":
            layout.addStretch()
            layout.addWidget(self.bubble)
            self.bubble.setStyleSheet(
                f"background-color: {USER_BUBBLE}; border-radius: 15px;"
            )
        else:
            layout.addWidget(self.bubble)
            layout.addStretch()
            self.bubble.setStyleSheet(
                f"background-color: {AI_BUBBLE}; border-radius: 15px;"
            )

    def toggle_audio(self):
        if self.is_playing:
            self.stop_audio()
        else:
            self.play_audio()

    def play_audio(self):
        if self.tts_processor:
            self.is_playing = True
            self.play_btn.setText("⏸")
            # Signal the parent to stop any other playing audio
            if self.signals:
                self.signals.audio_started.emit(self)
            
            def on_finish_callback():
                if self.signals:
                    self.signals.audio_reset.emit(self)
            
            if self.audio_data:
                # Use pre-generated audio
                samples, sample_rate = self.audio_data
                self.tts_processor.play_samples(samples, sample_rate, on_finish=on_finish_callback)
            else:
                # Generate on the fly
                threading.Thread(target=self.tts_processor.speak, args=(self.text,), kwargs={"on_finish": on_finish_callback}).start()

    def stop_audio(self):
        if self.tts_processor:
            self.tts_processor.stop()
            # The on_finish_callback from the thread will eventually trigger audio_reset
            # but we can also do it immediately for better responsiveness
            self.reset_ui()

    def reset_ui(self):
        self.is_playing = False
        self.play_btn.setText("▶")


class WhatsAppClone(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI")
        self.resize(420, 750)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.chat_client = ChatClient()
        self.audio_processor = AudioProcessor()
        self.tts_processor = TTSProcessor()
        self.is_recording = False

        # Signals
        self.signals = WorkerSignals()
        self.signals.add_message.connect(self.add_message_signal_handler)
        self.signals.update_indicator.connect(self.set_indicator)
        self.signals.audio_started.connect(self.handle_audio_start)
        self.signals.audio_reset.connect(self.handle_audio_reset)
        self.signals.set_inputs.connect(self.set_inputs_enabled)

        self.init_ui()
        
        # Auto-scroll handling
        self.scroll.verticalScrollBar().rangeChanged.connect(self.scroll_to_bottom)

        # Start initial greeting
        threading.Thread(target=self.initial_greeting).start()

    def add_message_signal_handler(self, text, sender="user", audio_data=None):
        bubble = self.add_message(text, sender, audio_data)
        if sender == "ai":
            # Automatically play audio for AI messages
            bubble.play_audio()
            # Re-enable inputs after AI is done
            self.set_inputs_enabled(True)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {HEADER_COLOR};")
        header_layout = QHBoxLayout(header)

        # Profile Pic Placeholder
        self.pic_label = QLabel()
        self.pic_label.setFixedSize(50, 50)
        self._set_profile_pic()
        header_layout.addWidget(self.pic_label)

        info_layout = QVBoxLayout()
        name_label = QLabel("AI")
        name_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 16px; font-weight: bold;"
        )
        status_label = QLabel("online")
        status_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 12px;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(status_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # Chat Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.scroll)

        # Indicators
        self.indicator_label = QLabel("")
        self.indicator_label.setAlignment(Qt.AlignCenter)
        self.indicator_label.setStyleSheet(
            "color: white; font-style: italic; background: transparent; padding: 5px;"
        )
        self.indicator_label.hide()
        main_layout.addWidget(self.indicator_label)

        # Input Bar
        input_bar = QFrame()
        input_bar.setFixedHeight(70)
        input_bar.setStyleSheet(f"background-color: {HEADER_COLOR};")
        input_layout = QHBoxLayout(input_bar)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("Type a message")
        self.entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_COLOR};
                color: {TEXT_COLOR};
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
                border: none;
            }}
        """)
        self.entry.returnPressed.connect(self.send_text_message)
        input_layout.addWidget(self.entry)

        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(45, 45)
        self.voice_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 22px;
                font-size: 20px;
            }}
            QPushButton:hover {{ background-color: #008f70; }}
        """)
        self.voice_btn.clicked.connect(self.toggle_recording)
        input_layout.addWidget(self.voice_btn)

        main_layout.addWidget(input_bar)

    def set_inputs_enabled(self, enabled):
        self.voice_btn.setEnabled(enabled)
        self.entry.setEnabled(enabled)
        # Visual feedback via stylesheet
        if not enabled:
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet() + "background-color: #555;")
        else:
            self.voice_btn.setStyleSheet(self.voice_btn.styleSheet().replace("background-color: #555;", ""))

    def _set_profile_pic(self):
        try:
            pixmap = QPixmap("profile.png")
            pixmap = pixmap.scaled(
                50, 50, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )

            # Mask to circle
            out_img = QPixmap(pixmap.size())
            out_img.fill(Qt.transparent)
            painter = QPainter(out_img)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QBrush(pixmap)
            painter.setBrush(path)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 50, 50)
            painter.end()
            self.pic_label.setPixmap(out_img)
        except:
            pass

    def add_message(self, text, sender="user", audio_data=None):
        bubble = MessageBubble(text, sender, self.tts_processor, self.signals, audio_data)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        return bubble

    def scroll_to_bottom(self):
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def handle_audio_start(self, active_bubble):
        # Stop all other bubbles that might be playing
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, MessageBubble) and widget != active_bubble:
                    if widget.sender == "ai" and widget.is_playing:
                        widget.reset_ui()

    def handle_audio_reset(self, bubble):
        if isinstance(bubble, MessageBubble):
            bubble.reset_ui()

    def set_indicator(self, text, visible):
        self.indicator_label.setText(text)
        if visible:
            self.indicator_label.show()
        else:
            self.indicator_label.hide()

    def initial_greeting(self):
        self.signals.set_inputs.emit(False)
        self.signals.update_indicator.emit("Connecting to AI Tutor...", True)
        greeting = self.chat_client.get_initial_greeting()
        self.signals.update_indicator.emit("AI is recording...", True)
        samples, rate = self.tts_processor.generate(greeting)
        self.signals.update_indicator.emit("", False)
        self.signals.add_message.emit(greeting, "ai", (samples, rate))

    def send_text_message(self):
        text = self.entry.text()
        if not text:
            return
        self.entry.clear()
        self.add_message(text, "user")
        threading.Thread(target=self.process_ai_response, args=(text,)).start()

    def process_ai_response(self, text):
        self.signals.set_inputs.emit(False)
        self.signals.update_indicator.emit("AI is thinking...", True)
        response = self.chat_client.get_response(text)
        self.signals.update_indicator.emit("AI is recording...", True)
        samples, rate = self.tts_processor.generate(response)
        self.signals.update_indicator.emit("", False)
        self.signals.add_message.emit(response, "ai", (samples, rate))

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.voice_btn.setText("⏹")
            self.voice_btn.setStyleSheet(
                self.voice_btn.styleSheet().replace(ACCENT_COLOR, "#ea0038")
            )
            self.signals.update_indicator.emit("Recording...", True)
            self.audio_processor.start_recording()
        else:
            self.is_recording = False
            self.voice_btn.setText("🎤")
            self.voice_btn.setStyleSheet(
                self.voice_btn.styleSheet().replace("#ea0038", ACCENT_COLOR)
            )
            self.signals.update_indicator.emit("Transcribing...", True)
            audio_np = self.audio_processor.stop_recording()
            threading.Thread(target=self.process_voice_input, args=(audio_np,)).start()

    def process_voice_input(self, audio_np):
        print("Transcription starting...")
        text = self.audio_processor.transcribe(audio_np)
        print(f"Transcribed text: {text}")
        self.signals.update_indicator.emit("", False)
        if text:
            self.signals.add_message.emit(text, "user", None)
            self.process_ai_response(text)
        else:
            self.signals.set_inputs.emit(True)
            print("No text transcribed.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppClone()
    window.show()
    sys.exit(app.exec())
