@echo off
cd /d "%~dp0"
set "PY=C:\Users\jh869\envchat\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" -m streamlit run app.py --server.port 8517
pause
