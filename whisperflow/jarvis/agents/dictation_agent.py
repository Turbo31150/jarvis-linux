"""
JARVIS Agent - Dictée vocale
Mode dictée: tout ce que vous dites est tapé au clavier

Sécurité: Le texte dicté est échappé via _escape_sendkeys() avant passage
à SendKeys, empêchant l'injection de commandes. Les touches spéciales
utilisent des scripts PowerShell statiques constants.
"""

import asyncio
import logging
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.agents.dictation")

# Scripts 100% statiques pour les touches spéciales
_STATIC_KEYS = {
    "enter": "$w = New-Object -ComObject WScript.Shell; $w.SendKeys('{ENTER}')",
    "tab": "$w = New-Object -ComObject WScript.Shell; $w.SendKeys('{TAB}')",
    "backspace": "$w = New-Object -ComObject WScript.Shell; $w.SendKeys('{BACKSPACE}')",
    "period": "$w = New-Object -ComObject WScript.Shell; $w.SendKeys('.')",
}

VOICE_PUNCTUATION = {
    "point": ".", "virgule": ",", "point d'exclamation": "!",
    "point d'interrogation": "?", "deux points": ":", "point-virgule": ";",
    "tiret": "-", "ouvrez la parenthèse": "(", "fermez la parenthèse": ")",
    "ouvrez les guillemets": '"', "fermez les guillemets": '"',
    "apostrophe": "'", "arobase": "@",
}

STOP_COMMANDS = frozenset({
    "arrête la dictée", "stop dictation", "fin de dictée",
    "arrête d'écrire", "mode normal", "quitte la dictée",
})

# Caractères spéciaux SendKeys qui doivent être échappés
_SENDKEYS_SPECIAL = {
    "+": "{+}", "^": "{^}", "%": "{%}", "~": "{~}",
    "(": "{(}", ")": "{)}", "{": "{{}", "}": "{}}",
    "[": "{[}", "]": "{]}",
}


def _escape_sendkeys(text: str) -> str:
    """Échappe les caractères spéciaux pour SendKeys - prévient l'injection"""
    return "".join(_SENDKEYS_SPECIAL.get(ch, ch) for ch in text)


async def _run_ps_static(name: str):
    """Exécute un script PowerShell statique par nom"""
    script = _STATIC_KEYS.get(name)
    if not script:
        return
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()


async def _type_text(text: str):
    """Tape du texte via SendKeys avec échappement de sécurité"""
    escaped = _escape_sendkeys(text)
    # Le texte est échappé, seuls des caractères littéraux passent
    script = f"$w = New-Object -ComObject WScript.Shell; $w.SendKeys('{escaped}')"
    proc = await asyncio.create_subprocess_exec(
        "powershell", "-NoProfile", "-Command", script,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()


class DictationAgent:
    """Agent de dictée vocale - tape tout ce que vous dites"""

    def __init__(self):
        self.active = False
        self._capitalize_next = True

    async def start(self, command: VoiceCommand) -> CommandResult:
        self.active = True
        self._capitalize_next = True
        return CommandResult(True, "dictation_on")

    async def stop(self, command: VoiceCommand) -> CommandResult:
        self.active = False
        return CommandResult(True, "dictation_off")

    def should_stop(self, text: str) -> bool:
        return text.strip().lower() in STOP_COMMANDS

    async def process_text(self, text: str) -> CommandResult:
        """Traite et tape le texte dicté"""
        if not self.active:
            return CommandResult(False, "Mode dictée inactif")

        if self.should_stop(text):
            return await self.stop(VoiceCommand(text, "dictation_stop"))

        processed = text.strip()

        # Remplacement ponctuation vocale
        for voice_cmd, replacement in VOICE_PUNCTUATION.items():
            if processed.lower() == voice_cmd:
                processed = replacement
                break

        # Commandes de formatage
        lower = processed.lower()
        if lower in ("nouvelle ligne", "à la ligne"):
            await _run_ps_static("enter")
            self._capitalize_next = True
            return CommandResult(True, "")
        if lower == "tabulation":
            await _run_ps_static("tab")
            return CommandResult(True, "")
        if lower in ("efface", "supprime", "backspace"):
            await _run_ps_static("backspace")
            return CommandResult(True, "")

        # Capitalisation auto
        if self._capitalize_next and processed and processed[0].isalpha():
            processed = processed[0].upper() + processed[1:]
            self._capitalize_next = False

        if processed and processed[-1] in ".!?":
            self._capitalize_next = True
            processed += " "
        elif processed and processed[-1] not in ".,;:!?-":
            processed += " "

        await _type_text(processed)
        return CommandResult(True, "")

    async def newline(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static("enter")
        self._capitalize_next = True
        return CommandResult(True, "")

    async def period(self, command: VoiceCommand) -> CommandResult:
        await _run_ps_static("period")
        self._capitalize_next = True
        return CommandResult(True, "")
