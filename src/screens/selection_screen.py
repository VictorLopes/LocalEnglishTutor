from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os
from constants import BG_COLOR, HEADER_COLOR, TEXT_COLOR, ACCENT_COLOR, SECONDARY_TEXT, get_resource_path

class SelectionScreen(QWidget):
    def __init__(self, title, options, on_select, on_back=None, is_grid=True):
        super().__init__()
        self.is_grid = is_grid
        self.setStyleSheet(f"background-color: {BG_COLOR};")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Header with Back Button and Title
        header_layout = QHBoxLayout()
        if on_back:
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
            back_btn.clicked.connect(on_back)
            header_layout.addWidget(back_btn)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(
            f"color: {TEXT_COLOR}; font-size: 22px; font-weight: bold;"
        )
        header_layout.addWidget(title_label)
        if on_back:
            header_layout.addSpacing(40) # Balance the back button
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.options_layout = QGridLayout(self.container) if is_grid else QVBoxLayout(self.container)
        self.options_layout.setSpacing(15)
        self.options_layout.setContentsMargins(10, 0, 10, 0)
        
        if not is_grid:
            self.options_layout.addStretch() # Push everything up

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        self.update_options(options, on_select)

    def update_options(self, options, on_select):
        # Clear existing buttons
        layout = self.options_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.is_grid:
            layout.addStretch()

        for i, option in enumerate(options):
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(60)
            
            # Use fixed width to prevent layout expansion
            btn_width = 175 if self.is_grid else 360
            btn.setFixedWidth(btn_width)
            
            # Set font explicitly for accurate measurement
            font = btn.font()
            font.setPointSize(16)
            btn.setFont(font)
            
            # Elide text based on available internal space (accounting for padding)
            max_text_width = btn_width - 20 
            metrics = btn.fontMetrics()
            elided_text = metrics.elidedText(option, Qt.ElideRight, max_text_width)
            btn.setText(elided_text)
            btn.setToolTip(option) if elided_text != option else None
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {HEADER_COLOR};
                    color: {TEXT_COLOR};
                    border-radius: 10px;
                    border: 1px solid {SECONDARY_TEXT};
                    padding: 0 10px;
                    text-align: {"center" if self.is_grid else "left"};
                }}
                QPushButton:hover {{
                    background-color: {ACCENT_COLOR};
                    border: 1px solid {ACCENT_COLOR};
                }}
            """)
            btn.clicked.connect(lambda checked, opt=option: on_select(opt))
            
            if self.is_grid:
                layout.addWidget(btn, i // 2, i % 2)
            else:
                layout.insertWidget(layout.count() - 1, btn)
