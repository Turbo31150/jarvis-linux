"""
JARVIS Skill - Minuteurs et rappels vocaux

Sécurité: aucun appel système, tout en mémoire asyncio.
Les durées sont parsées depuis le texte vocal français.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.timer")

# Parse durées FR: "5 minutes", "1 heure", "30 secondes", "2h30"
_DURATION_PATTERNS = [
    (re.compile(r'(\d+)\s*h(?:eures?)?(?:\s*(\d+))?', re.IGNORECASE), 'hm'),
    (re.compile(r'(\d+)\s*min(?:utes?)?', re.IGNORECASE), 'm'),
    (re.compile(r'(\d+)\s*sec(?:ondes?)?', re.IGNORECASE), 's'),
    (re.compile(r'(\d+)\s*heures?', re.IGNORECASE), 'h'),
]


def _parse_duration(text: str) -> int:
    """Parse une durée vocale en secondes. Retourne 0 si invalide."""
    # "2h30" ou "2 heures 30"
    m = re.search(r'(\d+)\s*h(?:eures?)?\s*(\d+)', text, re.IGNORECASE)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60

    # "X heures" or "Xh"
    m = re.search(r'(\d+)\s*h(?:eures?)?(?!\d)', text, re.IGNORECASE)
    if m:
        return int(m.group(1)) * 3600

    # "X minutes" or "Xmin"
    m = re.search(r'(\d+)\s*min(?:utes?)?', text, re.IGNORECASE)
    if m:
        return int(m.group(1)) * 60

    # "X secondes" or "Xsec" or "Xs"
    m = re.search(r'(\d+)\s*s(?:ec(?:ondes?)?)?(?!\w)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Nombre seul -> minutes par défaut
    m = re.search(r'(\d+)', text)
    if m:
        return int(m.group(1)) * 60

    return 0


def _format_duration(seconds: int) -> str:
    """Formate secondes en texte FR lisible."""
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h} heure{'s' if h > 1 else ''}" + (f" {m} minutes" if m else "")
    if seconds >= 60:
        m = seconds // 60
        s = seconds % 60
        return f"{m} minute{'s' if m > 1 else ''}" + (f" {s} secondes" if s else "")
    return f"{seconds} seconde{'s' if seconds > 1 else ''}"


class TimerReminderSkill:

    def __init__(self):
        self._timers: dict[str, asyncio.Task] = {}
        self._timer_count = 0
        self._on_timer_done = None  # callback(name, message) appelé quand timer expire

    def set_callback(self, callback):
        """Définit le callback appelé quand un timer expire."""
        self._on_timer_done = callback

    async def set_timer(self, command: VoiceCommand) -> CommandResult:
        """Démarre un minuteur. Ex: 'minuteur 5 minutes'"""
        text = command.target or command.raw_text
        seconds = _parse_duration(text)
        if seconds <= 0:
            return CommandResult(False, "Je n'ai pas compris la durée")
        if seconds > 86400:
            return CommandResult(False, "Durée maximum: 24 heures")

        self._timer_count += 1
        name = f"timer_{self._timer_count}"
        duration_text = _format_duration(seconds)

        async def _countdown():
            await asyncio.sleep(seconds)
            self._timers.pop(name, None)
            if self._on_timer_done:
                await self._on_timer_done(name, f"Minuteur terminé: {duration_text}")

        task = asyncio.create_task(_countdown())
        self._timers[name] = task
        return CommandResult(True, f"Minuteur lancé: {duration_text}",
                             data={"timer_name": name, "seconds": seconds})

    async def set_reminder(self, command: VoiceCommand) -> CommandResult:
        """Définit un rappel. Ex: 'rappelle-moi dans 10 minutes'"""
        text = command.target or command.raw_text
        seconds = _parse_duration(text)
        if seconds <= 0:
            return CommandResult(False, "Je n'ai pas compris le délai")

        # Extraire le message du rappel (après "de/que")
        msg_match = re.search(r'(?:de|que)\s+(.+?)(?:\s+dans\s+\d|$)', text, re.IGNORECASE)
        reminder_msg = msg_match.group(1) if msg_match else "Rappel"

        self._timer_count += 1
        name = f"reminder_{self._timer_count}"
        duration_text = _format_duration(seconds)

        async def _countdown():
            await asyncio.sleep(seconds)
            self._timers.pop(name, None)
            if self._on_timer_done:
                await self._on_timer_done(name, f"Rappel: {reminder_msg}")

        task = asyncio.create_task(_countdown())
        self._timers[name] = task
        return CommandResult(True, f"Rappel dans {duration_text}")

    async def cancel_timer(self, command: VoiceCommand) -> CommandResult:
        """Annule tous les minuteurs actifs."""
        if not self._timers:
            return CommandResult(True, "Aucun minuteur actif")
        count = len(self._timers)
        for task in self._timers.values():
            task.cancel()
        self._timers.clear()
        return CommandResult(True, f"{count} minuteur{'s' if count > 1 else ''} annulé{'s' if count > 1 else ''}")

    async def list_timers(self, command: VoiceCommand) -> CommandResult:
        """Liste les minuteurs actifs."""
        if not self._timers:
            return CommandResult(True, "Aucun minuteur actif")
        names = ", ".join(self._timers.keys())
        return CommandResult(True, f"{len(self._timers)} actif{'s' if len(self._timers) > 1 else ''}: {names}")

    @property
    def active_count(self) -> int:
        return len(self._timers)
