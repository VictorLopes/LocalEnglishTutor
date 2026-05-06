import sys
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
from constants import BG_COLOR


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI English Tutor")
        self.resize(420, 750)
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.config = self._load_config()
        self.subjects = self.config.get("subjects", {})
        self.selected_level = None
        self.selected_subject = None

        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # Screens
        self.level_screen = SelectionScreen(
            "Select Your Level",
            ["A1", "A2", "B1", "B2", "C1", "C2", "Business", "Job Interview"],
            self.on_level_selected,
            is_grid=True
        )
        self.subject_screen = SelectionScreen(
            "Select a Subject",
            [],
            self.on_subject_selected,
            on_back=self.go_back_to_levels,
            is_grid=False
        )

        self.stack.addWidget(self.level_screen)
        self.stack.addWidget(self.subject_screen)

    def _load_config(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(root_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        return {}

    def on_level_selected(self, level):
        self.selected_level = level
        subjects = self.subjects.get(level, [])
        self.subject_screen.update_options(subjects, self.on_subject_selected)
        self.stack.setCurrentIndex(1)

    def on_subject_selected(self, subject):
        self.selected_subject = subject
        self.chat_screen = ChatScreen(self.selected_level, self.selected_subject)
        self.stack.addWidget(self.chat_screen)
        self.stack.setCurrentWidget(self.chat_screen)

    def go_back_to_levels(self):
        self.stack.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
