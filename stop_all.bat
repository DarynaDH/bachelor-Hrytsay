@echo off
echo Stopping all services...

taskkill /F /IM python.exe >nul 2>&1

cd /d D:\game-analytics-system\TGbot1_db
docker compose down

echo All services stopped.
pause

