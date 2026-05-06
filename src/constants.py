# UI Colors
BG_COLOR = "#0b141a"
HEADER_COLOR = "#202c33"
USER_BUBBLE = "#005c4b"
AI_BUBBLE = "#202c33"
TEXT_COLOR = "#e9edef"
SECONDARY_TEXT = "#8696a0"
ACCENT_COLOR = "#00a884"

import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Get the directory of the src folder
        base_path = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to project root
        base_path = os.path.dirname(base_path)

    return os.path.join(base_path, relative_path)
