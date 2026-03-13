"""
JARVIS Skill - Chronometre vocal

Securite: time.time() pur en memoire.
Aucun appel systeme, aucune modification.
"""

import logging
import time
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.stopwatch")


def format_duration(seconds: float) -> str:
    """Formate une duree en texte vocal."""
    if seconds < 60:
        return f"{seconds:.1f} secondes"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} et {secs:.1f} secondes"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours} heure{'s' if hours > 1 else ''}, {mins} minute{'s' if mins > 1 else ''}"


class StopwatchSkill:

    def __init__(self):
        self._start_time: float = 0
        self._running = False
        self._laps: list[float] = []
        self._elapsed: float = 0  # accumulated time when paused

    @property
    def running(self) -> bool:
        return self._running

    @property
    def lap_count(self) -> int:
        return len(self._laps)

    def get_elapsed(self) -> float:
        """Retourne le temps ecoule en secondes."""
        if self._running:
            return self._elapsed + (time.time() - self._start_time)
        return self._elapsed

    async def start(self, command: VoiceCommand) -> CommandResult:
        """Demarre ou reprend le chronometre."""
        if self._running:
            return CommandResult(False, "Le chronomètre est déjà en marche.")

        self._running = True
        self._start_time = time.time()
        if self._elapsed == 0:
            return CommandResult(True, "Chronomètre démarré.")
        return CommandResult(True,
            f"Chronomètre repris à {format_duration(self._elapsed)}.")

    async def stop(self, command: VoiceCommand) -> CommandResult:
        """Arrete le chronometre."""
        if not self._running:
            return CommandResult(True,
                f"Chronomètre déjà arrêté. Temps: {format_duration(self._elapsed)}.")

        self._elapsed += time.time() - self._start_time
        self._running = False
        return CommandResult(True,
            f"Chronomètre arrêté. Temps: {format_duration(self._elapsed)}.",
            data={"elapsed": round(self._elapsed, 2)})

    async def lap(self, command: VoiceCommand) -> CommandResult:
        """Enregistre un tour."""
        if not self._running:
            return CommandResult(False, "Le chronomètre n'est pas en marche.")

        elapsed = self.get_elapsed()
        lap_num = len(self._laps) + 1
        self._laps.append(elapsed)

        return CommandResult(True,
            f"Tour {lap_num}: {format_duration(elapsed)}.",
            data={"lap": lap_num, "time": round(elapsed, 2)})

    async def reset(self, command: VoiceCommand) -> CommandResult:
        """Remet le chronometre a zero."""
        was_running = self._running
        self._running = False
        self._start_time = 0
        self._elapsed = 0
        self._laps.clear()
        return CommandResult(True, "Chronomètre remis à zéro.")

    async def status(self, command: VoiceCommand) -> CommandResult:
        """Donne l'etat du chronometre."""
        elapsed = self.get_elapsed()
        state = "en marche" if self._running else "arrêté"
        laps = len(self._laps)
        msg = f"Chronomètre {state}. Temps: {format_duration(elapsed)}."
        if laps:
            msg += f" {laps} tour{'s' if laps > 1 else ''} enregistré{'s' if laps > 1 else ''}."
        return CommandResult(True, msg,
            data={"elapsed": round(elapsed, 2), "running": self._running, "laps": laps})
