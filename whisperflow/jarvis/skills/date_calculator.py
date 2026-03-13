"""
JARVIS Skill - Calculatrice de dates

Securite: calculs datetime purs en memoire.
Aucun appel externe, aucune modification systeme.
"""

import logging
import re
from datetime import datetime, timedelta
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.date_calculator")

_JOURS_FR = {
    0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
    4: "vendredi", 5: "samedi", 6: "dimanche"
}

_MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril",
    5: "mai", 6: "juin", 7: "juillet", 8: "août",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}


def format_date_fr(dt: datetime) -> str:
    """Formate une date en francais."""
    jour = _JOURS_FR[dt.weekday()]
    mois = _MOIS_FR[dt.month]
    return f"{jour} {dt.day} {mois} {dt.year}"


def days_between(date1: datetime, date2: datetime) -> int:
    """Nombre de jours entre deux dates."""
    return abs((date2 - date1).days)


def add_days(base: datetime, days: int) -> datetime:
    """Ajoute des jours a une date."""
    return base + timedelta(days=days)


def days_until_event(month: int, day: int, from_date: datetime = None) -> int:
    """Jours restants jusqu'a un evenement annuel."""
    now = from_date or datetime.now()
    target = datetime(now.year, month, day)
    if target < now:
        target = datetime(now.year + 1, month, day)
    return (target - now).days


def parse_date_fr(text: str) -> datetime:
    """Parse une date depuis du texte francais."""
    mois_map = {v: k for k, v in _MOIS_FR.items()}

    # Format "25 décembre" ou "25 decembre 2026"
    m = re.search(
        r'(\d{1,2})\s+(janvier|f[ée]vrier|mars|avril|mai|juin|'
        r'juillet|ao[uû]t|septembre|octobre|novembre|d[ée]cembre)'
        r'(?:\s+(\d{4}))?',
        text.lower()
    )
    if m:
        jour = int(m.group(1))
        mois_str = m.group(2).replace("é", "e").replace("û", "u")
        # Normalise accents pour lookup
        mois_norm = {k.replace("é", "e").replace("û", "u"): v
                     for k, v in mois_map.items()}
        mois = mois_norm.get(mois_str, 1)
        annee = int(m.group(3)) if m.group(3) else datetime.now().year
        return datetime(annee, mois, jour)

    # Format JJ/MM/AAAA
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
    if m:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    raise ValueError(f"Date non reconnue: {text}")


class DateCalculatorSkill:

    async def days_until(self, command: VoiceCommand) -> CommandResult:
        """Calcule le nombre de jours jusqu'a une date."""
        text = command.target or command.raw_text
        if not text:
            return CommandResult(False, "Donnez-moi une date.")

        # Cas speciaux
        text_lower = text.lower()
        now = datetime.now()
        special = {
            "noël": (12, 25), "noel": (12, 25),
            "nouvel an": (1, 1), "jour de l'an": (1, 1),
            "saint-valentin": (2, 14), "valentin": (2, 14),
            "halloween": (10, 31),
            "fête nationale": (7, 14), "14 juillet": (7, 14),
        }

        for key, (month, day) in special.items():
            if key in text_lower:
                days = days_until_event(month, day, now)
                event_date = add_days(now, days)
                return CommandResult(True,
                    f"{days} jours avant {key}. "
                    f"Ce sera un {format_date_fr(event_date)}.",
                    data={"days": days, "event": key})

        try:
            target = parse_date_fr(text)
            diff = (target - now).days
            if diff < 0:
                return CommandResult(True,
                    f"C'était il y a {abs(diff)} jours: "
                    f"{format_date_fr(target)}.")
            return CommandResult(True,
                f"{diff} jours restants. "
                f"Ce sera un {format_date_fr(target)}.",
                data={"days": diff})
        except ValueError as e:
            return CommandResult(False, str(e))

    async def add_days_cmd(self, command: VoiceCommand) -> CommandResult:
        """Ajoute des jours a la date actuelle."""
        text = command.target or command.raw_text or ""
        m = re.search(r'(\d+)\s*jours?', text.lower())
        if not m:
            # Fallback: target est juste un nombre (du pattern regex)
            m = re.search(r'(\d+)', text)
        if not m:
            return CommandResult(False, "Dites le nombre de jours à ajouter.")

        days = int(m.group(1))
        result = add_days(datetime.now(), days)
        return CommandResult(True,
            f"Dans {days} jours, nous serons le {format_date_fr(result)}.",
            data={"days": days, "date": result.isoformat()})

    async def day_of_week(self, command: VoiceCommand) -> CommandResult:
        """Donne le jour de la semaine pour une date."""
        text = command.target or command.raw_text
        if not text:
            return CommandResult(False, "Donnez-moi une date.")

        try:
            dt = parse_date_fr(text)
            return CommandResult(True,
                f"Le {dt.day} {_MOIS_FR[dt.month]} {dt.year} "
                f"est un {_JOURS_FR[dt.weekday()]}.",
                data={"day": _JOURS_FR[dt.weekday()]})
        except ValueError as e:
            return CommandResult(False, str(e))
