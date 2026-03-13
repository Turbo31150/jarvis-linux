"""
JARVIS Skill - Gestion alimentation et affichage Windows

Sécurité: 100% scripts statiques prédéfinis, aucune entrée utilisateur.
powercfg utilise des GUIDs Windows constants.
"""

import asyncio
import logging
import webbrowser
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.power_display")

# GUIDs de plans d'alimentation Windows standard
_PLANS = {
    "high_perf": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
    "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
    "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
}


async def _run_exec(*args) -> str:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()


class PowerDisplaySkill:

    async def power_plan(self, command: VoiceCommand) -> CommandResult:
        result = await _run_exec("powercfg", "/GetActiveScheme")
        return CommandResult(True, f"Plan actif: {result}") if result else \
            CommandResult(False, "Impossible de lire le plan")

    async def set_high_performance(self, command: VoiceCommand) -> CommandResult:
        await _run_exec("powercfg", "/SetActive", _PLANS["high_perf"])
        return CommandResult(True, "Plan haute performance activé")

    async def set_balanced(self, command: VoiceCommand) -> CommandResult:
        await _run_exec("powercfg", "/SetActive", _PLANS["balanced"])
        return CommandResult(True, "Plan équilibré activé")

    async def set_power_saver(self, command: VoiceCommand) -> CommandResult:
        await _run_exec("powercfg", "/SetActive", _PLANS["power_saver"])
        return CommandResult(True, "Plan économie d'énergie activé")

    async def hibernate(self, command: VoiceCommand) -> CommandResult:
        await _run_exec("shutdown.exe", "/h")
        return CommandResult(True, "Hibernation lancée")

    async def screen_resolution(self, command: VoiceCommand) -> CommandResult:
        result = await _run_exec(
            "powershell", "-NoProfile", "-Command",
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
            "'{0}x{1}' -f $s.Width, $s.Height")
        return CommandResult(True, f"Résolution: {result}") if result else \
            CommandResult(False, "Erreur lecture résolution")

    async def night_mode(self, command: VoiceCommand) -> CommandResult:
        webbrowser.open("ms-settings:nightlight")
        return CommandResult(True, "Paramètres mode nuit ouverts")

    async def display_settings(self, command: VoiceCommand) -> CommandResult:
        webbrowser.open("ms-settings:display")
        return CommandResult(True, "Paramètres d'affichage ouverts")

    async def sound_settings(self, command: VoiceCommand) -> CommandResult:
        webbrowser.open("ms-settings:sound")
        return CommandResult(True, "Paramètres audio ouverts")
