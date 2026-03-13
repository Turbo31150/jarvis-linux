"""
JARVIS Skill - Gestionnaire du presse-papiers Windows
Copier, coller, couper, annuler, sélectionner tout

Sécurité: Scripts PowerShell 100% statiques (SendKeys constants).
Aucune entrée utilisateur n'est interpolée dans les commandes shell.
"""

import asyncio
import logging
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.clipboard")

# Tous les scripts sont des constantes statiques, pas d'input utilisateur
_SCRIPTS = {
    "copy": "$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^c')",
    "paste": "$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^v')",
    "cut": "$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^x')",
    "undo": "$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^z')",
    "select_all": "$wshell = New-Object -ComObject WScript.Shell; $wshell.SendKeys('^a')",
    "read": "Get-Clipboard",
}


async def _run_static_ps(name: str, capture: bool = False) -> str:
    script = _SCRIPTS[name]
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip() if capture else ""


class ClipboardManagerSkill:
    """Skill presse-papiers"""

    async def copy(self, command: VoiceCommand) -> CommandResult:
        await _run_static_ps("copy")
        return CommandResult(True, "Copié")

    async def paste(self, command: VoiceCommand) -> CommandResult:
        await _run_static_ps("paste")
        return CommandResult(True, "Collé")

    async def cut(self, command: VoiceCommand) -> CommandResult:
        await _run_static_ps("cut")
        return CommandResult(True, "Coupé")

    async def undo(self, command: VoiceCommand) -> CommandResult:
        await _run_static_ps("undo")
        return CommandResult(True, "Annulé")

    async def select_all(self, command: VoiceCommand) -> CommandResult:
        await _run_static_ps("select_all")
        return CommandResult(True, "Tout sélectionné")

    async def read_clipboard(self, command: VoiceCommand) -> CommandResult:
        content = await _run_static_ps("read", capture=True)
        if content:
            short = content[:200] + "..." if len(content) > 200 else content
            return CommandResult(True, f"Dans le presse-papiers: {short}")
        return CommandResult(True, "Le presse-papiers est vide")
