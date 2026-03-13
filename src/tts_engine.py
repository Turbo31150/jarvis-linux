#!/usr/bin/env python3
"""
Module TTS (Text-to-Speech) pour JARVIS.
Utilise espeak-ng pour synthèse vocale locale.
"""
import subprocess
import os
import logging

log = logging.getLogger("jarvis.tts")

MUTE = os.getenv("TTS_MUTE", "false").lower() == "true"
DEFAULT_LANG = os.getenv("TTS_LANG", "fr")
DEFAULT_SPEED = int(os.getenv("TTS_SPEED", "160"))


def speak(text: str, lang: str = None, mute: bool = None):
    """Lit un texte à haute voix via espeak-ng.

    Args:
        text: texte à lire
        lang: langue (fr, en, etc.)
        mute: si True, ne pas parler (override global)
    """
    if mute is None:
        mute = MUTE

    if mute:
        log.debug(f"[MUTE] {text}")
        return

    lang = lang or DEFAULT_LANG

    try:
        subprocess.run(
            ["espeak-ng", "-v", lang, "-s", str(DEFAULT_SPEED), text],
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError:
        log.error("espeak-ng non installé. sudo apt install espeak-ng")
    except subprocess.TimeoutExpired:
        log.warning("TTS timeout (>30s)")
    except Exception as e:
        log.error(f"Erreur TTS : {e}")


def speak_async(text: str, lang: str = None):
    """Version non-bloquante de speak()."""
    import threading
    t = threading.Thread(target=speak, args=(text, lang), daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    speak("Bonjour, je suis JARVIS. Système vocal opérationnel.")
