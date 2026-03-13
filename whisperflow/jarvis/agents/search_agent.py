"""
JARVIS Agent - Recherche locale et web
Cherche des fichiers, applications, et sur le web

Sécurité: Les recherches locales utilisent pathlib (pas de shell).
Les recherches web passent par webbrowser.open avec URL encodée.
La recherche d'apps utilise un script PowerShell statique prédéfini.
"""

import asyncio
import json
import logging
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.agents.search")

# Script PS statique - liste toutes les apps, pas d'input utilisateur
PS_LIST_APPS = "Get-StartApps | Select-Object -Property Name | ConvertTo-Json"


class SearchAgent:
    """Agent de recherche multi-sources"""

    def __init__(self):
        self.search_dirs = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
        ]

    async def search(self, command: VoiceCommand) -> CommandResult:
        """Recherche intelligente: local d'abord, puis web"""
        query = command.target.strip()
        if not query:
            return CommandResult(False, "Que cherchez-vous ?")

        local_results = self._search_local(query)
        if local_results:
            names = [f"- {r.name}" for r in local_results[:5]]
            msg = "Trouvé localement:\n" + "\n".join(names)
            return CommandResult(True, msg, data={"files": [str(r) for r in local_results]})

        url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
        return CommandResult(True, f"Rien trouvé localement. Recherche web: {query}")

    def _search_local(self, query: str) -> list:
        """Recherche dans les dossiers utilisateur via pathlib"""
        query_lower = query.lower()
        results = []
        for search_dir in self.search_dirs:
            if not search_dir.exists():
                continue
            try:
                for item in search_dir.rglob("*"):
                    if query_lower in item.name.lower():
                        results.append(item)
                        if len(results) >= 10:
                            return results
            except (PermissionError, OSError):
                continue
        return results

    async def search_apps(self, query: str) -> CommandResult:
        """Recherche dans les applications installées"""
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-NoProfile", "-Command", PS_LIST_APPS,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()

        try:
            apps = json.loads(stdout.decode("utf-8", errors="replace"))
            if isinstance(apps, dict):
                apps = [apps]
            query_lower = query.lower()
            matches = [a["Name"] for a in apps
                       if query_lower in a.get("Name", "").lower()]
            if matches:
                return CommandResult(
                    True, f"Applications trouvées: {', '.join(matches[:5])}"
                )
        except (json.JSONDecodeError, KeyError):
            pass

        return CommandResult(False, f"Aucune application '{query}' trouvée")
