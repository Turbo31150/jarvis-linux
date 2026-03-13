"""
JARVIS Skill - Gestion des fenêtres Windows
Minimiser, maximiser, basculer, bureau, capture d'écran

Sécurité: Toutes les commandes PowerShell sont des scripts statiques prédéfinis,
aucune entrée utilisateur n'est interpolée dans les commandes shell.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.window")

# Scripts PowerShell prédéfinis (aucune entrée utilisateur)
PS_MINIMIZE = (
    "$wshell = New-Object -ComObject WScript.Shell; "
    "$wshell.SendKeys('% n')"
)
PS_MAXIMIZE = (
    "$wshell = New-Object -ComObject WScript.Shell; "
    "$wshell.SendKeys('% x')"
)
PS_RESTORE = (
    "$wshell = New-Object -ComObject WScript.Shell; "
    "$wshell.SendKeys('% r')"
)
PS_ALT_TAB = (
    "$wshell = New-Object -ComObject WScript.Shell; "
    "$wshell.SendKeys('%{TAB}')"
)
PS_SHOW_DESKTOP = (
    "(New-Object -ComObject Shell.Application).ToggleDesktop()"
)


async def _run_ps_static(script: str):
    """Exécute un script PowerShell statique prédéfini"""
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()


class WindowManagerSkill:
    """Skill de gestion des fenêtres Windows"""

    async def minimize(self, command: VoiceCommand) -> CommandResult:
        """Minimise la fenêtre active"""
        await _run_ps_static(PS_MINIMIZE)
        return CommandResult(True, "Fenêtre minimisée")

    async def maximize(self, command: VoiceCommand) -> CommandResult:
        """Maximise la fenêtre active"""
        await _run_ps_static(PS_MAXIMIZE)
        return CommandResult(True, "Fenêtre maximisée")

    async def restore(self, command: VoiceCommand) -> CommandResult:
        """Restaure la fenêtre active"""
        await _run_ps_static(PS_RESTORE)
        return CommandResult(True, "Fenêtre restaurée")

    async def switch(self, command: VoiceCommand) -> CommandResult:
        """Bascule vers la fenêtre suivante (Alt+Tab)"""
        await _run_ps_static(PS_ALT_TAB)
        return CommandResult(True, "Fenêtre basculée")

    async def desktop(self, command: VoiceCommand) -> CommandResult:
        """Affiche le bureau"""
        await _run_ps_static(PS_SHOW_DESKTOP)
        return CommandResult(True, "Bureau affiché")

    async def screenshot(self, command: VoiceCommand) -> CommandResult:
        """Capture l'écran et sauvegarde en PNG"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshots_dir = Path.home() / "Pictures" / "JARVIS_Screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        filepath = screenshots_dir / f"capture_{timestamp}.png"

        # Le chemin est généré par le code, pas par l'utilisateur
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "$b = New-Object System.Drawing.Bitmap($s.Width, $s.Height); "
            "$g = [System.Drawing.Graphics]::FromImage($b); "
            "$g.CopyFromScreen($s.Location, [System.Drawing.Point]::Empty, $s.Size); "
            f"$b.Save('{filepath}'); "
            "$g.Dispose(); $b.Dispose()"
        )
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-NoProfile", "-Command", ps,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        if filepath.exists():
            return CommandResult(True, f"Capture sauvegardée: {filepath}")
        return CommandResult(False, "Erreur lors de la capture d'écran")
