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

def get_data_path(relative_path=""):
    """Get a persistent directory for user data (models, databases, etc.)"""
    app_name = "LocalEnglishTutor"
    
    if sys.platform == "win32":
        base_path = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), app_name)
    elif sys.platform == "darwin":
        # Using a more robust path resolution for macOS
        home = os.path.expanduser("~")
        if home == "~": # Fallback if expanduser fails
            home = os.environ.get("HOME", "/Users/" + os.environ.get("USER", "default"))
        base_path = os.path.join(home, "Library", "Application Support", app_name)
    else:
        base_path = os.path.join(os.path.expanduser("~"), ".local", "share", app_name)
        
    try:
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
            print(f"Created data directory at: {base_path}")
    except Exception as e:
        print(f"CRITICAL: Failed to create data directory {base_path}: {e}")
        # Fallback to current directory if everything else fails
        base_path = os.path.join(os.getcwd(), "data")
        os.makedirs(base_path, exist_ok=True)
        
    return os.path.join(base_path, relative_path)

# Diagnostics
print(f"--- Application Startup Diagnostics ---")
print(f"Platform: {sys.platform}")
data_root = get_data_path("")
print(f"Data Root: {data_root}")

# Verify write access
try:
    test_file = os.path.join(data_root, ".write_test")
    with open(test_file, "w") as f:
        f.write("test")
    os.remove(test_file)
    print(f"Write Access: Verified")
except Exception as e:
    print(f"Write Access: FAILED - {e}")

print(f"---------------------------------------")
