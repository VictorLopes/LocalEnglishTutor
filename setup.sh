#!/bin/bash

echo "--- Local English Tutor Setup ---"

# Detect OS and install PortAudio
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS. Checking for Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew is not installed. Please install it from https://brew.sh/"
        exit 1
    fi
    echo "Installing PortAudio and Python 3.12 via Homebrew..."
    brew install portaudio python@3.12
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux. Installing PortAudio and Python 3.12..."
    sudo apt-get update && sudo apt-get install -y libportaudio2 pulseaudio alsa-utils libasound2-plugins python3.12 python3.12-venv
else
    echo "Warning: Unsupported OS ($OSTYPE). Please ensure PortAudio and Python 3.12 are installed manually."
fi

# Create/Recreate venv with Python 3.12
echo "Configuring Python 3.12 virtual environment..."
# Try common paths for python3.12
PYTHON_CMD="python3.12"
if ! command -v $PYTHON_CMD &> /dev/null; then
    # On macOS, Homebrew might not symlink it to /usr/local/bin immediately
    if [[ -f "/opt/homebrew/bin/python3.12" ]]; then
        PYTHON_CMD="/opt/homebrew/bin/python3.12"
    elif [[ -f "/usr/local/bin/python3.12" ]]; then
        PYTHON_CMD="/usr/local/bin/python3.12"
    else
        echo "Error: Python 3.12 not found. Please ensure it is installed correctly."
        exit 1
    fi
fi

$PYTHON_CMD -m venv .venv --clear
source .venv/bin/activate

echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Ensuring Ollama model is available..."
ollama pull sam860/lfm2.5:1.2b

echo "--- Setup Complete! ---"
echo "You can now start the tutor using: ./start.sh"