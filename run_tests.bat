@echo off
echo Running all tests...
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
set EMBEDDING_PROVIDER=local
python -m pytest tests/ -v --tb=short
pause
