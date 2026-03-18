@echo off
echo Starting Streamlit Frontend...
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
streamlit run frontend/app.py --server.port 8501
pause
