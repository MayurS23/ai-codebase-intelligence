@echo off
echo ============================================
echo  AI Codebase Intelligence — Windows Setup
echo ============================================

:: Step 1 — Create virtual environment
echo.
echo [1/4] Creating virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

:: Step 2 — Upgrade pip
echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip

:: Step 3 — Install dependencies
echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt

:: Step 4 — Create .env if missing
echo.
echo [4/4] Setting up .env file...
if not exist .env (
    copy .env.example .env
    echo .env created from .env.example
    echo.
    echo  *** IMPORTANT: Open .env and fill in your API keys ***
    echo.
) else (
    echo .env already exists — skipping
)

:: Create data directories
if not exist data\repos mkdir data\repos
if not exist data\chromadb mkdir data\chromadb

echo.
echo ============================================
echo  Setup complete!
echo.
echo  Next steps:
echo  1. Edit .env and add your API keys
echo  2. Run: start_backend.bat   (Terminal 1)
echo  3. Run: start_frontend.bat  (Terminal 2)
echo  4. Open: http://localhost:8501
echo ============================================
pause
