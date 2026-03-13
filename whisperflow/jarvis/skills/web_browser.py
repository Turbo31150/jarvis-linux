"""
JARVIS Skill - Navigation web
Recherches Google, YouTube, Wikipedia, navigation par URL
"""

import asyncio
import logging
import webbrowser
from urllib.parse import quote_plus
from ..commander import VoiceCommand, CommandResult
from ..config import config

logger = logging.getLogger("jarvis.skills.web")


class WebBrowserSkill:
    """Skill de navigation web"""

    def __init__(self):
        self.web_shortcuts = config.get("web_shortcuts", {})

    async def google(self, command: VoiceCommand) -> CommandResult:
        """Recherche Google"""
        query = command.target.strip()
        if not query:
            return CommandResult(False, "Que voulez-vous chercher ?")
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        webbrowser.open(url)
        return CommandResult(True, f"Recherche Google: {query}")

    async def youtube(self, command: VoiceCommand) -> CommandResult:
        """Recherche YouTube"""
        query = command.target.strip()
        if not query:
            return CommandResult(False, "Que cherchez-vous sur YouTube ?")
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        webbrowser.open(url)
        return CommandResult(True, f"Recherche YouTube: {query}")

    async def wikipedia(self, command: VoiceCommand) -> CommandResult:
        """Recherche Wikipedia"""
        query = command.target.strip()
        if not query:
            return CommandResult(False, "Quel sujet sur Wikipédia ?")
        url = f"https://fr.wikipedia.org/wiki/{quote_plus(query)}"
        webbrowser.open(url)
        return CommandResult(True, f"Recherche Wikipedia: {query}")

    async def navigate(self, command: VoiceCommand) -> CommandResult:
        """Navigue vers un site ou un raccourci web"""
        target = command.target.strip().lower()
        if not target:
            return CommandResult(False, "Quel site ouvrir ?")

        # Vérifie les raccourcis configurés
        shortcut_url = self.web_shortcuts.get(target)
        if shortcut_url:
            webbrowser.open(shortcut_url)
            return CommandResult(True, f"Ouverture de {target}")

        # Construit l'URL si nécessaire
        if not target.startswith(("http://", "https://")):
            if "." in target:
                target = f"https://{target}"
            else:
                target = f"https://www.google.com/search?q={quote_plus(target)}"

        webbrowser.open(target)
        return CommandResult(True, f"Navigation vers {target}")

    async def weather(self, command: VoiceCommand) -> CommandResult:
        """Affiche la météo"""
        webbrowser.open("https://www.google.com/search?q=météo")
        return CommandResult(True, "Ouverture de la météo")
