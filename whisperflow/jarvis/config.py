"""
JARVIS Configuration - Paramètres globaux du système vocal
"""

import os
import json
from pathlib import Path

JARVIS_DIR = Path(__file__).parent
CONFIG_FILE = JARVIS_DIR / "jarvis_config.json"

DEFAULT_CONFIG = {
    "wake_word": "jarvis",
    "language": "fr",
    "tts_voice": "fr-FR-DeniseNeural",
    "tts_rate": "+10%",
    "whisper_model": "tiny",
    "confidence_threshold": 0.6,
    "silence_timeout_ms": 1500,
    "command_timeout_ms": 5000,
    "audio": {
        "sample_rate": 16000,
        "channels": 1,
        "chunk_size": 1024,
        "format": "int16"
    },
    "shortcuts": {
        "explorateur": "explorer.exe",
        "navigateur": "start msedge",
        "chrome": "start chrome",
        "firefox": "start firefox",
        "bloc-notes": "notepad.exe",
        "notepad": "notepad.exe",
        "calculatrice": "calc.exe",
        "terminal": "wt.exe",
        "powershell": "powershell.exe",
        "cmd": "cmd.exe",
        "paramètres": "start ms-settings:",
        "musique": "start wmplayer",
        "paint": "mspaint.exe",
        "word": "start winword",
        "excel": "start excel",
        "powerpoint": "start powerpnt",
        "teams": "start msteams:",
        "discord": "start discord:",
        "code": "code",
        "vscode": "code",
        "gestionnaire": "taskmgr.exe",
        "snipping": "snippingtool.exe",
    },
    "web_shortcuts": {
        "google": "https://www.google.com/search?q=",
        "youtube": "https://www.youtube.com/results?search_query=",
        "wikipedia": "https://fr.wikipedia.org/wiki/",
        "github": "https://github.com/search?q=",
        "gmail": "https://mail.google.com",
        "drive": "https://drive.google.com",
        "notion": "https://www.notion.so",
    },
    "agents": {
        "dictation": {"enabled": True, "trigger": "mode dictée"},
        "search": {"enabled": True, "trigger": "recherche"},
        "automation": {"enabled": True, "trigger": "automatise"},
        "navigation": {"enabled": True, "trigger": "navigue"},
    }
}


class JarvisConfig:
    def __init__(self):
        self._config = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                self._deep_merge(self._config, user_config)
            except (json.JSONDecodeError, IOError):
                pass

    def _deep_merge(self, base, override):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        keys = key.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def set(self, key, value):
        keys = key.split(".")
        d = self._config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save()


config = JarvisConfig()
