@echo off
title JARVIS Status
cd /d /home/turbo/jarvis-linux
/home/turbo\.local\bin\uv.exe run python main.py -s
pause
