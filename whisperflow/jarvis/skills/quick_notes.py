"""
JARVIS Skill - Notes vocales rapides

Sécurité: écrit uniquement dans ~/.jarvis/notes.txt.
Noms de fichier non-configurables, pas d'entrée utilisateur dans les chemins.
"""

import logging
from datetime import datetime
from pathlib import Path
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.notes")

NOTES_DIR = Path.home() / ".jarvis"
NOTES_FILE = NOTES_DIR / "notes.txt"


class QuickNotesSkill:

    def __init__(self):
        NOTES_DIR.mkdir(exist_ok=True)

    async def add_note(self, command: VoiceCommand) -> CommandResult:
        """Ajoute une note rapide avec horodatage."""
        text = command.target.strip() if command.target else ""
        if not text:
            return CommandResult(False, "Rien à noter")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"[{timestamp}] {text}\n"

        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(entry)

        word_count = len(text.split())
        return CommandResult(True, f"Note enregistrée: {word_count} mots")

    async def read_notes(self, command: VoiceCommand) -> CommandResult:
        """Lit les dernières notes."""
        if not NOTES_FILE.exists():
            return CommandResult(True, "Aucune note enregistrée")

        content = NOTES_FILE.read_text(encoding="utf-8").strip()
        if not content:
            return CommandResult(True, "Aucune note enregistrée")

        lines = content.split("\n")
        last_5 = lines[-5:]
        result = ". ".join(last_5)
        return CommandResult(True, f"{len(lines)} notes. Dernières: {result[:500]}")

    async def clear_notes(self, command: VoiceCommand) -> CommandResult:
        """Efface toutes les notes."""
        if NOTES_FILE.exists():
            count = len(NOTES_FILE.read_text(encoding="utf-8").strip().split("\n"))
            NOTES_FILE.write_text("", encoding="utf-8")
            return CommandResult(True, f"{count} notes effacées")
        return CommandResult(True, "Aucune note à effacer")

    async def search_notes(self, command: VoiceCommand) -> CommandResult:
        """Cherche dans les notes."""
        query = command.target.strip().lower() if command.target else ""
        if not query:
            return CommandResult(False, "Que chercher?")
        if not NOTES_FILE.exists():
            return CommandResult(True, "Aucune note enregistrée")

        content = NOTES_FILE.read_text(encoding="utf-8").strip()
        matches = [l for l in content.split("\n") if query in l.lower()]
        if matches:
            return CommandResult(True, f"{len(matches)} résultat{'s' if len(matches) > 1 else ''}: {'. '.join(matches[-3:])[:500]}")
        return CommandResult(True, f"Aucune note contenant '{query}'")

    @property
    def notes_count(self) -> int:
        if not NOTES_FILE.exists():
            return 0
        content = NOTES_FILE.read_text(encoding="utf-8").strip()
        return len(content.split("\n")) if content else 0
