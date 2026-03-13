"""
JARVIS Skill - Commandes favorites

Securite: stockage en memoire uniquement (list de dicts).
Aucun acces fichier, aucun appel externe.
"""

import logging
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.favorites")

_MAX_FAVORITES = 20


class FavoritesSkill:

    def __init__(self):
        self._favorites: list[dict] = []

    @property
    def count(self) -> int:
        return len(self._favorites)

    def get_all(self) -> list[dict]:
        """Retourne toutes les commandes favorites."""
        return list(self._favorites)

    async def add(self, command: VoiceCommand) -> CommandResult:
        """Ajoute une commande aux favoris."""
        text = command.target or ""
        if not text:
            return CommandResult(False,
                "Dites la commande à ajouter en favori.")

        # Verifie doublon
        for fav in self._favorites:
            if fav["command"] == text:
                return CommandResult(False,
                    f"'{text}' est déjà dans vos favoris.")

        if len(self._favorites) >= _MAX_FAVORITES:
            return CommandResult(False,
                f"Maximum {_MAX_FAVORITES} favoris atteint. "
                f"Supprimez-en un d'abord.")

        self._favorites.append({
            "command": text,
            "index": len(self._favorites) + 1,
        })

        return CommandResult(True,
            f"'{text}' ajouté aux favoris. "
            f"{len(self._favorites)} favori{'s' if len(self._favorites) > 1 else ''}.",
            data={"command": text, "count": len(self._favorites)})

    async def list_favorites(self, command: VoiceCommand) -> CommandResult:
        """Liste les commandes favorites."""
        if not self._favorites:
            return CommandResult(True,
                "Aucun favori. Dites 'ajoute en favori' suivi d'une commande.")

        parts = [f"{i+1}. {f['command']}"
                 for i, f in enumerate(self._favorites)]
        return CommandResult(True,
            f"{len(self._favorites)} favoris: " + ", ".join(parts),
            data={"favorites": self._favorites})

    async def remove(self, command: VoiceCommand) -> CommandResult:
        """Supprime un favori par nom ou numero."""
        text = command.target or ""
        if not text:
            return CommandResult(False,
                "Dites le numéro ou le nom du favori à supprimer.")

        # Par numero
        try:
            idx = int(text) - 1
            if 0 <= idx < len(self._favorites):
                removed = self._favorites.pop(idx)
                return CommandResult(True,
                    f"Favori '{removed['command']}' supprimé.")
        except ValueError:
            pass

        # Par nom
        for i, fav in enumerate(self._favorites):
            if text.lower() in fav["command"].lower():
                removed = self._favorites.pop(i)
                return CommandResult(True,
                    f"Favori '{removed['command']}' supprimé.")

        return CommandResult(False, f"Favori '{text}' non trouvé.")

    async def run_favorite(self, command: VoiceCommand) -> CommandResult:
        """Execute un favori par numero."""
        text = command.target or ""
        try:
            idx = int(text) - 1
        except ValueError:
            # Cherche par nom
            for fav in self._favorites:
                if text.lower() in fav["command"].lower():
                    return CommandResult(True,
                        fav["command"],
                        data={"run_command": fav["command"]})
            return CommandResult(False, "Favori non trouvé.")

        if 0 <= idx < len(self._favorites):
            fav = self._favorites[idx]
            return CommandResult(True,
                fav["command"],
                data={"run_command": fav["command"]})

        return CommandResult(False,
            f"Numéro invalide. Vous avez {len(self._favorites)} favoris.")
