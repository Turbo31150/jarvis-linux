"""
JARVIS Skill - Choix aleatoire vocal

Securite: utilise secrets pour aleatoire cryptographique.
Aucun appel externe, aucune modification systeme.
"""

import logging
import secrets
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.random_picker")


def coin_flip() -> str:
    """Pile ou face."""
    return secrets.choice(["pile", "face"])


def dice_roll(sides: int = 6) -> int:
    """Lance un de."""
    return secrets.randbelow(sides) + 1


def pick_from_list(items: list) -> str:
    """Choisit un element aleatoire."""
    if not items:
        return ""
    return secrets.choice(items)


def random_number(min_val: int, max_val: int) -> int:
    """Nombre aleatoire entre min et max inclus."""
    if min_val > max_val:
        min_val, max_val = max_val, min_val
    return min_val + secrets.randbelow(max_val - min_val + 1)


class RandomPickerSkill:

    async def flip_coin(self, command: VoiceCommand) -> CommandResult:
        """Pile ou face."""
        result = coin_flip()
        return CommandResult(True,
            f"C'est... {result}!",
            data={"result": result})

    async def roll_dice(self, command: VoiceCommand) -> CommandResult:
        """Lance un de."""
        import re
        sides = 6
        text = command.target or ""
        m = re.search(r'(\d+)', text)
        if m:
            sides = max(2, min(100, int(m.group(1))))

        result = dice_roll(sides)
        return CommandResult(True,
            f"Le dé à {sides} faces donne: {result}!",
            data={"result": result, "sides": sides})

    async def pick(self, command: VoiceCommand) -> CommandResult:
        """Choisit parmi une liste."""
        text = command.target or ""
        if not text:
            return CommandResult(False,
                "Donnez-moi des options séparées par 'ou'. "
                "Exemple: pizza ou sushi ou burger")

        # Parse les options (separees par "ou" ou ",")
        items = [x.strip() for x in text.replace(",", " ou ").split(" ou ") if x.strip()]

        if len(items) < 2:
            return CommandResult(False,
                "Il me faut au moins 2 options.")

        result = pick_from_list(items)
        return CommandResult(True,
            f"Mon choix: {result}!",
            data={"result": result, "options": items})

    async def random_num(self, command: VoiceCommand) -> CommandResult:
        """Nombre aleatoire."""
        import re
        text = command.target or ""
        m = re.search(r'(\d+)\s*(?:et|à|a|-)\s*(\d+)', text)
        if m:
            min_v = int(m.group(1))
            max_v = int(m.group(2))
        else:
            m = re.search(r'(\d+)', text)
            if m:
                min_v = 1
                max_v = int(m.group(1))
            else:
                min_v, max_v = 1, 100

        result = random_number(min_v, max_v)
        return CommandResult(True,
            f"Nombre aléatoire entre {min_v} et {max_v}: {result}!",
            data={"result": result, "min": min_v, "max": max_v})
