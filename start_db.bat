@echo off
echo Starting PostgreSQL database...

cd /d "%~dp0db"
docker compose up -d

pause