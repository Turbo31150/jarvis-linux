"""
JARVIS Skills - Compétences de contrôle Windows
"""

from .app_launcher import AppLauncherSkill
from .system_control import SystemControlSkill
from .window_manager import WindowManagerSkill
from .file_manager import FileManagerSkill
from .web_browser import WebBrowserSkill
from .media_control import MediaControlSkill
from .clipboard_manager import ClipboardManagerSkill

__all__ = [
    "AppLauncherSkill",
    "SystemControlSkill",
    "WindowManagerSkill",
    "FileManagerSkill",
    "WebBrowserSkill",
    "MediaControlSkill",
    "ClipboardManagerSkill",
]
