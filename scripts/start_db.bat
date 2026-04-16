@echo off
echo Starting PostgreSQL database...

cd /d D:\game-analytics-system\db

docker compose up -d

pause
