"""
JARVIS Agent - Navigation système Windows
Navigue dans les menus, paramètres, et interface Windows

Sécurité: Utilise uniquement des URIs ms-settings: prédéfinies et des
dossiers shell: Windows constants. Aucune entrée utilisateur dans les commandes.
explorer.exe est appelé avec des arguments shell: constants uniquement.
"""

import asyncio
import logging
import webbrowser
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.agents.navigation")

# URIs ms-settings: prédéfinies (constantes système Windows)
SETTINGS_MAP = {
    "wifi": "ms-settings:network-wifi",
    "réseau": "ms-settings:network-status",
    "bluetooth": "ms-settings:bluetooth",
    "affichage": "ms-settings:display",
    "écran": "ms-settings:display",
    "son": "ms-settings:sound",
    "audio": "ms-settings:sound",
    "notifications": "ms-settings:notifications",
    "batterie": "ms-settings:batterysaver",
    "stockage": "ms-settings:storagesense",
    "applications": "ms-settings:appsfeatures",
    "apps": "ms-settings:appsfeatures",
    "comptes": "ms-settings:accounts",
    "heure": "ms-settings:dateandtime",
    "date": "ms-settings:dateandtime",
    "langue": "ms-settings:regionlanguage",
    "clavier": "ms-settings:typing",
    "souris": "ms-settings:mousetouchpad",
    "imprimante": "ms-settings:printers",
    "mise à jour": "ms-settings:windowsupdate",
    "update": "ms-settings:windowsupdate",
    "sécurité": "ms-settings:windowsdefender",
    "confidentialité": "ms-settings:privacy",
    "personnalisation": "ms-settings:personalization",
    "fond d'écran": "ms-settings:personalization-background",
    "thème": "ms-settings:themes",
    "couleurs": "ms-settings:colors",
    "écran de verrouillage": "ms-settings:lockscreen",
    "démarrage": "ms-settings:startupapps",
    "accessibilité": "ms-settings:easeofaccess",
    "vpn": "ms-settings:network-vpn",
    "proxy": "ms-settings:network-proxy",
}

# Dossiers shell: système (constantes Windows)
SHELL_FOLDERS = {
    "téléchargements": "shell:Downloads",
    "downloads": "shell:Downloads",
    "documents": "shell:Personal",
    "bureau": "shell:Desktop",
    "images": "shell:My Pictures",
    "photos": "shell:My Pictures",
    "musique": "shell:My Music",
    "vidéos": "shell:My Video",
    "programme": "shell:ProgramFiles",
    "corbeille": "shell:RecycleBinFolder",
    "favoris": "shell:Favorites",
    "récent": "shell:Recent",
}


async def _open_shell_folder(shell_uri: str):
    """Ouvre un dossier shell: constant via explorer.exe"""
    proc = await asyncio.create_subprocess_exec(
        "explorer.exe", shell_uri,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await asyncio.sleep(0.5)


class NavigationAgent:
    """Agent de navigation système Windows"""

    async def navigate(self, command: VoiceCommand) -> CommandResult:
        """Navigue vers un paramètre ou dossier système"""
        target = command.target.strip().lower()
        if not target:
            return CommandResult(False, "Où voulez-vous naviguer ?")

        # 1. Paramètres Windows (URIs prédéfinies)
        settings_uri = SETTINGS_MAP.get(target)
        if settings_uri:
            webbrowser.open(settings_uri)
            return CommandResult(True, f"Ouverture des paramètres: {target}")

        # 2. Dossiers système (shell: constants)
        shell_folder = SHELL_FOLDERS.get(target)
        if shell_folder:
            await _open_shell_folder(shell_folder)
            return CommandResult(True, f"Ouverture du dossier: {target}")

        # 3. Recherche partielle dans les constantes
        for key, uri in SETTINGS_MAP.items():
            if key in target or target in key:
                webbrowser.open(uri)
                return CommandResult(True, f"Ouverture des paramètres: {key}")

        for key, folder in SHELL_FOLDERS.items():
            if key in target or target in key:
                await _open_shell_folder(folder)
                return CommandResult(True, f"Ouverture du dossier: {key}")

        return CommandResult(
            False,
            f"Destination '{target}' non reconnue. "
            f"Essayez: {', '.join(list(SETTINGS_MAP.keys())[:10])}..."
        )

    async def open_settings(self, command: VoiceCommand) -> CommandResult:
        webbrowser.open("ms-settings:")
        return CommandResult(True, "Paramètres Windows ouverts")

    async def list_destinations(self, command: VoiceCommand) -> CommandResult:
        settings = ", ".join(sorted(SETTINGS_MAP.keys()))
        folders = ", ".join(sorted(SHELL_FOLDERS.keys()))
        return CommandResult(True, f"Paramètres: {settings}\nDossiers: {folders}")
