@echo off
echo Starting Telegram bot...

cd /d "%~dp0bot"
venv\Scripts\python.exe main.py

pause