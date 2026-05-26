@echo off
echo Starting Backend (FastAPI)...

cd /d "%~dp0backend"
venv\Scripts\python.exe -m uvicorn app.main:app --reload

pause