from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QBrush
import os
from datetime import datetime
from constants import BG_COLOR, HEADER_COLOR, TEXT_COLOR, ACCENT_COLOR, SECONDARY_TEXT


class ConversationItem(QFrame):
    def __init__(self, conv_id, level, subject, last_msg, updated_at, note, on_click):
        super().__init__()
        self.conv_id = conv_id
        self.note = note
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border-bottom: 1px solid {SECONDARY_TEXT}33;
            }}
            QFrame:hover {{
                background-color: {HEADER_COLOR};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Profile Picture (Placeholder)
        self.pic_label = QLabel()
        self.pic_label.setFixedSize(50, 50)
        self._set_placeholder_pic()
        layout.addWidget(self.pic_label)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_layout = QHBoxLayout()
        name_label = QLabel(f"{level} - {subject}")
        # Set font explicitly for accurate elision measurement
        font = name_label.font()
        font.setPointSize(16)
        font.setBold(True)
        name_label.setFont(font)
        
        name_label.setStyleSheet(
            f"color: {TEXT_COLOR}; border: none;"
        )
        name_label.setFixedWidth(250)
        metrics = name_label.fontMetrics()
        elided = metrics.elidedText(
            name_label.text(), Qt.ElideRight, name_label.width()
        )
        name_label.setText(elided)

        title_layout.addWidget(name_label)

        title_layout.addStretch()

        # Time
        try:
            dt = datetime.fromisoformat(updated_at)
            time_str = dt.strftime("%H:%M")
        except:
            time_str = ""

        time_label = QLabel(time_str)
        time_label.setStyleSheet(
            f"color: {SECONDARY_TEXT}; font-size: 12px; border: none;"
        )
        title_layout.addWidget(time_label)

        info_layout.addLayout(title_layout)

        last_msg_label = QLabel(last_msg if last_msg else "No messages yet")
        last_msg_label.setStyleSheet(
            f"color: {SECONDARY_TEXT}; font-size: 14px; border: none;"
        )
        last_msg_label.setFixedWidth(250)
        # Elide text if too long
        metrics = last_msg_label.fontMetrics()
        elided = metrics.elidedText(
            last_msg_label.text(), Qt.ElideRight, last_msg_label.width()
        )
        last_msg_label.setText(elided)

        info_layout.addWidget(last_msg_label)

        if self.note:
            note_label = QLabel(f"📝 {self.note}")
            note_label.setStyleSheet(
                f"color: {ACCENT_COLOR}; font-size: 11px; font-style: italic; border: none; padding-top: 9px"
            )
            note_label.setFixedWidth(250)
            metrics = note_label.fontMetrics()
            elided = metrics.elidedText(
                note_label.text(), Qt.ElideRight, note_label.width()
            )
            note_label.setText(elided)
            info_layout.addWidget(note_label)

        layout.addLayout(info_layout)

        self.on_click = on_click

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click(self.conv_id)

    def _set_placeholder_pic(self):
        try:
            screens_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(os.path.dirname(screens_dir))
            pic_path = os.path.join(root_dir, "profile.jpg")
            if not os.path.exists(pic_path):
                pixmap = QPixmap(50, 50)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(QBrush(Qt.gray))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(0, 0, 50, 50)
                painter.end()
                self.pic_label.setPixmap(pixmap)
                return

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


class HistoryScreen(QWidget):
    def __init__(self, db, on_new_conv, on_select_conv):
        super().__init__()
        self.db = db
        self.on_new_conv = on_new_conv
        self.on_select_conv = on_select_conv
        self.showing_archived = False
        self.setStyleSheet(f"background-color: {BG_COLOR};")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"background-color: {HEADER_COLOR};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title_label = QLabel("Conversations")
        title_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 20px; font-weight: bold;"
        )
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Archive Toggle
        self.archive_toggle_btn = QPushButton("Show Archived")
        self.archive_toggle_btn.setFixedSize(120, 30)
        self.archive_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.archive_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {SECONDARY_TEXT};
                border: 1px solid {SECONDARY_TEXT}66;
                border-radius: 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.05);
            }}
        """)
        self.archive_toggle_btn.clicked.connect(self.toggle_archived_view)
        header_layout.addWidget(self.archive_toggle_btn)

        # New Conversation Button
        new_btn = QPushButton()
        screens_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(screens_dir))
        icon_path = os.path.join(root_dir, "assets", "icons", "add.png")
        new_btn.setIcon(QIcon(icon_path))
        new_btn.setIconSize(QSize(24, 24))
        new_btn.setFixedSize(40, 40)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #008f70; }}
        """)
        new_btn.clicked.connect(self.on_new_conv)
        header_layout.addWidget(new_btn)

        layout.addWidget(header)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        self.refresh_list()

    def toggle_archived_view(self):
        self.showing_archived = not self.showing_archived
        if self.showing_archived:
            self.archive_toggle_btn.setText("Show Active")
            self.archive_toggle_btn.setStyleSheet(
                self.archive_toggle_btn.styleSheet().replace(
                    SECONDARY_TEXT, ACCENT_COLOR
                )
            )
        else:
            self.archive_toggle_btn.setText("Show Archived")
            self.archive_toggle_btn.setStyleSheet(
                self.archive_toggle_btn.styleSheet().replace(
                    ACCENT_COLOR, SECONDARY_TEXT
                )
            )
        self.refresh_list()

    def refresh_list(self):
        # Clear existing
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        conversations = self.db.get_conversations(archived=self.showing_archived)
        for conv in conversations:
            # (id, level, subject, last_message, updated_at, is_archived, note)
            item = ConversationItem(
                conv[0],
                conv[1],
                conv[2],
                conv[3],
                conv[4],
                conv[6],
                self.on_select_conv,
            )
            self.list_layout.insertWidget(self.list_layout.count() - 1, item)
