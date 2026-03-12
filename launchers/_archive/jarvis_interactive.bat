@echo off
title JARVIS v10.6 - Mode Interactif
color 0B
echo.
echo  ==========================================
echo    JARVIS v10.6 - MODE INTERACTIF (clavier)
echo    69 outils MCP ^| 125 commandes ^| Brain IA
echo  ==========================================
echo.
cd /d /home/turbo/jarvis-linux
"/home/turbo/jarvis-linux\.venv\Scripts\python.exe" -c "import asyncio; from src.orchestrator import run_interactive; asyncio.run(run_interactive(cwd='/home/turbo/jarvis-linux'))"
echo.
echo [JARVIS] Session terminee.
pause
