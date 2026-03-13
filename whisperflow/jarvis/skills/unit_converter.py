"""
JARVIS Skill - Convertisseur d'unites vocal

Securite: calculs arithmetiques purs en memoire.
Aucun appel externe, facteurs de conversion statiques.
"""

import logging
import re
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.unit_converter")

# Facteurs de conversion (vers unite de base SI)
_CONVERSIONS = {
    # Distance (base: metres)
    "km": {"base": "m", "factor": 1000, "name": "kilomètres"},
    "m": {"base": "m", "factor": 1, "name": "mètres"},
    "cm": {"base": "m", "factor": 0.01, "name": "centimètres"},
    "mm": {"base": "m", "factor": 0.001, "name": "millimètres"},
    "miles": {"base": "m", "factor": 1609.344, "name": "miles"},
    "yards": {"base": "m", "factor": 0.9144, "name": "yards"},
    "feet": {"base": "m", "factor": 0.3048, "name": "pieds"},
    "inches": {"base": "m", "factor": 0.0254, "name": "pouces"},
    "pieds": {"base": "m", "factor": 0.3048, "name": "pieds"},
    "pouces": {"base": "m", "factor": 0.0254, "name": "pouces"},
    "kilomètres": {"base": "m", "factor": 1000, "name": "kilomètres"},
    "mètres": {"base": "m", "factor": 1, "name": "mètres"},
    "centimètres": {"base": "m", "factor": 0.01, "name": "centimètres"},

    # Poids (base: kg)
    "kg": {"base": "kg", "factor": 1, "name": "kilogrammes"},
    "g": {"base": "kg", "factor": 0.001, "name": "grammes"},
    "mg": {"base": "kg", "factor": 0.000001, "name": "milligrammes"},
    "lbs": {"base": "kg", "factor": 0.453592, "name": "livres"},
    "oz": {"base": "kg", "factor": 0.0283495, "name": "onces"},
    "livres": {"base": "kg", "factor": 0.453592, "name": "livres"},
    "onces": {"base": "kg", "factor": 0.0283495, "name": "onces"},
    "kilogrammes": {"base": "kg", "factor": 1, "name": "kilogrammes"},
    "grammes": {"base": "kg", "factor": 0.001, "name": "grammes"},
    "tonnes": {"base": "kg", "factor": 1000, "name": "tonnes"},

    # Donnees (base: octets)
    "octets": {"base": "o", "factor": 1, "name": "octets"},
    "ko": {"base": "o", "factor": 1024, "name": "kilo-octets"},
    "mo": {"base": "o", "factor": 1048576, "name": "méga-octets"},
    "go": {"base": "o", "factor": 1073741824, "name": "giga-octets"},
    "to": {"base": "o", "factor": 1099511627776, "name": "téra-octets"},
    "bytes": {"base": "o", "factor": 1, "name": "bytes"},
    "kb": {"base": "o", "factor": 1024, "name": "kilobytes"},
    "mb": {"base": "o", "factor": 1048576, "name": "megabytes"},
    "gb": {"base": "o", "factor": 1073741824, "name": "gigabytes"},
    "tb": {"base": "o", "factor": 1099511627776, "name": "terabytes"},
}

# Aliases FR pour parsing
_UNIT_ALIASES = {
    "kilomètre": "km", "kilomètres": "km",
    "mètre": "m", "mètres": "m",
    "centimètre": "cm", "centimètres": "cm",
    "millimètre": "mm", "millimètres": "mm",
    "mile": "miles",
    "yard": "yards",
    "pied": "pieds", "feet": "pieds", "foot": "pieds",
    "pouce": "pouces", "inch": "pouces", "inches": "pouces",
    "kilogramme": "kg", "kilo": "kg", "kilos": "kg",
    "gramme": "g",
    "milligramme": "mg",
    "livre": "livres", "pound": "lbs", "pounds": "lbs",
    "once": "onces", "ounce": "oz", "ounces": "oz",
    "tonne": "tonnes",
    "octet": "octets", "byte": "bytes",
    "kilo-octet": "ko", "kilobyte": "kb",
    "méga-octet": "mo", "megabyte": "mb",
    "giga-octet": "go", "gigabyte": "gb",
    "téra-octet": "to", "terabyte": "tb",
}


def _normalize_unit(text: str) -> str:
    """Normalise le nom d'unite."""
    t = text.lower().strip()
    return _UNIT_ALIASES.get(t, t)


def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """Convertit une valeur entre deux unites compatibles."""
    fu = _normalize_unit(from_unit)
    tu = _normalize_unit(to_unit)

    if fu not in _CONVERSIONS or tu not in _CONVERSIONS:
        raise ValueError(f"Unité inconnue: {fu if fu not in _CONVERSIONS else tu}")

    fc = _CONVERSIONS[fu]
    tc = _CONVERSIONS[tu]

    if fc["base"] != tc["base"]:
        raise ValueError(f"Unités incompatibles: {fc['name']} et {tc['name']}")

    # Convertit via unite de base
    base_value = value * fc["factor"]
    return base_value / tc["factor"]


def _format_value(value: float) -> str:
    """Formate le resultat pour la voix."""
    if value == int(value) and abs(value) < 1e12:
        return str(int(value))
    if abs(value) >= 1000:
        return f"{value:,.2f}"
    return f"{value:.4f}".rstrip("0").rstrip(".")


class UnitConverterSkill:

    async def convert(self, command: VoiceCommand) -> CommandResult:
        """Convertit des unites. Ex: '5 km en miles'"""
        # Utilise les groupes du Commander si disponibles (3 groupes: valeur, from, to)
        groups = command.params.get("groups", ())
        if len(groups) >= 3:
            val_str, from_u, to_u = groups[0], groups[1], groups[2]
            try:
                value = float(val_str.replace(",", "."))
                from_u = from_u.strip()
                to_u = to_u.strip()
            except (ValueError, AttributeError):
                return CommandResult(False, "Format: X unité en unité")
        else:
            # Fallback: re-parse depuis raw_text
            text = command.raw_text or command.target or ""
            if not text:
                return CommandResult(False, "Rien à convertir")
            m = re.search(
                r'(\d+(?:[.,]\d+)?)\s*([a-zéèêàâôûïü-]+)\s+(?:en|to|in|vers)\s+([a-zéèêàâôûïü-]+)',
                text.lower(), re.IGNORECASE
            )
            if not m:
                return CommandResult(False, "Format: X unité en unité")
            value = float(m.group(1).replace(",", "."))
            from_u = m.group(2)
            to_u = m.group(3)

        try:
            result = convert_units(value, from_u, to_u)
            from_name = _CONVERSIONS.get(_normalize_unit(from_u), {}).get("name", from_u)
            to_name = _CONVERSIONS.get(_normalize_unit(to_u), {}).get("name", to_u)

            return CommandResult(
                True,
                f"{_format_value(value)} {from_name} = {_format_value(result)} {to_name}",
                data={"value": value, "result": result, "from": from_u, "to": to_u}
            )
        except ValueError as e:
            return CommandResult(False, str(e))
