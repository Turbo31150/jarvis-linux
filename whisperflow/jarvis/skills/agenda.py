"""
JARVIS Skill - Agenda vocal simple

Securite: stockage en memoire uniquement (list de dicts).
Aucun acces fichier, aucun appel externe.
"""

import logging
import re
from datetime import datetime, timedelta
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.agenda")

_MAX_EVENTS = 50


def _parse_time(text: str):
    """Extrait une heure depuis du texte. Retourne (heure, minute) ou None."""
    m = re.search(r'(\d{1,2})\s*[h:]\s*(\d{0,2})', text.lower())
    if m:
        h = int(m.group(1))
        mins = int(m.group(2)) if m.group(2) else 0
        if 0 <= h <= 23 and 0 <= mins <= 59:
            return (h, mins)
    return None


class AgendaSkill:

    def __init__(self):
        self._events: list[dict] = []

    @property
    def count(self) -> int:
        return len(self._events)

    def get_events(self) -> list[dict]:
        return list(self._events)

    async def add_event(self, command: VoiceCommand) -> CommandResult:
        """Ajoute un evenement a l'agenda."""
        text = command.target or ""
        if not text:
            return CommandResult(False,
                "Dites l'heure et la description. Exemple: 14h reunion.")

        if len(self._events) >= _MAX_EVENTS:
            return CommandResult(False,
                f"Maximum {_MAX_EVENTS} événements atteint.")

        time_info = _parse_time(text)
        # Retire l'heure du texte pour garder la description
        desc = text
        if time_info:
            desc = re.sub(r'\d{1,2}\s*[h:]\s*\d{0,2}', '', text).strip()

        event = {
            "description": desc or text,
            "time": f"{time_info[0]:02d}:{time_info[1]:02d}" if time_info else None,
            "created": datetime.now().isoformat(),
        }
        self._events.append(event)

        time_str = f" à {event['time']}" if event['time'] else ""
        return CommandResult(True,
            f"Événement ajouté{time_str}: {event['description']}.",
            data=event)

    async def list_events(self, command: VoiceCommand) -> CommandResult:
        """Liste les evenements de l'agenda."""
        if not self._events:
            return CommandResult(True,
                "Agenda vide. Dites 'agenda ajoute' suivi d'un événement.")

        # Trie par heure si disponible
        sorted_events = sorted(self._events,
            key=lambda e: e.get("time") or "99:99")

        parts = []
        for i, ev in enumerate(sorted_events, 1):
            time_str = f"{ev['time']} - " if ev.get("time") else ""
            parts.append(f"{i}. {time_str}{ev['description']}")

        return CommandResult(True,
            f"{len(self._events)} événement{'s' if len(self._events) > 1 else ''}: "
            + ", ".join(parts),
            data={"events": sorted_events})

    async def clear_events(self, command: VoiceCommand) -> CommandResult:
        """Vide l'agenda."""
        count = len(self._events)
        self._events.clear()
        return CommandResult(True,
            f"Agenda vidé. {count} événement{'s' if count > 1 else ''} supprimé{'s' if count > 1 else ''}.")

    async def next_event(self, command: VoiceCommand) -> CommandResult:
        """Donne le prochain evenement."""
        if not self._events:
            return CommandResult(True, "Aucun événement prévu.")

        now = datetime.now().strftime("%H:%M")
        timed = [e for e in self._events if e.get("time")]
        future = [e for e in timed if e["time"] > now]

        if future:
            future.sort(key=lambda e: e["time"])
            nxt = future[0]
            return CommandResult(True,
                f"Prochain événement à {nxt['time']}: {nxt['description']}.",
                data=nxt)

        if self._events:
            last = self._events[-1]
            return CommandResult(True,
                f"Dernier événement ajouté: {last['description']}.",
                data=last)

        return CommandResult(True, "Aucun événement prévu.")
