"""
JARVIS Skill - Gestionnaire de fichiers Windows
Créer, supprimer, chercher, renommer des fichiers et dossiers

Sécurité: Les noms de fichiers sont sanitizés. La suppression utilise
la corbeille Windows (récupérable). Seuls les dossiers utilisateur sont accessibles.
"""

import logging
from pathlib import Path
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.file")

SEARCH_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Music",
    Path.home() / "Videos",
]

SAFE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
                 "0123456789 .-_àâéèêëïîôùûüçÀÂÉÈÊËÏÎÔÙÛÜÇ")


def _sanitize_name(name: str) -> str:
    return "".join(c for c in name if c in SAFE_CHARS).strip()


class FileManagerSkill:
    """Skill de gestion de fichiers"""

    async def create(self, command: VoiceCommand) -> CommandResult:
        """Crée un fichier ou dossier sur le bureau"""
        name = command.target.strip()
        if not name:
            return CommandResult(False, "Donnez un nom pour le fichier ou dossier")

        safe_name = _sanitize_name(name)
        if not safe_name:
            return CommandResult(False, "Nom de fichier invalide")

        desktop = Path.home() / "Desktop"
        raw = command.raw_text.lower()

        if any(w in raw for w in ("dossier", "répertoire", "folder")):
            path = desktop / safe_name
            path.mkdir(parents=True, exist_ok=True)
            return CommandResult(True, f"Dossier '{safe_name}' créé sur le bureau")
        else:
            if "." not in safe_name:
                safe_name += ".txt"
            path = desktop / safe_name
            path.touch()
            return CommandResult(True, f"Fichier '{safe_name}' créé sur le bureau")

    async def delete(self, command: VoiceCommand) -> CommandResult:
        """Met un fichier à la corbeille Windows (récupérable)"""
        name = command.target.strip()
        if not name:
            return CommandResult(False, "Quel fichier ou dossier supprimer ?")

        found = self._find_file(name)
        if not found:
            return CommandResult(False, f"Fichier '{name}' introuvable")

        try:
            from send2trash import send2trash
            send2trash(str(found))
            return CommandResult(True, f"'{found.name}' envoyé à la corbeille")
        except ImportError:
            # Fallback: rename to .trash suffix instead of permanent delete
            trash_path = found.with_suffix(found.suffix + ".trash")
            try:
                found.rename(trash_path)
                return CommandResult(
                    True,
                    f"'{found.name}' renommé en .trash (installez send2trash pour corbeille)"
                )
            except Exception as e:
                return CommandResult(False, f"Impossible de supprimer '{found.name}': {e}")

    async def search(self, command: VoiceCommand) -> CommandResult:
        """Recherche un fichier dans les répertoires utilisateur"""
        query = command.target.strip().lower()
        if not query:
            return CommandResult(False, "Que cherchez-vous ?")

        results = []
        for search_dir in SEARCH_DIRS:
            if not search_dir.exists():
                continue
            try:
                for item in search_dir.rglob("*"):
                    if query in item.name.lower():
                        results.append(item)
                        if len(results) >= 10:
                            break
            except (PermissionError, OSError):
                continue
            if len(results) >= 10:
                break

        if results:
            names = [f"- {r.name} ({r.parent.name}/)" for r in results[:5]]
            msg = f"J'ai trouvé {len(results)} résultats:\n" + "\n".join(names)
            return CommandResult(True, msg, data={"files": [str(r) for r in results]})

        return CommandResult(False, f"Aucun fichier trouvé pour '{query}'")

    async def rename(self, command: VoiceCommand) -> CommandResult:
        """Renomme un fichier"""
        groups = command.params.get("groups", ())
        if len(groups) < 2:
            return CommandResult(False, "Syntaxe: renomme [ancien] en [nouveau]")

        old_name = groups[0].strip()
        new_name = _sanitize_name(groups[1].strip())

        if not new_name:
            return CommandResult(False, "Nouveau nom invalide")

        found = self._find_file(old_name)
        if not found:
            return CommandResult(False, f"Fichier '{old_name}' introuvable")

        new_path = found.parent / new_name
        try:
            found.rename(new_path)
            return CommandResult(True, f"Renommé: '{found.name}' -> '{new_name}'")
        except Exception as e:
            return CommandResult(False, f"Erreur renommage: {e}")

    def _find_file(self, name: str) -> Path | None:
        """Cherche un fichier par nom dans les répertoires connus"""
        name_lower = name.lower()
        for search_dir in SEARCH_DIRS:
            if not search_dir.exists():
                continue
            try:
                for item in search_dir.rglob("*"):
                    if name_lower in item.name.lower():
                        return item
            except (PermissionError, OSError):
                continue
        return None
