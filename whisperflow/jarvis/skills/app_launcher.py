"""
JARVIS Skill - Lanceur d'applications Windows
Ouvre et ferme n'importe quelle application par la voix
"""

import asyncio
import logging
import shlex
from ..commander import VoiceCommand, CommandResult
from ..config import config

logger = logging.getLogger("jarvis.skills.app_launcher")

# Whitelist d'applications autorisées (sécurité anti-injection)
SAFE_EXECUTABLES = {
    "explorateur": ["explorer.exe"],
    "navigateur": ["cmd", "/c", "start", "msedge"],
    "chrome": ["cmd", "/c", "start", "chrome"],
    "firefox": ["cmd", "/c", "start", "firefox"],
    "edge": ["cmd", "/c", "start", "msedge"],
    "bloc-notes": ["notepad.exe"],
    "notepad": ["notepad.exe"],
    "calculatrice": ["calc.exe"],
    "terminal": ["wt.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "paramètres": ["cmd", "/c", "start", "ms-settings:"],
    "paint": ["mspaint.exe"],
    "word": ["cmd", "/c", "start", "winword"],
    "excel": ["cmd", "/c", "start", "excel"],
    "powerpoint": ["cmd", "/c", "start", "powerpnt"],
    "teams": ["cmd", "/c", "start", "msteams:"],
    "discord": ["cmd", "/c", "start", "discord:"],
    "code": ["code"],
    "vscode": ["code"],
    "gestionnaire": ["taskmgr.exe"],
    "snipping": ["snippingtool.exe"],
    "spotify": ["cmd", "/c", "start", "spotify:"],
    "musique": ["cmd", "/c", "start", "wmplayer"],
}

PROCESS_NAMES = {
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "navigateur": "msedge.exe",
    "bloc-notes": "notepad.exe",
    "notepad": "notepad.exe",
    "calculatrice": "Calculator.exe",
    "word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
    "teams": "Teams.exe",
    "discord": "Discord.exe",
    "code": "Code.exe",
    "vscode": "Code.exe",
    "terminal": "WindowsTerminal.exe",
    "spotify": "Spotify.exe",
    "paint": "mspaint.exe",
}


class AppLauncherSkill:
    """Skill pour lancer et fermer des applications Windows"""

    async def launch(self, command: VoiceCommand) -> CommandResult:
        """Ouvre une application depuis la whitelist"""
        app_name = command.target.strip().lower()

        # Recherche exacte puis partielle dans la whitelist
        cmd_args = SAFE_EXECUTABLES.get(app_name)
        if not cmd_args:
            for key, val in SAFE_EXECUTABLES.items():
                if key in app_name or app_name in key:
                    cmd_args = val
                    app_name = key
                    break

        if not cmd_args:
            return CommandResult(
                False,
                f"Application '{app_name}' non reconnue. "
                f"Essayez: {', '.join(sorted(SAFE_EXECUTABLES.keys()))}"
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.sleep(0.5)
            logger.info(f"Application lancée: {app_name}")
            return CommandResult(True, f"J'ai ouvert {app_name}")
        except Exception as e:
            logger.error(f"Erreur lancement {app_name}: {e}")
            return CommandResult(False, f"Impossible d'ouvrir {app_name}")

    async def close(self, command: VoiceCommand) -> CommandResult:
        """Ferme une application par nom de processus"""
        app_name = command.target.strip().lower()
        process_name = PROCESS_NAMES.get(app_name)

        if not process_name:
            return CommandResult(False, f"Je ne sais pas fermer '{app_name}'")

        try:
            proc = await asyncio.create_subprocess_exec(
                "taskkill", "/IM", process_name, "/F",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
            if proc.returncode == 0:
                logger.info(f"Application fermée: {app_name}")
                return CommandResult(True, f"J'ai fermé {app_name}")
            else:
                return CommandResult(False, f"{app_name} n'est pas en cours d'exécution")
        except Exception as e:
            logger.error(f"Erreur fermeture {app_name}: {e}")
            return CommandResult(False, f"Impossible de fermer {app_name}")
