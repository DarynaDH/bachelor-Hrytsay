@echo off
echo Generating test data...

cd /d "%~dp0"
backend\venv\Scripts\python.exe seed.py

pause