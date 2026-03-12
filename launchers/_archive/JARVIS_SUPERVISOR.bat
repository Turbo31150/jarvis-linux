@echo off
title JARVIS Supervisor
cd /D /home/turbo/jarvis-linux
echo ===== JARVIS Supervisor — Watch Mode =====
echo Monitoring all services every 30s...
echo.
python scripts\jarvis_supervisor.py --watch
pause
