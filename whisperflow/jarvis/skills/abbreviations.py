"""
JARVIS Skill - Dictionnaire d'abreviations

Securite: dictionnaire statique en memoire.
Aucun appel externe, aucune modification systeme.
"""

import logging
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.abbreviations")

# Dictionnaire FR courant
_ABBREVIATIONS = {
    # Informatique
    "ia": "Intelligence Artificielle",
    "api": "Application Programming Interface",
    "cpu": "Central Processing Unit",
    "gpu": "Graphics Processing Unit",
    "ram": "Random Access Memory",
    "ssd": "Solid State Drive",
    "hdd": "Hard Disk Drive",
    "usb": "Universal Serial Bus",
    "html": "HyperText Markup Language",
    "css": "Cascading Style Sheets",
    "sql": "Structured Query Language",
    "url": "Uniform Resource Locator",
    "ip": "Internet Protocol",
    "http": "HyperText Transfer Protocol",
    "https": "HyperText Transfer Protocol Secure",
    "dns": "Domain Name System",
    "vpn": "Virtual Private Network",
    "pdf": "Portable Document Format",
    "json": "JavaScript Object Notation",
    "xml": "eXtensible Markup Language",
    "ide": "Integrated Development Environment",
    "cli": "Command Line Interface",
    "gui": "Graphical User Interface",
    "os": "Operating System",
    "iot": "Internet of Things",
    "ml": "Machine Learning",
    "llm": "Large Language Model",
    "nlp": "Natural Language Processing",

    # General FR
    "rh": "Ressources Humaines",
    "pme": "Petite et Moyenne Entreprise",
    "tva": "Taxe sur la Valeur Ajoutée",
    "smic": "Salaire Minimum Interprofessionnel de Croissance",
    "bac": "Baccalauréat",
    "bts": "Brevet de Technicien Supérieur",
    "dut": "Diplôme Universitaire de Technologie",
    "cdi": "Contrat à Durée Indéterminée",
    "cdd": "Contrat à Durée Déterminée",
    "cv": "Curriculum Vitae",
    "rsa": "Revenu de Solidarité Active",
    "sncf": "Société Nationale des Chemins de fer Français",
    "ratp": "Régie Autonome des Transports Parisiens",

    # Organisations
    "onu": "Organisation des Nations Unies",
    "ue": "Union Européenne",
    "otan": "Organisation du Traité de l'Atlantique Nord",
    "nasa": "National Aeronautics and Space Administration",
    "oms": "Organisation Mondiale de la Santé",
    "fmi": "Fonds Monétaire International",

    # Unites
    "km": "kilomètre",
    "kg": "kilogramme",
    "mb": "mégaoctet",
    "gb": "gigaoctet",
    "tb": "téraoctet",
}


def lookup_abbreviation(abbr: str) -> str:
    """Cherche une abreviation dans le dictionnaire."""
    return _ABBREVIATIONS.get(abbr.lower().strip(), "")


def get_all_abbreviations() -> dict:
    """Retourne tout le dictionnaire."""
    return dict(_ABBREVIATIONS)


class AbbreviationsSkill:

    async def define(self, command: VoiceCommand) -> CommandResult:
        """Donne la definition d'une abreviation."""
        text = (command.target or "").strip()
        if not text:
            return CommandResult(False,
                "Donnez-moi une abréviation. Exemple: API, CPU, HTML.")

        result = lookup_abbreviation(text)
        if result:
            return CommandResult(True,
                f"{text.upper()} signifie: {result}.",
                data={"abbreviation": text.upper(), "definition": result})

        return CommandResult(False,
            f"Je ne connais pas l'abréviation '{text}'. "
            f"Je connais {len(_ABBREVIATIONS)} abréviations courantes.")

    async def list_category(self, command: VoiceCommand) -> CommandResult:
        """Liste les abreviations disponibles."""
        count = len(_ABBREVIATIONS)
        # Montre quelques exemples
        samples = list(_ABBREVIATIONS.keys())[:5]
        examples = ", ".join(s.upper() for s in samples)
        return CommandResult(True,
            f"Je connais {count} abréviations. "
            f"Exemples: {examples}... "
            f"Demandez la définition de n'importe laquelle.",
            data={"count": count})
