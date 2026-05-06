from PySide6.QtGui import QIcon
import sys
import multiprocessing
import json
import os
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
)
from screens.selection_screen import SelectionScreen
from screens.chat_screen import ChatScreen
from screens.history_screen import HistoryScreen
from database import Database
from constants import BG_COLOR, get_resource_path


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI English Tutor")
        self.setFixedSize(450, 700)

        icon_path = get_resource_path("profile.jpg")
        self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.db = Database()
        self.config = self._load_config()
        self.subjects = self.config.get("subjects", {})
        self.selected_level = None
        self.selected_subject = None

        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # Screens
        self.history_screen = HistoryScreen(
            self.db, self.start_new_conversation, self.open_existing_conversation
        )

        self.level_screen = SelectionScreen(
            "Select Your Level",
            ["A1", "A2", "B1", "B2", "C1", "C2", "Business", "Job Interview"],
            self.on_level_selected,
            on_back=self.go_back_to_history,
            is_grid=True,
        )
        self.subject_screen = SelectionScreen(
            "Select a Subject",
            [],
            self.on_subject_selected,
            on_back=self.go_back_to_levels,
            is_grid=False,
        )

        self.stack.addWidget(self.history_screen)
        self.stack.addWidget(self.level_screen)
        self.stack.addWidget(self.subject_screen)

    def _load_config(self):
        config_path = get_resource_path("config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def start_new_conversation(self):
        self.stack.setCurrentWidget(self.level_screen)

    def open_existing_conversation(self, conv_id):
        # Get conv details from DB
        conv = self.db.get_conversation(conv_id)
        if conv:
            # (id, level, subject, last_message, updated_at, is_archived, note)
            self.selected_level = conv[1]
            self.selected_subject = conv[2]
            self.chat_screen = ChatScreen(
                self.db,
                self.selected_level,
                self.selected_subject,
                conversation_id=conv_id,
            )
            self.stack.addWidget(self.chat_screen)
            self.stack.setCurrentWidget(self.chat_screen)

    def on_level_selected(self, level):
        self.selected_level = level
        subjects = self.subjects.get(level, [])
        self.subject_screen.update_options(subjects, self.on_subject_selected)
        self.stack.setCurrentWidget(self.subject_screen)

    def on_subject_selected(self, subject):
        self.selected_subject = subject
        self.chat_screen = ChatScreen(
            self.db, self.selected_level, self.selected_subject
        )
        self.stack.addWidget(self.chat_screen)
        self.stack.setCurrentWidget(self.chat_screen)

    def go_back_to_history(self):
        self.history_screen.refresh_list()
        self.stack.setCurrentWidget(self.history_screen)

    def go_back_to_levels(self):
        self.stack.setCurrentWidget(self.level_screen)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
