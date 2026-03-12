@echo off
title JARVIS v10.6 - Systray
cd /d /home/turbo/jarvis-linux
"/home/turbo/jarvis-linux\.venv\Scripts\python.exe" -c "from src.systray import run_systray; run_systray()"
