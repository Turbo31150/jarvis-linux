"""
JARVIS Skill - Traducteur vocal FR/EN

Securite: dictionnaire statique en memoire.
Aucun appel API externe, aucune entree dans les commandes systeme.
"""

import logging
import re
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.translator")

# Dictionnaire bidirectionnel FR <-> EN (mots/phrases courants)
_FR_TO_EN = {
    "bonjour": "hello", "bonsoir": "good evening", "au revoir": "goodbye",
    "merci": "thank you", "s'il vous plaît": "please", "oui": "yes",
    "non": "no", "comment allez-vous": "how are you",
    "je ne comprends pas": "I don't understand",
    "excusez-moi": "excuse me", "pardon": "sorry",
    "combien": "how much", "où": "where", "quand": "when",
    "pourquoi": "why", "comment": "how", "qui": "who",
    "aujourd'hui": "today", "demain": "tomorrow", "hier": "yesterday",
    "matin": "morning", "après-midi": "afternoon", "soir": "evening",
    "nuit": "night", "semaine": "week", "mois": "month", "année": "year",
    "lundi": "monday", "mardi": "tuesday", "mercredi": "wednesday",
    "jeudi": "thursday", "vendredi": "friday", "samedi": "saturday",
    "dimanche": "sunday",
    "rouge": "red", "bleu": "blue", "vert": "green", "jaune": "yellow",
    "noir": "black", "blanc": "white", "gris": "gray",
    "ordinateur": "computer", "écran": "screen", "clavier": "keyboard",
    "souris": "mouse", "fichier": "file", "dossier": "folder",
    "rechercher": "search", "ouvrir": "open", "fermer": "close",
    "sauvegarder": "save", "copier": "copy", "coller": "paste",
    "supprimer": "delete", "annuler": "cancel", "confirmer": "confirm",
    "eau": "water", "pain": "bread", "maison": "house", "école": "school",
    "travail": "work", "temps": "time", "bien": "good", "mal": "bad",
    "grand": "big", "petit": "small", "nouveau": "new", "vieux": "old",
}

# Inverse: EN -> FR
_EN_TO_FR = {v: k for k, v in _FR_TO_EN.items()}


def _translate_word(word: str, direction: str) -> str:
    """Traduit un mot/phrase. direction: 'fr_en' ou 'en_fr'"""
    w = word.lower().strip()
    if direction == "fr_en":
        return _FR_TO_EN.get(w, "")
    return _EN_TO_FR.get(w, "")


def _translate_text(text: str, direction: str) -> str:
    """Essaie de traduire le texte mot par mot."""
    source = _FR_TO_EN if direction == "fr_en" else _EN_TO_FR
    words = text.lower().strip().split()
    result = []

    i = 0
    while i < len(words):
        found = False
        # Essaye des groupes de mots (3, 2, 1)
        for length in range(min(3, len(words) - i), 0, -1):
            phrase = " ".join(words[i:i + length])
            if phrase in source:
                result.append(source[phrase])
                i += length
                found = True
                break
        if not found:
            result.append(words[i])
            i += 1

    return " ".join(result)


class TranslatorSkill:

    async def translate_fr_en(self, command: VoiceCommand) -> CommandResult:
        """Traduit du francais vers l'anglais."""
        text = command.target or command.raw_text
        if not text or not text.strip():
            return CommandResult(False, "Rien à traduire")

        # Nettoyer le prefixe "en anglais"
        clean = re.sub(r'^(?:en\s+anglais\s+)', '', text.strip(), flags=re.IGNORECASE)
        if not clean:
            clean = text.strip()

        result = _translate_text(clean, "fr_en")
        if result == clean.lower():
            return CommandResult(False, f"Je ne connais pas la traduction de '{clean}'")

        return CommandResult(True, f"En anglais: {result}",
                             data={"source": clean, "translation": result, "direction": "fr_en"})

    async def translate_en_fr(self, command: VoiceCommand) -> CommandResult:
        """Traduit de l'anglais vers le francais."""
        text = command.target or command.raw_text
        if not text or not text.strip():
            return CommandResult(False, "Nothing to translate")

        clean = re.sub(r'^(?:en\s+fran[çc]ais\s+)', '', text.strip(), flags=re.IGNORECASE)
        if not clean:
            clean = text.strip()

        result = _translate_text(clean, "en_fr")
        if result == clean.lower():
            return CommandResult(False, f"I don't know the translation of '{clean}'")

        return CommandResult(True, f"En français: {result}",
                             data={"source": clean, "translation": result, "direction": "en_fr"})

    async def lookup(self, command: VoiceCommand) -> CommandResult:
        """Cherche la traduction d'un mot dans les deux sens."""
        text = (command.target or command.raw_text or "").lower().strip()
        if not text:
            return CommandResult(False, "Quel mot traduire?")

        if text in _FR_TO_EN:
            return CommandResult(True, f"{text} = {_FR_TO_EN[text]} (EN)")
        if text in _EN_TO_FR:
            return CommandResult(True, f"{text} = {_EN_TO_FR[text]} (FR)")

        return CommandResult(False, f"Mot inconnu: '{text}'")
