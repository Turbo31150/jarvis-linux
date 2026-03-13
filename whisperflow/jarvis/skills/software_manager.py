"""
JARVIS Skill - Gestion logiciels Windows via winget

Sécurité: winget appelé via create_subprocess_exec (pas de shell).
Noms de paquets validés par regex alphanumérique strict avant passage en argument.
"""

import asyncio
import logging
import re
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.software")

SAFE_PACKAGE = re.compile(r'^[a-zA-Z0-9._\-]{1,128}$')


class SoftwareManagerSkill:

    async def install(self, command: VoiceCommand) -> CommandResult:
        pkg = command.target.strip()
        if not pkg or not SAFE_PACKAGE.match(pkg):
            return CommandResult(False, f"Nom de paquet invalide: '{pkg}'")
        proc = await asyncio.create_subprocess_exec(
            "winget", "install", "--id", pkg,
            "--accept-source-agreements", "--accept-package-agreements", "-e",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")
        if proc.returncode == 0:
            return CommandResult(True, f"{pkg} installé")
        if "already installed" in output.lower():
            return CommandResult(True, f"{pkg} déjà installé")
        return CommandResult(False, f"Échec installation {pkg}")

    async def uninstall(self, command: VoiceCommand) -> CommandResult:
        pkg = command.target.strip()
        if not pkg or not SAFE_PACKAGE.match(pkg):
            return CommandResult(False, f"Nom invalide: '{pkg}'")
        proc = await asyncio.create_subprocess_exec(
            "winget", "uninstall", "--id", pkg, "-e",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.wait()
        return CommandResult(proc.returncode == 0,
            f"{pkg} désinstallé" if proc.returncode == 0 else f"Échec {pkg}")

    async def update_all(self, command: VoiceCommand) -> CommandResult:
        proc = await asyncio.create_subprocess_exec(
            "winget", "upgrade", "--all", "--accept-source-agreements",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await proc.communicate()
        return CommandResult(True, "Mise à jour lancée")

    async def list_installed(self, command: VoiceCommand) -> CommandResult:
        proc = await asyncio.create_subprocess_exec(
            "winget", "list", "--count", "15",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace").strip()
        return CommandResult(bool(output), output[:800] if output else "Erreur")

    async def check_updates(self, command: VoiceCommand) -> CommandResult:
        proc = await asyncio.create_subprocess_exec(
            "winget", "upgrade",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace").strip()
        return CommandResult(True, output[:600] if output else "Tout est à jour")
