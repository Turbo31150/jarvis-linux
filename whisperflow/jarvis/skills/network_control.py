"""
JARVIS Skill - Contrôle réseau Windows

Sécurité: Scripts PS 100% statiques. ping valide l'hôte via regex strict.
"""

import asyncio
import json
import logging
import re
import webbrowser
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.network")

SAFE_HOST = re.compile(r'^[a-zA-Z0-9.\-]{1,253}$')

_PS = {
    "status": (
        "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | "
        "Select-Object Name, InterfaceDescription, LinkSpeed | ConvertTo-Json"),
    "ip_local": (
        "Get-NetIPAddress -AddressFamily IPv4 | "
        "Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | "
        "Select-Object InterfaceAlias, IPAddress | ConvertTo-Json"),
    "ip_public": (
        "(Invoke-WebRequest -Uri 'https://api.ipify.org' -UseBasicParsing "
        "-TimeoutSec 5).Content"),
    "dns": (
        "Get-DnsClientServerAddress -AddressFamily IPv4 | "
        "Where-Object {$_.ServerAddresses.Count -gt 0} | "
        "Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json"),
    "wifi": "netsh wlan show networks mode=bssid",
}


async def _ps(name: str) -> str:
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", _PS[name],
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()


class NetworkControlSkill:

    async def network_status(self, command: VoiceCommand) -> CommandResult:
        result = await _ps("status")
        try:
            adapters = json.loads(result)
            if isinstance(adapters, dict):
                adapters = [adapters]
            lines = [f"- {a['Name']}: {a.get('LinkSpeed', '?')}" for a in adapters]
            return CommandResult(True, f"{len(adapters)} interfaces actives:\n" + "\n".join(lines))
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Impossible de lire le réseau")

    async def ip_local(self, command: VoiceCommand) -> CommandResult:
        result = await _ps("ip_local")
        try:
            ips = json.loads(result)
            if isinstance(ips, dict):
                ips = [ips]
            lines = [f"- {ip['InterfaceAlias']}: {ip['IPAddress']}" for ip in ips]
            return CommandResult(True, "Adresses IP:\n" + "\n".join(lines))
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Impossible de lire les IPs")

    async def ip_public(self, command: VoiceCommand) -> CommandResult:
        result = await _ps("ip_public")
        if result and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', result):
            return CommandResult(True, f"IP publique: {result}")
        return CommandResult(False, "Impossible de déterminer l'IP publique")

    async def ping(self, command: VoiceCommand) -> CommandResult:
        host = command.target.strip() or "google.com"
        if not SAFE_HOST.match(host):
            return CommandResult(False, f"Hôte invalide: {host}")
        proc = await asyncio.create_subprocess_exec(
            "ping", "-n", "3", host,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode == 0:
            for line in output.split("\n"):
                if "Moyenne" in line or "Average" in line:
                    return CommandResult(True, f"Ping {host}: {line.strip()}")
            return CommandResult(True, f"Ping {host}: connexion OK")
        return CommandResult(False, f"Ping {host} échoué")

    async def wifi_list(self, command: VoiceCommand) -> CommandResult:
        proc = await asyncio.create_subprocess_exec(
            "netsh", "wlan", "show", "networks",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        result = stdout.decode("utf-8", errors="replace").strip()
        if result:
            return CommandResult(True, f"Réseaux WiFi:\n{result[:500]}")
        return CommandResult(False, "Aucun réseau WiFi détecté")

    async def speed_test(self, command: VoiceCommand) -> CommandResult:
        webbrowser.open("https://www.speedtest.net")
        return CommandResult(True, "Ouverture du test de débit")
