"""Expose every famous equation baked into ``eml_math.FAMOUS`` to the UI.

Each entry returned by :func:`all_famous` is a triple::

    (chip_label, python_expression, raw_eml_description)

``chip_label`` is the equation's human description (e.g. ``E = m c²``);
``python_expression`` is a clickable Python form built by walking the
compact-mode tree via :func:`eml_math.tree_to_python` (the library owns
the conversion — this module is just a thin re-shape for the chip row);
``raw_eml_description`` is the native EML string that came out of
``FamousEquation.eml`` (kept as a tooltip / debug aid).
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Tuple


# Renderer-friendly Greek glyphs that appear as eml-math vec leaves
# (``π``, ``σ``, ``λ``, …) need to become valid Python identifiers before
# the chip's expression can be re-parsed by the input field. eml-math's
# ``tree_to_python`` preserves leaf labels verbatim, so we post-process
# the output here. (This is presentation-layer cleanup — keeping the
# library's contract clean.)
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


def _greek_to_ascii(text: str) -> str:
    """Replace Greek single-letter constants with their ASCII names."""
    for glyph, name in _GLYPH_TO_NAME.items():
        if glyph in text:
            text = text.replace(glyph, name)
    return text


@lru_cache(maxsize=1)
def all_famous() -> List[Tuple[str, str, str]]:
    """Return ``[(label, python_expression, raw_eml), ...]`` for every
    famous equation in eml-math, sorted by category then title.

    Cached because the eml-math symbol table is module-level and never
    changes during the app's lifetime.
    """
    from eml_math import FAMOUS, get_famous, parse_eml_tree, tree_to_python

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
                tree = parse_eml_tree(head, expand_eml=False)
                py = _greek_to_ascii(tree_to_python(tree))
            except Exception:                              # noqa: BLE001
                py = fe.description.split("=", 1)[-1].strip()
            label = fe.description or fe.title
            out.append((label, py, fe.eml))
    return out
