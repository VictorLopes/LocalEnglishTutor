import time
import threading
import os
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QMenu,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QObject, QSize
from PySide6.QtGui import QPixmap, QPainter, QBrush, QIcon
from chat_client import ChatClient
from audio_processor import AudioProcessor
from tts_processor import TTSProcessor
from constants import (
    BG_COLOR,
    HEADER_COLOR,
    USER_BUBBLE,
    AI_BUBBLE,
    TEXT_COLOR,
    SECONDARY_TEXT,
    ACCENT_COLOR,
    get_resource_path,
    get_data_path,
)


class WorkerSignals(QObject):
    add_message = Signal(
        str, str, object
    )  # text, sender, audio_data (tuple of samples, rate)
    update_indicator = Signal(str, bool)  # text, visible
    audio_started = Signal(object)  # bubble object
    audio_reset = Signal(object)  # bubble object
    set_inputs = Signal(bool)


class MessageBubble(QFrame):
    def __init__(
        self, text, sender="user", tts_processor=None, signals=None, audio_data=None
    ):
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
            self.play_btn = QPushButton()

            # Get icon path
            icon_path = get_resource_path(os.path.join("assets", "icons", "start.png"))
            self.play_btn.setIcon(QIcon(icon_path))
            self.play_btn.setIconSize(QSize(18, 18))

            self.play_btn.setFixedSize(30, 30)
            self.play_btn.setCursor(Qt.PointingHandCursor)
            self.play_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ACCENT_COLOR};
                    color: white;
                    border-radius: 15px;
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

            icon_path = get_resource_path(os.path.join("assets", "icons", "pause.png"))
            self.play_btn.setIcon(QIcon(icon_path))
            if self.signals:
                self.signals.audio_started.emit(self)

            def on_finish_callback():
                if self.signals:
                    self.signals.update_indicator.emit("", False)
                    self.signals.audio_reset.emit(self)

            if not self.audio_data and self.tts_processor.kokoro is None:
                if self.signals:
                    self.signals.update_indicator.emit(
                        "Downloading speech model...", True
                    )

            if self.audio_data:
                samples, sample_rate = self.audio_data
                self.tts_processor.play_samples(
                    samples, sample_rate, on_finish=on_finish_callback
                )
            else:

                def speak_thread():
                    def progress_cb(msg):
                        if self.signals:
                            self.signals.update_indicator.emit(msg, True)

                    self.tts_processor.speak(
                        self.text,
                        on_finish=on_finish_callback,
                        progress_callback=progress_cb,
                    )
                    # Clear indicator once generation is done and playback starts
                    if self.signals:
                        self.signals.update_indicator.emit("", False)

                threading.Thread(target=speak_thread).start()

    def stop_audio(self):
        if self.tts_processor:
            self.tts_processor.stop()
            self.reset_ui()

    def reset_ui(self):
        self.is_playing = False
        icon_path = get_resource_path(os.path.join("assets", "icons", "start.png"))
        self.play_btn.setIcon(QIcon(icon_path))


