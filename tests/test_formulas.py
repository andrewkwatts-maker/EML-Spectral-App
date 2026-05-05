"""End-to-end formula coverage for the single-page UI.

Every formula goes through the same pipeline the screen uses:

    text  ──► default_parser().parse(text)
                       │
                       ▼
              ParsedExpression(eml, tree, info_line, search_result)
                       │
                       ├──► format_all(...)           (EML / LaTeX / Python / JSON outputs)
                       ├──► tree.flow_png(...)        (the PNG the user sees)
                       ├──► tree.layout(...)          (the layout the hover layer uses)
                       └──► latex_renderer.render_latex_png(latex)
                                                       (the typeset preview above the input)

We assert each stage produces real output. Anything that returns ``None``
or the magic ``kind='unknown'`` leaf is a regression.

Cases span basic arithmetic → trig identities → famous physics formulae
(Einstein, Newton, Pythagoras, Planck, Lorentz, Ohm, …) so a future
breakage in eml-math's AST walker, the LaTeX path, or the layout engine
shows up here before the user types a single character.
"""
from __future__ import annotations

from typing import Tuple

import pytest

from eml_spectral_app.services.formats import format_all, normal_math
from eml_spectral_app.services.latex_renderer import (
    render_latex_png,
    to_latex_source,
)
from eml_spectral_app.services.parser import default_parser


# ---------------------------------------------------------------------------
# Test corpus — (label, expression). Order matters only for the screenshot
# script; the parametrize ids show up in pytest output.
# ---------------------------------------------------------------------------
BASIC = [
    ("constant_int",         "1"),
    ("constant_sum",         "1 + 1"),
    ("constant_product",     "2 * 3"),
    ("identity_x",           "x"),
    ("two_var_add",          "x + y"),
    ("two_var_sub",          "x - y"),
    ("ratio",                "x / y"),
    ("power",                "x ** 2"),
    ("multivariate_compose", "(1/x) + (y**3)"),
    ("nested_grouping",      "(a + b) * (c - d)"),
]

TRIGONOMETRIC = [
    ("sin_plus_cos",         "sin(x) + cos(x)"),
    ("pythagoras_trig",      "sin(x)**2 + cos(x)**2"),
    ("euclidean_norm",       "sqrt(x**2 + y**2)"),
    ("tangent_quotient",     "sin(x) / cos(x)"),
]

FAMOUS_PHYSICS = [
    ("einstein_e_mc2",       "m * c ** 2"),
    ("newton_f_ma",          "m * a"),
    ("ohms_law",             "I * R"),
    ("planck_e_hf",          "h * f"),
    ("circle_area",          "pi * r ** 2"),
    ("circle_circumference", "2 * pi * r"),
    ("kinetic_energy",       "(1/2) * m * v ** 2"),
    ("lorentz_factor",       "1 / sqrt(1 - v**2 / c**2)"),
    ("coulomb_k_qq_r2",      "k * q1 * q2 / r ** 2"),
    ("ideal_gas",            "P * V"),  # = nRT — single side suffices for tree shape
]

ALL_CASES = BASIC + TRIGONOMETRIC + FAMOUS_PHYSICS


# ---------------------------------------------------------------------------
# Pipeline assertions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("label,expr", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_parse_succeeds(label: str, expr: str) -> None:
    parser = default_parser()
    parsed = parser.parse(expr)
    assert parsed is not None, f"parse returned None for {expr!r}"
    assert parsed.tree is not None
    assert parsed.eml.strip() != ""


@pytest.mark.parametrize("label,expr", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_tree_has_no_unknown_descendants(label: str, expr: str) -> None:
    """The BinOp regression in eml-math used to leave ``kind='unknown'`` on
    every infix node. Pin that it stays fixed for every case in the corpus."""
    parsed = default_parser().parse(expr)
    seen = []
    stack = [parsed.tree]
    while stack:
        n = stack.pop()
        seen.append(n)
        stack.extend(n.children)
    bad = [n for n in seen if n.kind == "unknown"]
    assert not bad, f"unknown kinds in {expr!r}: {[n.label for n in bad]}"


@pytest.mark.parametrize("label,expr", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_format_all_returns_strings(label: str, expr: str) -> None:
    parsed = default_parser().parse(expr)
    formats = format_all(parsed)
    assert set(formats) == {"eml", "latex", "python", "json"}
    for k, v in formats.items():
        assert isinstance(v, str) and v.strip(), f"empty {k!r} for {expr!r}"


@pytest.mark.parametrize("label,expr", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_tree_renders_to_png(label: str, expr: str) -> None:
    parsed = default_parser().parse(expr)
    png = parsed.tree.flow_png(direction="down", width=400, height=280)
    assert isinstance(png, (bytes, bytearray)) and len(png) > 200, (
        f"PNG too small for {expr!r}: {len(png)} bytes"
    )


@pytest.mark.parametrize("label,expr", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_tree_layout_has_nodes(label: str, expr: str) -> None:
    parsed = default_parser().parse(expr)
    layout = parsed.tree.layout(direction="down", canvas=(400, 280))
    nodes = layout["nodes"]
    assert nodes, f"empty layout for {expr!r}"
    # The hover layer needs every node to expose x/y/kind/label.
    for n in nodes:
        assert {"id", "label", "kind", "x", "y"}.issubset(n.keys())


@pytest.mark.parametrize("label,expr", ALL_CASES, ids=[c[0] for c in ALL_CASES])
def test_latex_preview_renders(label: str, expr: str) -> None:
    parsed = default_parser().parse(expr)
    latex = to_latex_source(expr, parsed)
    assert latex and isinstance(latex, str), f"no latex for {expr!r}"
    png = render_latex_png(latex, figsize=(6.0, 1.0), dpi=100)
    assert isinstance(png, (bytes, bytearray)) and len(png) > 200, (
        f"latex preview too small for {expr!r}"
    )


# ---------------------------------------------------------------------------
# Compress button — single-variable cases only (the eml-math beam-search
# can't compress multivariate expressions, so we just exercise the ones it
# does support).
# ---------------------------------------------------------------------------
COMPRESSIBLE = [
    ("sin_plus_cos",     "sin(x) + cos(x)"),
    ("polynomial",       "x**2 + 2*x + 1"),
    ("trig_squares",     "sin(x)**2 + cos(x)**2"),
]


@pytest.mark.parametrize("label,expr", COMPRESSIBLE, ids=[c[0] for c in COMPRESSIBLE])
def test_compress_returns_normal_math(label: str, expr: str) -> None:
    """Compress button must write back ``cos(x) + sin(x)`` style — no
    ``import math`` header, no ``math.`` prefix, no EML primitive form."""
    parsed = default_parser().parse(expr)
    out = normal_math(parsed)
    assert out, f"empty normal_math output for {expr!r}"
    assert "import math" not in out
    assert "math." not in out
    assert "lambda" not in out
