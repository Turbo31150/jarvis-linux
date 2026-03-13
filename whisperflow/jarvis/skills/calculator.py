"""
JARVIS Skill - Calculatrice vocale

Sécurité: Parse AST statique uniquement via ast.parse().
Aucun appel a la fonction builtin eval().
Seuls les noeuds Constant, BinOp et UnaryOp sont acceptes.
Operateurs: +, -, *, /, %, puissance.
"""

import ast
import logging
import operator
import re
from ..commander import VoiceCommand, CommandResult

logger = logging.getLogger("jarvis.skills.calculator")

# Mapping mots FR -> operateurs
_WORD_TO_OP = {
    "plus": "+", "et": "+", "add": "+",
    "moins": "-", "minus": "-", "subtract": "-",
    "fois": "*", "multiplie par": "*", "times": "*", "x": "*",
    "divise par": "/", "sur": "/", "divided by": "/",
    "puissance": "**", "exposant": "**", "power": "**",
    "modulo": "%", "mod": "%",
}

# Operateurs autorises pour le parser AST
_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _ast_compute(expr: str) -> float:
    """Calcule une expression via AST statique. N'utilise PAS eval()."""
    tree = ast.parse(expr, mode='eval')

    def _visit(node):
        if isinstance(node, ast.Expression):
            return _visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op_func = _SAFE_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Operateur non supporte: {type(node.op).__name__}")
            left = _visit(node.left)
            right = _visit(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Division par zero")
            if isinstance(node.op, ast.Pow) and right > 100:
                raise ValueError("Exposant trop grand")
            return op_func(left, right)
        if isinstance(node, ast.UnaryOp):
            op_func = _SAFE_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Operateur non supporte: {type(node.op).__name__}")
            return op_func(_visit(node.operand))
        raise ValueError(f"Expression non supportee: {type(node).__name__}")

    return _visit(tree)


def _text_to_math(text: str) -> str:
    """Convertit le texte vocal en expression mathematique."""
    result = text.lower().strip()

    # Remplacer "virgule" par "."
    result = re.sub(r'(\d+)\s*virgule\s*(\d+)', r'\1.\2', result)

    # Remplacer les mots par les operateurs (plus longs d'abord)
    for word, op in sorted(_WORD_TO_OP.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, f" {op} ")

    # Nettoyer: garder uniquement chiffres, operateurs, espaces, points, parentheses
    result = re.sub(r'[^0-9+\-*/.%() ]', ' ', result)
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def _format_result(value: float) -> str:
    """Formate le resultat pour la lecture vocale."""
    if value == int(value):
        return str(int(value))
    return f"{value:.4f}".rstrip('0').rstrip('.')


class CalculatorSkill:

    async def calculate(self, command: VoiceCommand) -> CommandResult:
        """Calcule une expression mathematique vocale."""
        text = command.target or command.raw_text
        if not text or not text.strip():
            return CommandResult(False, "Rien a calculer")

        try:
            expr = _text_to_math(text)
            if not expr or not any(c.isdigit() for c in expr):
                return CommandResult(False, "Expression non reconnue")

            result = _ast_compute(expr)
            formatted = _format_result(result)
            return CommandResult(True, f"Resultat: {formatted}",
                                 data={"expression": expr, "result": result})
        except (ValueError, SyntaxError, TypeError) as e:
            return CommandResult(False, f"Erreur de calcul: {e}")

    async def percentage(self, command: VoiceCommand) -> CommandResult:
        """Calcule un pourcentage. Ex: '20 pourcent de 150'"""
        text = command.raw_text or command.target
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:pourcent|%|percent)\s+(?:de|of)\s+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if not m:
            return CommandResult(False, "Format: X pourcent de Y")
        pct = float(m.group(1))
        total = float(m.group(2))
        result = pct * total / 100
        return CommandResult(True, f"{pct}% de {_format_result(total)} = {_format_result(result)}")

    async def convert_temperature(self, command: VoiceCommand) -> CommandResult:
        """Conversion de temperature."""
        text = command.target or command.raw_text
        m = re.search(r'(\d+(?:\.\d+)?)\s*(?:degres?|°)?\s*(?:en\s+)?(celsius|fahrenheit|kelvin|c|f|k)', text, re.IGNORECASE)
        if not m:
            return CommandResult(False, "Format: X degres en celsius/fahrenheit/kelvin")
        value = float(m.group(1))
        target = m.group(2).lower()[0]

        if target == 'f':
            result = value * 9 / 5 + 32
            return CommandResult(True, f"{_format_result(value)} celsius = {_format_result(result)} fahrenheit")
        elif target == 'c':
            result = (value - 32) * 5 / 9
            return CommandResult(True, f"{_format_result(value)} fahrenheit = {_format_result(result)} celsius")
        elif target == 'k':
            result = value + 273.15
            return CommandResult(True, f"{_format_result(value)} celsius = {_format_result(result)} kelvin")
        return CommandResult(False, "Conversion non reconnue")
