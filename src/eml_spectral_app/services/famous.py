"""Expose every famous equation baked into ``eml_math.FAMOUS`` to the UI.

The library ships 46+ named equations across geometry / math / physics
categories. Hand-curating a subset in the KV file would just go stale, so
the chip row reads from this service. Each entry is::

    (chip_label, python_expression, eml_description_after_dash)

``chip_label`` is the equation's human description (e.g. ``E = m c²``),
``python_expression`` is a valid Python expression the input field can
parse (built by walking the compact-mode tree), and the third element is
the eml-math native EML string (used as a tooltip / debug aid).
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Tree → Python source — operates on the compact (non-expanded) tree that
# eml-math ships in ``parse_eml_tree(..., expand_eml=False)``. Each node has
# a clean operator label, so the recursion is short and total.
# ---------------------------------------------------------------------------
# Map renderer-friendly Unicode glyphs back to plain ASCII identifiers
# eml-math accepts (``pi``, ``sigma`` …). The renderer shows π, σ, … but the
# parser & evaluator are keyed on the spelled names.
_GLYPH_TO_NAME = {
    "π": "pi", "Π": "pi",
    "σ": "sigma", "Σ": "sigma",
    "λ": "lambda_", "Λ": "lambda_",
    "γ": "gamma", "Γ": "gamma",
    "α": "alpha", "β": "beta",
    "θ": "theta", "Θ": "theta",
    "φ": "phi", "Φ": "phi",
    "ω": "omega", "Ω": "omega",
    "δ": "delta", "Δ": "delta",
    "ρ": "rho", "ε": "epsilon", "η": "eta", "μ": "mu", "ν": "nu",
    "τ": "tau", "ψ": "psi", "χ": "chi", "ζ": "zeta", "ξ": "xi",
}


def _normalize_leaf(label: str) -> str:
    """Make *label* a valid Python identifier / numeric literal."""
    if label.startswith("×"):
        label = label[1:]
    # Subscript digits — keep readable: x₁ → x1
    SUBS = str.maketrans({"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
                          "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"})
    label = label.translate(SUBS)
    # Single-glyph greek constants → ASCII names.
    if label in _GLYPH_TO_NAME:
        return _GLYPH_TO_NAME[label]
    # Mixed: replace any remaining mapped glyph in the middle of a token.
    for glyph, name in _GLYPH_TO_NAME.items():
        if glyph in label:
            label = label.replace(glyph, name)
    return label


def _tree_to_python(node) -> str:
    if not node.children:
        return _normalize_leaf(node.label)

    op = node.label
    args = [_tree_to_python(c) for c in node.children]
    if op == "add" and len(args) == 2:
        return f"({args[0]} + {args[1]})"
    if op == "sub" and len(args) == 2:
        return f"({args[0]} - {args[1]})"
    if op == "mul" and len(args) == 2:
        return f"({args[0]} * {args[1]})"
    if op == "div" and len(args) == 2:
        return f"({args[0]} / {args[1]})"
    if op == "pow" and len(args) == 2:
        return f"({args[0]} ** {args[1]})"
    if op == "sqrt":
        return f"sqrt({args[0]})"
    if op == "inv":
        return f"(1/{args[0]})"
    if op == "sqr":
        return f"({args[0]} ** 2)"
    if op == "neg":
        return f"(-{args[0]})"
    if op == "eml" and len(args) == 2:
        return f"(exp({args[0]}) - ln({args[1]}))"
    if op in {"exp", "ln", "log", "sin", "cos", "tan", "sinh", "cosh", "tanh",
              "arcsin", "arccos", "arctan", "asin", "acos", "atan", "abs",
              "sigmoid", "logistic", "hypot", "log10", "expm1", "log1p"}:
        return f"{op}({', '.join(args)})"
    # Unknown compound — emit a callable form; if the input field re-parses
    # this it will still produce a ``compound`` node.
    return f"{op}({', '.join(args)})"


@lru_cache(maxsize=1)
def all_famous() -> List[Tuple[str, str, str]]:
    """Return ``[(label, python_expression, raw_eml), ...]`` for every
    famous equation in eml-math, sorted by category then name.

    Cached because the eml-math symbol table is module-level and never
    changes during the app's lifetime.
    """
    from eml_math import FAMOUS, get_famous, parse_eml_tree

    by_cat: dict = {}
    for name in FAMOUS:
        fe = get_famous(name)
        cat = fe.category or "other"
        by_cat.setdefault(cat, []).append((name, fe))

    out: List[Tuple[str, str, str]] = []
    for cat in sorted(by_cat):
        for _, fe in sorted(by_cat[cat], key=lambda nf: nf[1].title):
            try:
                head = fe.eml.split(" — ", 1)[0]
                t = parse_eml_tree(head, expand_eml=False)
                py = _tree_to_python(t)
            except Exception:                              # noqa: BLE001
                py = fe.description.split("=", 1)[-1].strip()
            label = fe.description or fe.title
            out.append((label, py, fe.eml))
    return out
