@echo off
echo Starting Backend (FastAPI)...

cd /d D:\game-analytics-system\backend

venv\Scripts\python.exe -m uvicorn app.main:app --reload

pause
