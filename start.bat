@echo off

if exist .venv_win\Scripts\activate.bat (
    echo Starting Local English Tutor using .venv_win...
    call .venv_win\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo Starting Local English Tutor using .venv...
    call .venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

python src/app.py
pause
