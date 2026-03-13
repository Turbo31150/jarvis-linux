"""
JARVIS Skill - Pomodoro (technique de productivite)

Securite: tout en memoire asyncio, pas d'appel systeme.
Cycles: 25min travail, 5min pause (configurable par voix).
"""

import asyncio
import logging
from datetime import datetime
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.pomodoro")

# Durees par defaut (secondes)
_DEFAULT_WORK = 25 * 60     # 25 minutes
_DEFAULT_BREAK = 5 * 60     # 5 minutes
_DEFAULT_LONG_BREAK = 15 * 60  # 15 minutes (après 4 cycles)


class PomodoroSkill:

    def __init__(self):
        self._active = False
        self._task: asyncio.Task = None
        self._cycle = 0
        self._total_cycles = 0
        self._phase = "idle"  # idle, work, break, long_break
        self._work_duration = _DEFAULT_WORK
        self._break_duration = _DEFAULT_BREAK
        self._on_phase_change = None  # callback(phase, message)

    def set_callback(self, callback):
        """Callback appele a chaque changement de phase."""
        self._on_phase_change = callback

    @property
    def active(self) -> bool:
        return self._active

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def cycle(self) -> int:
        return self._cycle

    @property
    def total_completed(self) -> int:
        return self._total_cycles

    async def start(self, command: VoiceCommand) -> CommandResult:
        """Demarre un cycle Pomodoro."""
        if self._active:
            return CommandResult(False,
                f"Pomodoro déjà actif: phase {self._phase}, cycle {self._cycle}")

        self._active = True
        self._cycle = 1
        self._phase = "work"

        self._task = asyncio.create_task(self._run_cycle())
        return CommandResult(True,
            f"Pomodoro lancé! Cycle 1: travail pendant "
            f"{self._work_duration // 60} minutes. C'est parti!")

    async def stop(self, command: VoiceCommand) -> CommandResult:
        """Arrete le Pomodoro en cours."""
        if not self._active:
            return CommandResult(True, "Aucun Pomodoro actif")

        self._active = False
        if self._task:
            self._task.cancel()
            self._task = None

        completed = self._cycle - 1 if self._phase == "work" else self._cycle
        self._phase = "idle"
        return CommandResult(True,
            f"Pomodoro arrêté. {completed} cycle{'s' if completed != 1 else ''} "
            f"complété{'s' if completed != 1 else ''}.")

    async def status(self, command: VoiceCommand) -> CommandResult:
        """Donne l'etat du Pomodoro."""
        if not self._active:
            return CommandResult(True,
                f"Pomodoro inactif. {self._total_cycles} cycles "
                f"complétés au total.")

        phase_name = {
            "work": "travail", "break": "pause",
            "long_break": "longue pause", "idle": "inactif"
        }
        return CommandResult(True,
            f"Pomodoro actif: {phase_name.get(self._phase, self._phase)}, "
            f"cycle {self._cycle}. "
            f"{self._total_cycles} cycles complétés au total.")

    async def _run_cycle(self):
        """Boucle principale du Pomodoro."""
        try:
            while self._active:
                # Phase travail
                self._phase = "work"
                if self._on_phase_change:
                    await self._on_phase_change("work",
                        f"Cycle {self._cycle}: travail pendant "
                        f"{self._work_duration // 60} minutes")

                await asyncio.sleep(self._work_duration)

                if not self._active:
                    break

                self._total_cycles += 1

                # Pause longue tous les 4 cycles
                if self._cycle % 4 == 0:
                    self._phase = "long_break"
                    pause_time = _DEFAULT_LONG_BREAK
                    msg = f"Cycle {self._cycle} terminé! Longue pause de {pause_time // 60} minutes"
                else:
                    self._phase = "break"
                    pause_time = self._break_duration
                    msg = f"Cycle {self._cycle} terminé! Pause de {pause_time // 60} minutes"

                if self._on_phase_change:
                    await self._on_phase_change(self._phase, msg)

                await asyncio.sleep(pause_time)

                if not self._active:
                    break

                self._cycle += 1

        except asyncio.CancelledError:
            pass
        finally:
            self._phase = "idle"
