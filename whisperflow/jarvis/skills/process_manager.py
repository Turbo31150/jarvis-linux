"""
JARVIS Skill - Gestionnaire de processus Windows
Liste, tue, surveille les processus et ressources système

Sécurité: Tous les scripts PowerShell sont des constantes statiques
prédéfinies. taskkill valide les noms via regex alphanumériques.
Aucune entrée utilisateur n'est interpolée dans les commandes shell.
"""

import asyncio
import json
import logging
import re
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.process")

# ====== SCRIPTS POWERSHELL 100% STATIQUES ======
PS_TOP_CPU = (
    "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 "
    "Name, @{N='CPU';E={[math]::Round($_.CPU,1)}}, "
    "@{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,0)}} | ConvertTo-Json"
)
PS_SYS_INFO = (
    "$cpu = (Get-WmiObject Win32_Processor).LoadPercentage; "
    "$ram = Get-WmiObject Win32_OperatingSystem; "
    "$usedGB = [math]::Round(($ram.TotalVisibleMemorySize - "
    "$ram.FreePhysicalMemory)/1MB, 1); "
    "$totalGB = [math]::Round($ram.TotalVisibleMemorySize/1MB, 1); "
    "$ramPct = [math]::Round(($ram.TotalVisibleMemorySize - "
    "$ram.FreePhysicalMemory) / $ram.TotalVisibleMemorySize * 100, 0); "
    "@{CPU=$cpu; RAM_Used_GB=$usedGB; RAM_Total_GB=$totalGB; "
    "RAM_Pct=$ramPct} | ConvertTo-Json"
)
PS_DISK_SPACE = (
    "Get-PSDrive -PSProvider FileSystem | Where-Object {$_.Used -gt 0} | "
    "Select-Object Name, @{N='Used_GB';E={[math]::Round($_.Used/1GB,1)}}, "
    "@{N='Free_GB';E={[math]::Round($_.Free/1GB,1)}}, "
    "@{N='Total_GB';E={[math]::Round(($_.Used+$_.Free)/1GB,1)}} | "
    "ConvertTo-Json"
)
PS_UPTIME = (
    "$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime; "
    "$up = (Get-Date) - $boot; "
    "'{0} jours {1} heures {2} minutes' -f $up.Days, $up.Hours, $up.Minutes"
)
PS_LIST_PROCESSES = (
    "Get-Process | Sort-Object WorkingSet64 -Descending | "
    "Select-Object -First 15 Name, Id, "
    "@{N='RAM_MB';E={[math]::Round($_.WorkingSet64/1MB,0)}} | ConvertTo-Json"
)
PS_GPU_INFO = (
    "Get-WmiObject Win32_VideoController | Select-Object Name, "
    "@{N='VRAM_GB';E={[math]::Round($_.AdapterRAM/1GB,1)}}, "
    "DriverVersion, Status | ConvertTo-Json"
)
PS_IP_ADDRESS = (
    "(Get-NetIPAddress -AddressFamily IPv4 | "
    "Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | "
    "Select-Object -First 1).IPAddress"
)

# Regex pour valider les noms de processus
SAFE_PROCESS_NAME = re.compile(r'^[a-zA-Z0-9_.\-]{1,64}$')


async def _run_ps_static(script: str) -> str:
    """Exécute un script PowerShell prédéfini statique"""
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return stdout.decode("utf-8", errors="replace").strip()