class ChatScreen(QWidget):
    def __init__(self, db, level, subject, conversation_id=None):
        super().__init__()
        self.db = db
        self.level = level
        self.subject = subject
        self.conversation_id = conversation_id
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.chat_client = ChatClient()
        self.chat_client.set_system_prompt(level, subject)

        self.models_dir = get_data_path("models")
        os.makedirs(self.models_dir, exist_ok=True)

        self.audio_processor = AudioProcessor(download_root=self.models_dir)
        self.tts_processor = TTSProcessor(models_dir=self.models_dir)
        self.is_recording = False

        self.signals = WorkerSignals()
        self.signals.add_message.connect(self.add_message_signal_handler)
        self.signals.update_indicator.connect(self.set_indicator)
        self.signals.audio_started.connect(self.handle_audio_start)
        self.signals.audio_reset.connect(self.handle_audio_reset)
        self.signals.set_inputs.connect(self.set_inputs_enabled)

        self.init_ui()
        self.scroll.verticalScrollBar().rangeChanged.connect(self.scroll_to_bottom)

        if self.conversation_id:
            self.load_existing_conversation()
        else:
            threading.Thread(target=self.initial_greeting).start()

    def add_message_signal_handler(self, text, sender="user", audio_data=None):
        bubble = self.add_message(text, sender, audio_data)
        if sender == "ai":
            if audio_data:
                bubble.play_audio()
            self.set_inputs_enabled(True)

    def load_existing_conversation(self):
        messages = self.db.get_messages(self.conversation_id)
        self.chat_client.load_history(messages)
        for text, sender in messages:
            self.add_message(text, sender, save_to_db=False)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {HEADER_COLOR};")
        header_layout = QHBoxLayout(header)

        self.pic_label = QLabel()
        self.pic_label.setFixedSize(50, 50)
        self._set_profile_pic()
        header_layout.addWidget(self.pic_label)

        info_layout = QVBoxLayout()
        name_label = QLabel(f"AI - {self.level}")
        name_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 16px; font-weight: bold;"
        )
        status_label = QLabel(self.subject)
        status_label.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 12px;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(status_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        back_btn = QPushButton()

        icon_path = get_resource_path(os.path.join("assets", "icons", "back.png"))
        back_btn.setIcon(QIcon(icon_path))
        back_btn.setIconSize(QSize(24, 24))

        back_btn.setFixedSize(40, 40)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
            }}
            QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.1); border-radius: 20px; }}
        """)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)

        # Menu button (Ellipsis)
        self.menu_btn = QPushButton()
        icon_path = get_resource_path(os.path.join("assets", "icons", "ellipsis.png"))
        self.menu_btn.setIcon(QIcon(icon_path))
        self.menu_btn.setIconSize(QSize(24, 24))
        self.menu_btn.setFixedSize(40, 40)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
            }}
            QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.1); border-radius: 20px; }}
        """)
        self.menu_btn.clicked.connect(self.show_menu)
        header_layout.addWidget(self.menu_btn)

        main_layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_widget)
        main_layout.addWidget(self.scroll)

        self.indicator_label = QLabel("")
        self.indicator_label.setAlignment(Qt.AlignCenter)
        self.indicator_label.setStyleSheet(
            "color: white; font-style: italic; background: transparent; padding: 5px;"
        )
        self.indicator_label.hide()
        main_layout.addWidget(self.indicator_label)

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

        self.voice_btn = QPushButton()

        icon_path = get_resource_path(os.path.join("assets", "icons", "microphone.png"))
        self.voice_btn.setIcon(QIcon(icon_path))
        self.voice_btn.setIconSize(QSize(24, 24))

        self.voice_btn.setFixedSize(45, 45)
        self.voice_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                border-radius: 22px;
            }}
            QPushButton:hover {{ background-color: #008f70; }}
        """)
        self.voice_btn.clicked.connect(self.toggle_recording)
        input_layout.addWidget(self.voice_btn)

        main_layout.addWidget(input_bar)

    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {HEADER_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {SECONDARY_TEXT}33;
            }}
            QMenu::item {{
                padding: 8px 25px;
            }}
            QMenu::item:selected {{
                background-color: {ACCENT_COLOR};
            }}
        """)

        # Get current state
        conv_data = self.db.get_conversation(self.conversation_id)
        is_archived = conv_data[5] if conv_data else 0

        archive_text = (
            "Unarchive conversation" if is_archived else "Archive conversation"
        )

        archive_action = menu.addAction(archive_text)
        note_action = menu.addAction("Make a note")
        menu.addSeparator()
        delete_action = menu.addAction("Delete conversation")

        action = menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

        if action == archive_action:
            self.db.archive_conversation(self.conversation_id, not is_archived)
            self.go_back()
        elif action == note_action:
            self.make_note()
        elif action == delete_action:
            self.confirm_delete()

    def make_note(self):
        conv_data = self.db.get_conversation(self.conversation_id)
        current_note = conv_data[6] if conv_data else ""

        note, ok = QInputDialog.getMultiLineText(
            self,
            "Conversation Note",
            "Enter your note for this conversation:",
            current_note,
        )
        if ok:
            self.db.update_note(self.conversation_id, note)

    def confirm_delete(self):
        reply = QMessageBox.question(
            self,
            "Delete Conversation",
            "Are you sure you want to delete this conversation? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.db.delete_conversation(self.conversation_id)
            self.go_back()

    def go_back(self):
        if self.tts_processor:
            self.tts_processor.stop()
        if self.is_recording:
            self.audio_processor.stop_recording()
            self.is_recording = False

        main_window = self.window()
        if hasattr(main_window, "go_back_to_history"):
            main_window.go_back_to_history()

    def set_inputs_enabled(self, enabled):
        self.voice_btn.setEnabled(enabled)
        self.entry.setEnabled(enabled)
        if not enabled:
            self.voice_btn.setStyleSheet(
                self.voice_btn.styleSheet() + "background-color: #555;"
            )
        else:
            self.voice_btn.setStyleSheet(
                self.voice_btn.styleSheet().replace("background-color: #555;", "")
            )

    def _set_profile_pic(self):
        try:
            pic_path = get_resource_path("profile.jpg")
            pixmap = QPixmap(pic_path)
            pixmap = pixmap.scaled(
                50, 50, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
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

    def add_message(self, text, sender="user", audio_data=None, save_to_db=True):
        if save_to_db and self.conversation_id:
            self.db.add_message(self.conversation_id, text, sender)

        bubble = MessageBubble(
            text, sender, self.tts_processor, self.signals, audio_data
        )
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        return bubble

    def scroll_to_bottom(self):
        self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        )

    def handle_audio_start(self, active_bubble):
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

        # Pre-load Whisper model in the background
        self.signals.update_indicator.emit(
            "Checking transcription model (this may take a while if downloading)...",
            True,
        )
        self.audio_processor.load_model(download_root=self.models_dir)
        # Pre-load TTS model in the background
        def update_tts_progress(msg):
            self.signals.update_indicator.emit(msg, True)

        self.tts_processor.load_model(progress_callback=update_tts_progress)
        self.signals.update_indicator.emit("Connecting to AI Tutor...", True)

        # Create conversation in DB if not exists
        if not self.conversation_id:
            self.conversation_id = self.db.create_conversation(self.level, self.subject)

        greeting = self.chat_client.get_initial_greeting()
        if self.tts_processor.kokoro is None:
            def update_tts_progress(msg):
                self.signals.update_indicator.emit(msg, True)
            self.tts_processor.load_model(progress_callback=update_tts_progress)
        else:
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
        
        if self.tts_processor.kokoro is None:
            def update_tts_progress(msg):
                self.signals.update_indicator.emit(msg, True)
            self.tts_processor.load_model(progress_callback=update_tts_progress)
        else:
            self.signals.update_indicator.emit("AI is recording...", True)
            
        samples, rate = self.tts_processor.generate(response)
        self.signals.update_indicator.emit("", False)
        self.signals.add_message.emit(response, "ai", (samples, rate))

    def toggle_recording(self):
        if not self.is_recording:
            try:
                self.audio_processor.start_recording()
                self.is_recording = True

                icon_path = get_resource_path(os.path.join("assets", "icons", "stop.png"))
                self.voice_btn.setIcon(QIcon(icon_path))

                self.voice_btn.setStyleSheet(
                    self.voice_btn.styleSheet().replace(ACCENT_COLOR, "#ea0038")
                )
                if self.audio_processor.model is None:
                    self.signals.update_indicator.emit(
                        "Downloading transcription model...", True
                    )
                else:
                    self.signals.update_indicator.emit("Recording...", True)
            except Exception as e:
                print(f"Recording error: {e}")
                self.signals.update_indicator.emit(f"⚠️ {str(e)}", True)
                threading.Timer(
                    3.0, lambda: self.signals.update_indicator.emit("", False)
                ).start()
        else:
            self.is_recording = False

            icon_path = get_resource_path(os.path.join("assets", "icons", "microphone.png"))
            self.voice_btn.setIcon(QIcon(icon_path))

            self.voice_btn.setStyleSheet(
                self.voice_btn.styleSheet().replace("#ea0038", ACCENT_COLOR)
            )
            if self.audio_processor.model is None:
                self.signals.update_indicator.emit(
                    "Downloading transcription model...", True
                )
            else:
                self.signals.update_indicator.emit("Transcribing...", True)
            audio_np = self.audio_processor.stop_recording()
            threading.Thread(target=self.process_voice_input, args=(audio_np,)).start()

    def process_voice_input(self, audio_np):
        try:
            if self.audio_processor.model is None:
                self.signals.update_indicator.emit(
                    "Downloading transcription model...", True
                )

            # Check for silent audio before transcribing
            max_val = 0
            if audio_np is not None and len(audio_np) > 0:
                max_val = np.max(np.abs(audio_np))

            if max_val < 0.001:
                self.signals.update_indicator.emit(
                    "⚠️ No sound detected. Check microphone permissions.", True
                )
                self.signals.set_inputs.emit(True)
                threading.Timer(5.0, lambda: self.signals.update_indicator.emit("", False)).start()
                return

            text = self.audio_processor.transcribe(audio_np)
            self.signals.update_indicator.emit("", False)
            if text:
                self.signals.add_message.emit(text, "user", None)
                self.process_ai_response(text)
            else:
                self.signals.update_indicator.emit("⚠️ Could not understand. Try again.", True)
                self.signals.set_inputs.emit(True)
                threading.Timer(3.0, lambda: self.signals.update_indicator.emit("", False)).start()
        except Exception as e:
            print(f"Transcription error: {e}")
            self.signals.update_indicator.emit(f"⚠️ Error: {str(e)}", True)
            self.signals.set_inputs.emit(True)
            threading.Timer(5.0, lambda: self.signals.update_indicator.emit("", False)).start()


