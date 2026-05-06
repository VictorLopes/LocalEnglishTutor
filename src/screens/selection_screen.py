from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QScrollArea,
)
from PySide6.QtCore import Qt
from constants import BG_COLOR, HEADER_COLOR, TEXT_COLOR, ACCENT_COLOR, SECONDARY_TEXT

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
            back_btn = QPushButton("←")
            back_btn.setFixedSize(40, 40)
            back_btn.setCursor(Qt.PointingHandCursor)
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {TEXT_COLOR};
                    font-size: 24px;
                    border: none;
                }}
                QPushButton:hover {{ color: {ACCENT_COLOR}; }}
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

        # Scrollable area for options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.options_layout = QGridLayout(self.container) if is_grid else QVBoxLayout(self.container)
        self.options_layout.setSpacing(15)
        self.options_layout.setContentsMargins(10, 0, 10, 0)
        
        if not is_grid:
            self.options_layout.addStretch() # Push everything up

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

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
            btn = QPushButton(option)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {HEADER_COLOR};
                    color: {TEXT_COLOR};
                    border-radius: 10px;
                    font-size: 16px;
                    border: 1px solid {SECONDARY_TEXT};
                    padding: 0 20px;
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
