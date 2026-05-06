@echo off
setlocal enabledelayedexpansion

echo --- Local English Tutor Setup (Windows) ---

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Create Windows virtual environment
echo Creating Windows virtual environment (.venv_win)...
python -m venv .venv_win --clear
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment.
    pause
    exit /b 1
)

:: 3. Activate and install dependencies
echo Activating virtual environment...
call .venv_win\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Warning: Some dependencies failed to install. Please check the logs above.
)

:: 4. Ollama check
echo Checking for Ollama...
ollama --version >nul 2>&1
if %errorlevel% eq 0 (
    echo Ensuring Ollama model is available...
    ollama pull sam860/lfm2.5:1.2b
) else (
    echo Warning: Ollama not found. Please install it from https://ollama.com/ to use the local LLM.
)

echo.
echo --- Setup Complete! ---
echo You can now start the tutor using: start.bat
echo.
pause
