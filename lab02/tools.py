import ast
import operator as op
from urllib.parse import quote

import requests

OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            raise ValueError("Unsupported expression")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
        return OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression):
    try:
        expr = str(expression).replace(",", "").replace("GHS", "").strip()
        result = _eval(ast.parse(expr, mode="eval").body)
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return str(round(result, 6))
    except Exception as exc:
        return f"Error: {exc}"


def wiki_lookup(title):
    url = (
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + quote(title.strip().replace(" ", "_"), safe="")
    )
    try:
        response = requests.get(
            url, timeout=10, headers={"User-Agent": "DCIT403-lab02"}
        )
    except requests.RequestException as exc:
        return f"Wikipedia lookup failed: {exc}"
    if response.status_code != 200:
        return f"No Wikipedia page found for '{title}'."
    extract = response.json().get("extract", "")
    if not extract:
        return f"Wikipedia page '{title}' has no summary text."
    return extract[:800]


TOOLS = {"calculator": calculator, "wiki_lookup": wiki_lookup}

TOOL_DESCRIPTIONS = """- calculator: evaluates one arithmetic expression. Input: a plain expression
  such as 4*185 + 3*95. Use it for every arithmetic step.
- wiki_lookup: returns a short Wikipedia summary. Input: a page title such as
  Makola Market. Use it for facts about people, places and history."""

TOOL_NAMES = " | ".join(TOOLS) + " | finish"
