"""
JARVIS Agent - Automatisation et macros vocales
Enregistre et rejoue des séquences de commandes
"""

import json
import logging
from pathlib import Path
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.agents.automation")

MACROS_FILE = Path.home() / ".jarvis" / "macros.json"


class AutomationAgent:
    """Agent d'automatisation - macros et séquences de commandes"""

    def __init__(self):
        self.macros: dict[str, list[str]] = {}
        self.recording = False
        self.current_macro_name = ""
        self.current_macro_steps: list[str] = []
        self._load_macros()

    def _load_macros(self):
        if MACROS_FILE.exists():
            try:
                with open(MACROS_FILE, "r", encoding="utf-8") as f:
                    self.macros = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.macros = {}

    def _save_macros(self):
        MACROS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MACROS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.macros, f, indent=2, ensure_ascii=False)

    async def create(self, command: VoiceCommand) -> CommandResult:
        """Commence l'enregistrement d'une macro"""
        name = command.target.strip().lower()
        if not name:
            return CommandResult(False, "Donnez un nom à la macro")

        self.recording = True
        self.current_macro_name = name
        self.current_macro_steps = []
        return CommandResult(
            True,
            f"Enregistrement de la macro '{name}'. "
            f"Dites vos commandes puis 'fin de macro' pour terminer."
        )

    async def stop_recording(self) -> CommandResult:
        """Arrête l'enregistrement et sauvegarde la macro"""
        if not self.recording:
            return CommandResult(False, "Aucun enregistrement en cours")

        name = self.current_macro_name
        self.macros[name] = self.current_macro_steps
        self._save_macros()

        self.recording = False
        steps = len(self.current_macro_steps)
        self.current_macro_steps = []
        self.current_macro_name = ""

        return CommandResult(True, f"Macro '{name}' sauvegardée avec {steps} étapes")

    def record_step(self, text: str):
        """Enregistre une étape pendant l'enregistrement"""
        if self.recording:
            self.current_macro_steps.append(text)

    async def run(self, command: VoiceCommand) -> CommandResult:
        """Exécute une macro sauvegardée"""
        name = command.target.strip().lower()
        steps = self.macros.get(name)

        if not steps:
            available = ", ".join(self.macros.keys()) if self.macros else "aucune"
            return CommandResult(
                False,
                f"Macro '{name}' introuvable. Disponibles: {available}"
            )

        return CommandResult(
            True,
            f"Exécution de la macro '{name}' ({len(steps)} étapes)",
            data={"macro_steps": steps}
        )

    async def list_macros(self, command: VoiceCommand) -> CommandResult:
        """Liste toutes les macros disponibles"""
        if not self.macros:
            return CommandResult(True, "Aucune macro enregistrée")

        lines = [f"- {name} ({len(steps)} étapes)"
                 for name, steps in self.macros.items()]
        return CommandResult(True, "Macros disponibles:\n" + "\n".join(lines))

    async def delete_macro(self, name: str) -> CommandResult:
        """Supprime une macro"""
        if name in self.macros:
            del self.macros[name]
            self._save_macros()
            return CommandResult(True, f"Macro '{name}' supprimée")
        return CommandResult(False, f"Macro '{name}' introuvable")
