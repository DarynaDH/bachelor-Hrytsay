@echo off
echo Stopping all services...

echo Stopping backend and bot...
taskkill /F /IM python.exe >nul 2>&1

echo Stopping database...
cd /d "%~dp0db"
docker compose down

echo All services stopped.
pause