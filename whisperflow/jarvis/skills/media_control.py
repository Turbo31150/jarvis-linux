"""
JARVIS Skill - Contrôle multimédia Windows
Play, pause, suivant, précédent via les touches média système

Sécurité: Utilise uniquement des scripts PowerShell statiques prédéfinis
avec des codes de touches virtuelles constants. Aucune entrée utilisateur
n'est passée aux commandes shell.
"""

import asyncio
import logging
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.media")

# Scripts PowerShell statiques pour chaque touche média
_PS_TYPE_DEF = (
    "Add-Type -TypeDefinition '"
    "using System; using System.Runtime.InteropServices; "
    "public class MK { "
    "[DllImport(\"user32.dll\")] "
    "public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo); "
    "}'"
)

PS_PLAY_PAUSE = f"{_PS_TYPE_DEF}; [MK]::keybd_event(0xB3, 0, 0, 0); [MK]::keybd_event(0xB3, 0, 2, 0)"
PS_NEXT = f"{_PS_TYPE_DEF}; [MK]::keybd_event(0xB0, 0, 0, 0); [MK]::keybd_event(0xB0, 0, 2, 0)"
PS_PREV = f"{_PS_TYPE_DEF}; [MK]::keybd_event(0xB1, 0, 0, 0); [MK]::keybd_event(0xB1, 0, 2, 0)"
PS_STOP = f"{_PS_TYPE_DEF}; [MK]::keybd_event(0xB2, 0, 0, 0); [MK]::keybd_event(0xB2, 0, 2, 0)"


async def _run_ps_static(script: str):
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()


class MediaControlSkill:
    """Skill de contrôle multimédia"""

    async def play(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static(PS_PLAY_PAUSE)
        return CommandResult(True, "Lecture/Pause")

    async def pause(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static(PS_PLAY_PAUSE)
        return CommandResult(True, "Pause")

    async def next_track(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static(PS_NEXT)
        return CommandResult(True, "Piste suivante")

    async def previous_track(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static(PS_PREV)
        return CommandResult(True, "Piste précédente")

    async def stop(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static(PS_STOP)
        return CommandResult(True, "Lecture arrêtée")
