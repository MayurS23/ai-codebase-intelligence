@echo off
echo Starting FastAPI Backend...
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
