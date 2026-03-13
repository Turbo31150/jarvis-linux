"""
JARVIS Wake Word Detection - Détection du mot d'activation "Jarvis"
"""

import re
import logging
from difflib import SequenceMatcher

logger = logging.getLogger("jarvis.wake")

WAKE_VARIANTS = [
    "jarvis", "jarvi", "jarviss", "djarvis", "charvis",
    "jarves", "jarvice", "jarvis,", "hey jarvis",
    "ok jarvis", "dis jarvis", "dit jarvis",
]


def detect_wake_word(text: str, wake_word: str = "jarvis", threshold: float = 0.75) -> tuple:
    """
    Détecte le mot d'activation dans le texte transcrit.

    Returns:
        (detected: bool, command_text: str) - True si wake word trouvé + texte restant
    """
    if not text:
        return False, ""

    text_lower = text.lower().strip()

    # Correspondance exacte au début
    for variant in WAKE_VARIANTS:
        if text_lower.startswith(variant):
            remainder = text_lower[len(variant):].strip().lstrip(",").lstrip(".").strip()
            logger.info(f"Wake word détecté (exact): '{variant}' -> commande: '{remainder}'")
            return True, remainder

    # Correspondance floue du premier mot
    words = text_lower.split()
    if words:
        first_word = words[0].rstrip(".,!?")
        similarity = SequenceMatcher(None, first_word, wake_word).ratio()
        if similarity >= threshold:
            remainder = " ".join(words[1:]).strip()
            logger.info(f"Wake word détecté (fuzzy {similarity:.2f}): '{first_word}' -> '{remainder}'")
            return True, remainder

    return False, ""


def strip_wake_word(text: str) -> str:
    """Retire le wake word du texte s'il est présent"""
    detected, remainder = detect_wake_word(text)
    return remainder if detected else text
