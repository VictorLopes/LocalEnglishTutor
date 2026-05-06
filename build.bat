@echo off
setlocal enabledelayedexpansion

echo --- LocalEnglishTutor Windows Build System ---

:: 1. Check for virtual environment
if exist .venv\Scripts\activate.bat (
    echo Using virtual environment .venv
    call .venv\Scripts\activate.bat
) else (
    echo WARNING: .venv not found. Using system python.
)

:: 2. Install build dependencies
echo Installing PyInstaller...
pip install pyinstaller

:: 3. Clean previous builds
echo Cleaning old build files...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del /q *.spec

:: 4. Build arguments
set APP_NAME=LocalEnglishTutor
set MAIN_SCRIPT=src\app.py

echo Starting build process...

:: Run PyInstaller
:: On Windows, use ; as separator for --add-data
pyinstaller --noconsole --name "%APP_NAME%" ^
    --add-data "config.json;." ^
    --add-data "profile.jpg;." ^
    --add-data "images;images" ^
    --add-data "assets;assets" ^
    --collect-all onnxruntime ^
    --collect-all faster_whisper ^
    --collect-all kokoro_onnx ^
    --collect-all phonemizer_fork ^
    --collect-all language_tags ^
    --collect-all segments ^
    --collect-all csvw ^
    --hidden-import PySide6.QtSvg ^
    --icon "icon.ico" ^
    "%MAIN_SCRIPT%"

echo --- Build Complete! ---
echo Executable: dist\%APP_NAME%\%APP_NAME%.exe
echo.
echo NOTE: To run the binary, make sure you have Ollama running locally.
echo The first time you run it, it will download Whisper and Kokoro models into a 'models' folder next to the executable.

pause
