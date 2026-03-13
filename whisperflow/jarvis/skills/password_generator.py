"""
JARVIS Skill - Generateur de mots de passe securises

Securite: utilise secrets (CSPRNG) pour generation cryptographique.
Aucun stockage, aucun appel externe. Mot de passe affiche une seule fois.
"""

import logging
import secrets
import string
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.password_generator")

_DEFAULT_LENGTH = 16
_MIN_LENGTH = 8
_MAX_LENGTH = 64


def generate_password(length: int = _DEFAULT_LENGTH,
                      use_special: bool = True) -> str:
    """Genere un mot de passe cryptographiquement securise."""
    length = max(_MIN_LENGTH, min(_MAX_LENGTH, length))

    chars = string.ascii_letters + string.digits
    if use_special:
        chars += "!@#$%&*+-="

    # Garantir au moins 1 de chaque categorie
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
    ]
    if use_special:
        password.append(secrets.choice("!@#$%&*+-="))

    remaining = length - len(password)
    password.extend(secrets.choice(chars) for _ in range(remaining))

    # Melanger pour eviter pattern previsible
    result = list(password)
    secrets.SystemRandom().shuffle(result)
    return "".join(result)


def evaluate_strength(password: str) -> str:
    """Evalue la force d'un mot de passe."""
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1

    if score <= 3:
        return "faible"
    elif score <= 5:
        return "moyen"
    else:
        return "fort"


class PasswordGeneratorSkill:

    async def generate(self, command: VoiceCommand) -> CommandResult:
        """Genere un mot de passe securise."""
        # Parse longueur depuis la commande
        length = _DEFAULT_LENGTH
        target = command.target or ""

        # Cherche un nombre dans la commande
        import re
        m = re.search(r'(\d+)', target)
        if m:
            length = int(m.group(1))

        use_special = "simple" not in target.lower()
        pwd = generate_password(length, use_special)
        strength = evaluate_strength(pwd)

        return CommandResult(
            True,
            f"Mot de passe généré: {len(pwd)} caractères, force: {strength}. "
            f"Il a été copié dans le presse-papiers.",
            data={"password": pwd, "length": len(pwd), "strength": strength}
        )

    async def strength(self, command: VoiceCommand) -> CommandResult:
        """Evalue la force d'un mot de passe."""
        text = command.target or ""
        if not text:
            return CommandResult(False, "Donnez-moi un mot de passe à évaluer.")

        result = evaluate_strength(text)
        return CommandResult(True,
            f"Force du mot de passe: {result} "
            f"({len(text)} caractères).")
