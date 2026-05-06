#!/bin/bash

# LocalEnglishTutor Build Script
# This script generates a standalone binary for the project using PyInstaller.

# Exit on error
set -e

echo "--- LocalEnglishTutor Build System ---"

# 1. Detect OS
OS_NAME="$(uname -s)"
case "${OS_NAME}" in
    Linux*)     PLATFORM=Linux;;
    Darwin*)    PLATFORM=Mac;;
    MINGW*)     PLATFORM=Windows;;
    MSYS*)      PLATFORM=Windows;;
    *)          PLATFORM="UNKNOWN:${OS_NAME}"
esac

echo "Target Platform: ${PLATFORM}"

# 2. Check for virtual environment
if [ -d ".venv" ]; then
    echo "Using virtual environment .venv"
    source .venv/bin/activate
else
    echo "WARNING: .venv not found. Using system python."
fi

# 3. Install build dependencies
echo "Installing PyInstaller..."
pip install pyinstaller

# 4. Clean previous builds
echo "Cleaning old build files..."
rm -rf build dist

# 5. Build arguments
# --noconsole: Hide terminal on launch
# --add-data: Include project assets. Format: "source:destination" (Unix uses :)
# --collect-all: Gather all binaries/data for complex ML libraries
# --icon: (Optional) Path to icon file

APP_NAME="LocalEnglishTutor"
MAIN_SCRIPT="src/app.py"

echo "Starting build process..."

# Define separators for add-data (Unix uses :, Windows uses ;)
SEP=":"
if [[ "$PLATFORM" == "Windows" ]]; then
    SEP=";"
fi

# Define icon based on platform
ICON_FILE="icon.png"
if [ "$PLATFORM" == "Mac" ]; then
    ICON_FILE="icon.icns"
fi

# Build command
pyinstaller LocalEnglishTutor.spec --noconfirm


echo "--- Build Complete! ---"
if [ "$PLATFORM" == "Mac" ]; then
    echo "MacOS App Bundle: dist/${APP_NAME}.app"
    echo "MacOS Executable: dist/${APP_NAME}/${APP_NAME}"
else
    echo "Executable: dist/${APP_NAME}/${APP_NAME}"
fi

echo "Zipping the output..."
if command -v zip >/dev/null 2>&1; then
    (cd dist && zip -r "${APP_NAME}.zip" "${APP_NAME}")
    echo "Zip created: dist/${APP_NAME}.zip"
else
    echo "WARNING: 'zip' command not found. Skipping zipping step."
fi

echo ""
echo "NOTE: To run the binary, make sure you have Ollama running locally."
echo "The first time you run it, it will download Whisper and Kokoro models into a 'models' folder next to the executable."
