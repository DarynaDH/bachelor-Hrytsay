@echo off
echo Starting Backend (FastAPI)...

cd /d D:\game-analytics-system\TGbot1_backend

venv\Scripts\python.exe -m uvicorn main:app --reload

pause
