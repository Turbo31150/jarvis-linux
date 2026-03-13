"""
JARVIS Skill - Snapshot systeme vocal

Securite: lectures seules via psutil (lecture memoire/cpu/disque).
Aucune modification systeme, aucune commande dangereuse.
"""

import logging
import platform
from datetime import datetime
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.system_snapshot")


def _get_system_info() -> dict:
    """Collecte les informations systeme de base (sans psutil)."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "node": platform.node(),
        "timestamp": datetime.now().isoformat(),
    }
    return info


def _try_psutil_info() -> dict:
    """Essaie de collecter les infos psutil si disponible."""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": cpu_percent,
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "disk_used_gb": round(disk.used / (1024**3), 1),
            "disk_percent": round(disk.percent, 1),
            "process_count": len(psutil.pids()),
        }
    except ImportError:
        return {}


class SystemSnapshotSkill:

    def __init__(self):
        self._snapshots: list[dict] = []
        self._max_snapshots = 10

    async def take_snapshot(self, command: VoiceCommand) -> CommandResult:
        """Prend un snapshot de l'etat systeme actuel."""
        info = _get_system_info()
        perf = _try_psutil_info()
        info.update(perf)

        self._snapshots.append(info)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)

        # Construire le message vocal
        parts = [f"Snapshot système pris."]
        if "cpu_percent" in info:
            parts.append(f"CPU: {info['cpu_percent']}%")
        if "ram_percent" in info:
            parts.append(f"RAM: {info['ram_percent']}% ({info['ram_used_gb']} sur {info['ram_total_gb']} Go)")
        if "disk_percent" in info:
            parts.append(f"Disque: {info['disk_percent']}%")
        if "process_count" in info:
            parts.append(f"{info['process_count']} processus")

        return CommandResult(True, " ".join(parts), data=info)

    async def compare(self, command: VoiceCommand) -> CommandResult:
        """Compare le dernier snapshot avec le precedent."""
        if len(self._snapshots) < 2:
            return CommandResult(False,
                "Il faut au moins 2 snapshots pour comparer. "
                "Dites 'snapshot système' pour en prendre un.")

        current = self._snapshots[-1]
        previous = self._snapshots[-2]

        changes = []
        for key in ("cpu_percent", "ram_percent", "disk_percent"):
            if key in current and key in previous:
                diff = current[key] - previous[key]
                name = key.replace("_percent", "").upper()
                if abs(diff) >= 1:
                    direction = "augmenté" if diff > 0 else "diminué"
                    changes.append(f"{name} a {direction} de {abs(diff):.1f}%")

        if not changes:
            return CommandResult(True, "Pas de changement significatif depuis le dernier snapshot.")

        return CommandResult(True,
            f"Changements depuis le dernier snapshot: {'. '.join(changes)}.")

    async def history(self, command: VoiceCommand) -> CommandResult:
        """Affiche l'historique des snapshots."""
        if not self._snapshots:
            return CommandResult(True, "Aucun snapshot enregistré.")

        count = len(self._snapshots)
        last = self._snapshots[-1]
        ts = last.get("timestamp", "inconnu")

        return CommandResult(True,
            f"{count} snapshot{'s' if count > 1 else ''} enregistré{'s' if count > 1 else ''}. "
            f"Dernier: {ts}")

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)