class ProcessManagerSkill:
    """Skill de gestion des processus et monitoring système"""

    async def list_processes(self, command: VoiceCommand) -> CommandResult:
        """Liste les 15 processus les plus gourmands en RAM"""
        result = await _run_ps_static(PS_LIST_PROCESSES)
        try:
            processes = json.loads(result)
            if isinstance(processes, dict):
                processes = [processes]
            lines = [f"- {p['Name']} (PID {p['Id']}, {p['RAM_MB']} Mo)"
                     for p in processes[:10]]
            return CommandResult(True, "Top 10 processus:\n" + "\n".join(lines))
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Impossible de lister les processus")

    async def kill_process(self, command: VoiceCommand) -> CommandResult:
        """Tue un processus par nom (validé par regex)"""
        name = command.target.strip()
        if not name:
            return CommandResult(False, "Quel processus tuer ?")
        if not name.endswith(".exe"):
            name += ".exe"
        if not SAFE_PROCESS_NAME.match(name):
            return CommandResult(False, f"Nom de processus invalide: {name}")

        proc = await asyncio.create_subprocess_exec(
            "taskkill", "/IM", name, "/F",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        if proc.returncode == 0:
            return CommandResult(True, f"Processus {name} terminé")
        return CommandResult(False, f"{name} introuvable")

    async def system_resources(self, command: VoiceCommand) -> CommandResult:
        """Affiche CPU, RAM"""
        result = await _run_ps_static(PS_SYS_INFO)
        try:
            info = json.loads(result)
            return CommandResult(True,
                f"Processeur à {info['CPU']}%. "
                f"Mémoire: {info['RAM_Used_GB']} sur {info['RAM_Total_GB']} Go, "
                f"{info['RAM_Pct']}% utilisé.")
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Impossible de lire les ressources")

    async def top_cpu(self, command: VoiceCommand) -> CommandResult:
        """Top 5 processus par CPU"""
        result = await _run_ps_static(PS_TOP_CPU)
        try:
            procs = json.loads(result)
            if isinstance(procs, dict):
                procs = [procs]
            lines = [f"- {p['Name']}: CPU {p.get('CPU', '?')}%, {p['RAM_MB']} Mo"
                     for p in procs[:5]]
            return CommandResult(True, "Top CPU:\n" + "\n".join(lines))
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Erreur lecture CPU")

    async def disk_space(self, command: VoiceCommand) -> CommandResult:
        """Affiche l'espace disque"""
        result = await _run_ps_static(PS_DISK_SPACE)
        try:
            drives = json.loads(result)
            if isinstance(drives, dict):
                drives = [drives]
            lines = [f"- Disque {d['Name']}: {d['Free_GB']} Go libres sur {d['Total_GB']} Go"
                     for d in drives]
            return CommandResult(True, "Espace disque:\n" + "\n".join(lines))
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Erreur lecture disque")

    async def uptime(self, command: VoiceCommand) -> CommandResult:
        """Temps depuis dernier démarrage"""
        result = await _run_ps_static(PS_UPTIME)
        if result:
            return CommandResult(True, f"Ordinateur allumé depuis {result}")
        return CommandResult(False, "Impossible de déterminer l'uptime")

    async def gpu_info(self, command: VoiceCommand) -> CommandResult:
        """Carte graphique"""
        result = await _run_ps_static(PS_GPU_INFO)
        try:
            gpu = json.loads(result)
            if isinstance(gpu, list):
                gpu = gpu[0]
            return CommandResult(True,
                f"GPU: {gpu.get('Name', '?')}, {gpu.get('VRAM_GB', '?')} Go VRAM")
        except (json.JSONDecodeError, KeyError):
            return CommandResult(False, "Erreur lecture GPU")

    async def ip_address(self, command: VoiceCommand) -> CommandResult:
        """Adresse IP locale"""
        result = await _run_ps_static(PS_IP_ADDRESS)
        if result:
            return CommandResult(True, f"Adresse IP: {result}")
        return CommandResult(False, "Impossible de déterminer l'adresse IP")

    async def hardware_info(self, command: VoiceCommand) -> CommandResult:
        """Résumé matériel complet"""
        parts = []
        sys_r = await _run_ps_static(PS_SYS_INFO)
        try:
            info = json.loads(sys_r)
            parts.append(
                f"CPU {info['CPU']}%. RAM {info['RAM_Used_GB']}/{info['RAM_Total_GB']} Go.")
        except (json.JSONDecodeError, KeyError):
            pass
        gpu_r = await _run_ps_static(PS_GPU_INFO)
        try:
            gpu = json.loads(gpu_r)
            if isinstance(gpu, list):
                gpu = gpu[0]
            parts.append(f"GPU: {gpu.get('Name', '?')}.")
        except (json.JSONDecodeError, KeyError):
            pass
        uptime_r = await _run_ps_static(PS_UPTIME)
        if uptime_r:
            parts.append(f"Allumé depuis {uptime_r}.")
        return CommandResult(True, " ".join(parts) if parts else "Infos indisponibles")
