#!/bin/bash

echo "--- Local English Tutor Setup ---"

# Find Python >= 3.12 already installed on the system
find_python() {
    for cmd in python3 python3.14 python3.13 python3.12; do
        if command -v "$cmd" &> /dev/null; then
            local ver
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            local major minor
            major=$(echo "$ver" | cut -d. -f1)
            minor=$(echo "$ver" | cut -d. -f2)
            if [[ "$major" -gt 3 ]] || [[ "$major" -eq 3 && "$minor" -ge 12 ]]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# Detect OS and install PortAudio (and Python 3.12 only if no compatible version found)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS. Checking for Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew is not installed. Please install it from https://brew.sh/"
        exit 1
    fi
    echo "Installing PortAudio via Homebrew..."
    brew install portaudio
    if ! find_python &> /dev/null; then
        echo "No compatible Python (>= 3.12) found. Installing python@3.12 via Homebrew..."
        brew install python@3.12
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux. Installing PortAudio..."
    sudo apt-get update && sudo apt-get install -y libportaudio2 pulseaudio alsa-utils libasound2-plugins
    if ! find_python &> /dev/null; then
        echo "No compatible Python (>= 3.12) found. Installing python3.12..."
        sudo apt-get install -y python3.12 python3.12-venv
    fi
else
    echo "Warning: Unsupported OS ($OSTYPE). Please ensure PortAudio and Python >= 3.12 are installed manually."
fi

# Locate the Python command to use
PYTHON_CMD=$(find_python)
if [[ -z "$PYTHON_CMD" ]]; then
    # Last resort: check Homebrew paths on macOS
    for path in /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12; do
        if [[ -f "$path" ]]; then
            PYTHON_CMD="$path"
            break
        fi
    done
fi

if [[ -z "$PYTHON_CMD" ]]; then
    echo "Error: Python >= 3.12 not found. Please install it and re-run this script."
    exit 1
fi

PYTHON_VER=$("$PYTHON_CMD" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $PYTHON_VER ($PYTHON_CMD)"

# Create/Recreate venv
echo "Configuring Python $PYTHON_VER virtual environment..."
"$PYTHON_CMD" -m venv .venv --clear
source .venv/bin/activate

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Ensuring Ollama model is available..."
ollama pull sam860/lfm2.5:1.2b

echo "--- Setup Complete! ---"
echo "You can now start the tutor using: ./start.sh"