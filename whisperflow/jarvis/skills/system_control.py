"""
JARVIS Skill - Contrôle système Windows
Volume, luminosité, batterie, heure, veille, WiFi, Bluetooth

Note de sécurité: Ce module utilise uniquement des commandes système
prédéfinies sans interpolation d'entrée utilisateur dans les commandes shell.
"""

import asyncio
import logging
from datetime import datetime
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.system")


async def _run_ps_safe(script: str) -> str:
    """Exécute un script PowerShell prédéfini (pas d'entrée utilisateur)"""
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()


class SystemControlSkill:
    """Skill de contrôle système Windows"""

    async def volume_up(self, command: VoiceCommand) -> CommandResult:
        """Monte le volume"""
        ps = (
            "$wshell = New-Object -ComObject WScript.Shell; "
            "1..5 | ForEach-Object { $wshell.SendKeys([char]175) }"
        )
        await _run_ps_safe(ps)
        return CommandResult(True, "Volume augmenté")

    async def volume_down(self, command: VoiceCommand) -> CommandResult:
        """Baisse le volume"""
        ps = (
            "$wshell = New-Object -ComObject WScript.Shell; "
            "1..5 | ForEach-Object { $wshell.SendKeys([char]174) }"
        )
        await _run_ps_safe(ps)
        return CommandResult(True, "Volume diminué")

    async def volume_set(self, command: VoiceCommand) -> CommandResult:
        """Règle le volume à un niveau précis (0-100)"""
        try:
            level = int(command.target)
            level = max(0, min(100, level))
        except ValueError:
            return CommandResult(False, "Niveau de volume invalide")

        # On baisse à 0 puis remonte au niveau voulu via SendKeys
        steps_up = level // 2
        ps = (
            "$wshell = New-Object -ComObject WScript.Shell; "
            "1..50 | ForEach-Object { $wshell.SendKeys([char]174) }; "
            f"1..{steps_up} | ForEach-Object {{ $wshell.SendKeys([char]175) }}"
        )
        await _run_ps_safe(ps)
        return CommandResult(True, f"Volume réglé à environ {level}%")

    async def mute(self, command: VoiceCommand) -> CommandResult:
        """Active/désactive le mode muet"""
        ps = (
            "$wshell = New-Object -ComObject WScript.Shell; "
            "$wshell.SendKeys([char]173)"
        )
        await _run_ps_safe(ps)
        return CommandResult(True, "Son coupé/réactivé")

    async def brightness(self, command: VoiceCommand) -> CommandResult:
        """Règle la luminosité de l'écran"""
        try:
            level = int(command.target)
            level = max(0, min(100, level))
        except ValueError:
            return CommandResult(False, "Niveau de luminosité invalide")

        ps = (
            f"(Get-WmiObject -Namespace root\\WMI "
            f"-Class WmiMonitorBrightnessMethods)"
            f".WmiSetBrightness(1, {level})"
        )
        await _run_ps_safe(ps)
        return CommandResult(True, f"Luminosité réglée à {level}%")

    async def wifi(self, command: VoiceCommand) -> CommandResult:
        """Active ou désactive le WiFi"""
        action = command.target.strip().lower()
        enable = action in ("on", "active", "activer", "activé")
        state = "enabled" if enable else "disabled"

        proc = await asyncio.create_subprocess_exec(
            "netsh", "interface", "set", "interface", "Wi-Fi", state,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return CommandResult(True, f"WiFi {'activé' if enable else 'désactivé'}")

    async def bluetooth(self, command: VoiceCommand) -> CommandResult:
        """Active ou désactive le Bluetooth"""
        action = command.target.strip().lower()
        enable = action in ("on", "active", "activer", "activé")
        state = "On" if enable else "Off"

        ps = (
            "[Windows.Devices.Radios.Radio, Windows.System.Devices, "
            "ContentType = WindowsRuntime] | Out-Null; "
            "$radios = [Windows.Devices.Radios.Radio]::GetRadiosAsync()"
            ".GetAwaiter().GetResult(); "
            "$bt = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }; "
            "if ($bt) { $bt.SetStateAsync("
            f"[Windows.Devices.Radios.RadioState]::'{state}'"
            ").GetAwaiter().GetResult() }"
        )
        await _run_ps_safe(ps)
        return CommandResult(True, f"Bluetooth {'activé' if enable else 'désactivé'}")

    async def shutdown(self, command: VoiceCommand) -> CommandResult:
        """Éteint l'ordinateur (délai de sécurité 30s)"""
        return CommandResult(
            True,
            "Extinction programmée dans 30 secondes. Dites 'annule' pour annuler.",
            data={"pending_action": "shutdown", "args": ["/s", "/t", "30"]}
        )

    async def restart(self, command: VoiceCommand) -> CommandResult:
        """Redémarre l'ordinateur (délai de sécurité 30s)"""
        return CommandResult(
            True,
            "Redémarrage programmé dans 30 secondes. Dites 'annule' pour annuler.",
            data={"pending_action": "shutdown", "args": ["/r", "/t", "30"]}
        )

    async def sleep(self, command: VoiceCommand) -> CommandResult:
        """Verrouille l'ordinateur"""
        proc = await asyncio.create_subprocess_exec(
            "rundll32.exe", "user32.dll,LockWorkStation",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        return CommandResult(True, "Ordinateur verrouillé")

    async def battery(self, command: VoiceCommand) -> CommandResult:
        """Affiche le niveau de batterie"""
        result = await _run_ps_safe(
            "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"
        )
        if result and result.isdigit():
            return CommandResult(True, f"Batterie à {result}%")
        return CommandResult(True, "Pas de batterie détectée, vous êtes sur secteur")

    async def time(self, command: VoiceCommand) -> CommandResult:
        """Annonce l'heure actuelle"""
        now = datetime.now()
        return CommandResult(True, f"Il est {now.strftime('%H heures %M')}")

    async def date(self, command: VoiceCommand) -> CommandResult:
        """Annonce la date actuelle"""
        now = datetime.now()
        jours = ["lundi", "mardi", "mercredi", "jeudi",
                 "vendredi", "samedi", "dimanche"]
        mois_noms = ["janvier", "février", "mars", "avril", "mai", "juin",
                     "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        return CommandResult(
            True,
            f"Nous sommes {jours[now.weekday()]} {now.day} "
            f"{mois_noms[now.month - 1]} {now.year}"
        )

    async def cancel_pending(self) -> CommandResult:
        """Annule une action système en attente (shutdown, restart)"""
        proc = await asyncio.create_subprocess_exec(
            "shutdown.exe", "/a",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return CommandResult(True, "Action annulée")
