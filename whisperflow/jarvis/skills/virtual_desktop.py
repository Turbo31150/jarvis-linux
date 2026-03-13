"""
JARVIS Skill - Bureaux virtuels Windows 10/11

Securite: 100% raccourcis clavier statiques predefinis.
Aucune entree utilisateur dans les commandes.
"""

import asyncio
import logging
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.virtual_desktop")

# Scripts PowerShell statiques pour raccourcis clavier Windows
_SCRIPTS = {
    "new_desktop": (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('^#{d}')"
    ),
    "close_desktop": (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('^#{F4}')"
    ),
    "desktop_left": (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('^#{LEFT}')"
    ),
    "desktop_right": (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('^#{RIGHT}')"
    ),
    "task_view": (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('#{TAB}')"
    ),
}


async def _run_static_ps(script_key: str) -> bool:
    """Lance un script PS statique predefini (pas d'entree utilisateur)."""
    script = _SCRIPTS[script_key]
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await proc.wait()
    return proc.returncode == 0


class VirtualDesktopSkill:

    async def new_desktop(self, command: VoiceCommand) -> CommandResult:
        ok = await _run_static_ps("new_desktop")
        return CommandResult(ok, "Nouveau bureau virtuel" if ok else "Erreur")

    async def close_desktop(self, command: VoiceCommand) -> CommandResult:
        ok = await _run_static_ps("close_desktop")
        return CommandResult(ok, "Bureau virtuel ferme" if ok else "Erreur")

    async def switch_left(self, command: VoiceCommand) -> CommandResult:
        ok = await _run_static_ps("desktop_left")
        return CommandResult(ok, "Bureau precedent" if ok else "Erreur")

    async def switch_right(self, command: VoiceCommand) -> CommandResult:
        ok = await _run_static_ps("desktop_right")
        return CommandResult(ok, "Bureau suivant" if ok else "Erreur")

    async def task_view(self, command: VoiceCommand) -> CommandResult:
        ok = await _run_static_ps("task_view")
        return CommandResult(ok, "Vue des taches" if ok else "Erreur")
