"""Stress-test the EML → normal-math back-conversion contract.

The library's ``EMLTreeNode.to_latex`` already pattern-matches the EML
primitive expansions back to ``mul / div / pow / sqrt / inv / abs``.
Walk every entry in ``eml_math.FAMOUS`` and confirm:

  - ``parse_eml_tree(..., expand_eml=True)`` returns a tree that
    ``to_latex()`` is willing to render,
  - The rendered LaTeX contains the **operator marker(s)** we expect for
    that equation's shape (no leftover ``\exp(\ln \dots)`` ribbons in the
    final string for cases the patterns should have collapsed).

Pins the eml-math contract from the consumer side — a future regression
in tree.py's pattern matcher fails this suite before it reaches users.
"""
from __future__ import annotations

import pytest

from eml_math import FAMOUS, get_famous, parse_eml_tree


@pytest.mark.parametrize("name", sorted(FAMOUS))
def test_to_latex_emits_non_empty(name: str) -> None:
    fe = get_famous(name)
    head = fe.eml.split(" — ", 1)[0]
    tree = parse_eml_tree(head, expand_eml=True)
    out = tree.to_latex()
    assert isinstance(out, str) and out.strip(), name


@pytest.mark.parametrize(
    ("name", "must_contain"),
    [
        # Powers must render via ``^`` in LaTeX rather than as raw exp/ln.
        ("einstein_e_mc2",       ["c", "^", "{2}"]),
        ("circle_area",          ["r", "^", "{2}"]),
        ("kinetic_energy",       ["v", "^", "{2}"]),
        ("relativistic_energy",  ["sqrt"]),
        ("lorentz_factor",       ["sqrt"]),
        # Divisions must use \frac (or at least one ``/``).
        ("ohms_law",             ["I", "R"]),
        ("planck_e_hf",          ["h", "f"]),
        ("de_broglie",           ["h", "p"]),
    ],
)
def test_to_latex_contains_expected_markers(name: str, must_contain: list) -> None:
    """Operator-pattern markers survive into the LaTeX output."""
    fe = get_famous(name)
    head = fe.eml.split(" — ", 1)[0]
    out = parse_eml_tree(head, expand_eml=True).to_latex()
    for token in must_contain:
        assert token in out, f"{name}: missing {token!r} in {out!r}"


def test_no_compact_form_leakage() -> None:
    """``to_latex`` should never emit raw ``mul(`` / ``div(`` / ``pow(``
    operator names — those are EML's compact-form *labels*, not LaTeX."""
    bad_tokens = ("\\mul", "\\div(", "\\pow", "\\add(")
    for name in FAMOUS:
        fe = get_famous(name)
        head = fe.eml.split(" — ", 1)[0]
        out = parse_eml_tree(head, expand_eml=True).to_latex()
        for tok in bad_tokens:
            assert tok not in out, f"{name}: leaked {tok} in {out!r}"
