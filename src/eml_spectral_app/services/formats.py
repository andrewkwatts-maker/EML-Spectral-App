"""Format adapters: ``ParsedExpression`` → strings the GUI displays.

The screen never imports ``eml_math.decompress`` directly; it asks here.
Each format is a one-line function (SRP), gathered into :func:`format_all`
for the bulk path the screen uses.
"""
from __future__ import annotations

import json
from typing import Any, Dict


def to_eml(parsed: Any) -> str:
    return parsed.eml


def to_latex(parsed: Any) -> str:
    """Prefer eml-math's LaTeX (search result) over the tree's AST repr,
    which is garbage for unknown-kind nodes."""
    if parsed.search_result is not None:
        from eml_math import decompress
        return decompress(parsed.search_result, fmt="latex")
    try:
        return parsed.tree.to_latex()
    except Exception:                                  # noqa: BLE001
        return parsed.eml


def to_python(parsed: Any) -> str:
    if parsed.search_result is not None:
        from eml_math import decompress
        try:
            return decompress(parsed.search_result, fmt="python")
        except Exception as exc:                       # noqa: BLE001
            return f"# python decompress failed: {exc}"
    return f"# eml: {parsed.eml}"


def to_json(parsed: Any) -> str:
    """Headline JSON — only EML-canonical representations.

    Deliberately drops the compact-form serialisation (``to_compact``)
    because its labels (``mul``, ``div``, ``pow`` …) are *not* EML
    primitives — they're convenience names for compound ops. Showing
    them in the JSON misled the reader; LaTeX is the right representation
    for anything outside the ``exp / ln / add / sub`` core, and the EML
    line below preserves the raw input.
    """
    payload: Dict[str, Any] = {
        "eml": parsed.eml,
        "latex": to_latex(parsed),
    }
    sr = parsed.search_result
    if sr is not None:
        payload["search"] = {
            "formula": sr.formula,
            "complexity": sr.complexity,
            "error": sr.error,
            "params": list(sr.params),
        }
    return json.dumps(payload, indent=2)


def format_all(parsed: Any) -> Dict[str, str]:
    return {
        "eml": to_eml(parsed),
        "latex": to_latex(parsed),
        "python": to_python(parsed),
        "json": to_json(parsed),
    }


def normal_math(parsed: Any) -> str:
    """Return a "normal math" string suitable for an input field.

    Uses ``SearchResult.formula`` when available (gives ``cos(x) + sin(x)``,
    no ``math.`` prefix and no ``import math`` header). Falls back to the
    EML source text otherwise.
    """
    if parsed.search_result is not None:
        return parsed.search_result.formula
    return parsed.eml
