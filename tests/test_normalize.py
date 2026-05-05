"""Pin the input-normalisation contract.

The user types math the way it appears in print — caret for power, ``×``
for multiplication, Unicode minus, superscript exponents — and expects
the parser to accept it. ``services.parser._normalize_input`` is the
single rewrite step that maps those keystrokes onto the canonical Python
syntax eml-math expects. Each substitution is pinned here so a future
refactor doesn't quietly drop one and break user input.
"""
from __future__ import annotations

import pytest

from eml_spectral_app.services.parser import _normalize_input


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # caret → ** (the headline ask)
        ("a^b",                "a**b"),
        ("m^c**2",             "m**c**2"),
        # Unicode operators copied out of LaTeX renderings
        ("a×b",                "a*b"),
        ("π·r",                "π*r"),   # operator normalised, identifier left alone
        ("a÷b",                "a/b"),
        ("a−b",                "a-b"),
        # Unicode superscripts → ^N then → **N
        ("x²",                 "x**2"),
        ("y³ + x⁵",            "y**3 + x**5"),
        # Subscripts kept as plain digits
        ("x₁ + y₂",            "x1 + y2"),
        # Mix
        ("a^b + 2×c − d/e",    "a**b + 2*c - d/e"),
    ],
)
def test_substitutions(raw: str, expected: str) -> None:
    assert _normalize_input(raw) == expected


def test_double_star_not_re_doubled() -> None:
    """``**`` must not be re-expanded by the caret regex."""
    assert _normalize_input("a**b") == "a**b"
    assert _normalize_input("a ** b") == "a ** b"


def test_empty_and_none_safe() -> None:
    assert _normalize_input("") == ""
    assert _normalize_input(None) is None  # type: ignore[arg-type]


def test_normalisation_runs_via_multiparser() -> None:
    """End-to-end: the live ``MultiParser.parse`` accepts caret input."""
    from eml_spectral_app.services.parser import default_parser
    parsed = default_parser().parse("m^c**2")
    assert parsed is not None
    # The ``eml`` field carries the *normalised* source — caret resolved.
    assert "^" not in parsed.eml
    assert "**" in parsed.eml
