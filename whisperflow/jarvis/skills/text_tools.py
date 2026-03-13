"""
JARVIS Skill - Outils de manipulation de texte

Securite: operations string pures en memoire.
Aucun appel externe, aucune modification systeme.
"""

import logging
import re
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.text_tools")


def word_count(text: str) -> int:
    """Compte les mots dans un texte."""
    return len(text.split())


def char_count(text: str, spaces: bool = False) -> int:
    """Compte les caracteres."""
    if spaces:
        return len(text)
    return len(text.replace(" ", ""))


def to_uppercase(text: str) -> str:
    return text.upper()


def to_lowercase(text: str) -> str:
    return text.lower()


def to_title_case(text: str) -> str:
    return text.title()


def reverse_text(text: str) -> str:
    return text[::-1]


def make_acronym(text: str) -> str:
    """Cree un acronyme a partir des premieres lettres."""
    words = text.split()
    return "".join(w[0].upper() for w in words if w)


def remove_accents(text: str) -> str:
    """Retire les accents francais."""
    replacements = {
        "à": "a", "â": "a", "ä": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
        "À": "A", "Â": "A",
        "É": "E", "È": "E", "Ê": "E",
        "Î": "I", "Ô": "O",
        "Ù": "U", "Û": "U",
        "Ç": "C",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


class TextToolsSkill:

    async def count_words(self, command: VoiceCommand) -> CommandResult:
        """Compte les mots dans un texte."""
        text = command.target or ""
        if not text:
            return CommandResult(False, "Donnez-moi un texte à analyser.")

        words = word_count(text)
        chars = char_count(text, spaces=False)
        return CommandResult(True,
            f"{words} mots, {chars} caractères.",
            data={"words": words, "chars": chars})

    async def uppercase(self, command: VoiceCommand) -> CommandResult:
        """Convertit en majuscules."""
        text = command.target or ""
        if not text:
            return CommandResult(False, "Donnez-moi un texte.")
        result = to_uppercase(text)
        return CommandResult(True, result, data={"text": result})

    async def lowercase(self, command: VoiceCommand) -> CommandResult:
        """Convertit en minuscules."""
        text = command.target or ""
        if not text:
            return CommandResult(False, "Donnez-moi un texte.")
        result = to_lowercase(text)
        return CommandResult(True, result, data={"text": result})

    async def acronym(self, command: VoiceCommand) -> CommandResult:
        """Cree un acronyme."""
        text = command.target or ""
        if not text:
            return CommandResult(False, "Donnez-moi un texte.")
        result = make_acronym(text)
        return CommandResult(True,
            f"Acronyme: {result}",
            data={"acronym": result})

    async def spell(self, command: VoiceCommand) -> CommandResult:
        """Epelle un mot lettre par lettre."""
        text = command.target or ""
        if not text:
            return CommandResult(False, "Donnez-moi un mot à épeler.")
        letters = " - ".join(text.upper())
        return CommandResult(True, letters, data={"spelled": letters})
