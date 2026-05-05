"""Parser strategy registry for EML expressions.

Strategies are tried in order — first non-None wins (OCP: append a new
dialect without touching the screen). Each strategy returns a
:class:`ParsedExpression` so the screen sees one shape regardless of how
the parse happened.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Protocol

# The single rewrite step that maps caret / Unicode-operator user input
# onto Python form lives in eml-math now (the library is the source of
# truth for what the parser accepts). Re-export under the historical
# private name so the existing call site stays unchanged.
from eml_math import normalize_input as _normalize_input


@dataclass
class ParsedExpression:
    """View-model returned by a parser. The screen never looks past this.

    ``tree`` is the user's typed expression rendered as a pure-EML tree.
    ``compressed_tree`` is populated only when the beam search succeeded
    and the compressed result differs from the input — the pill switch on
    the screen lets the user flip between the two views.
    """

    eml: str            # canonical EML / Python source string for ``tree``
    tree: Any           # EMLTreeNode — pure-EML (eml(L,R)) view, for the graph
    info_line: str      # one-line status describing the parse path
    search_result: Any = None       # eml_math.SearchResult when compress ran
    compressed_tree: Any = None     # pure-EML tree of the compressed form
    compressed_latex: str = ""      # LaTeX string of the compressed form
    # Parallel "expanded but not pure" tree — used for the normal-math
    # LaTeX rendering. Its to_latex() pattern-matches exp/ln/add/sub back
    # into mul/div/pow/sqrt/inv etc. so the user sees readable maths
    # alongside the literal EML primitive form on the graph side.
    normal_tree: Any = None
    compressed_normal_tree: Any = None


class ParseStrategy(Protocol):
    def applies(self, text: str) -> bool: ...
    def parse(self, text: str) -> Optional[ParsedExpression]: ...


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------
class _NamedSymbolStrategy:
    """Treat single tokens as named eml-math symbols (``pi``, ``phi`` …)."""

    name = "named-symbol"

    def applies(self, text: str) -> bool:
        return text.strip().isidentifier()

    def parse(self, text: str) -> Optional[ParsedExpression]:
        from eml_math import decompress, get, parse_eml_tree
        r = get(text)
        if r is None:
            return None
        eml = decompress(r, fmt="eml")
        tree = parse_eml_tree(f"EML: {eml}", pure_eml=True)
        normal_tree = parse_eml_tree(f"EML: {eml}", expand_eml=True)
        return ParsedExpression(
            eml=eml, tree=tree, normal_tree=normal_tree,
            info_line=f"named symbol  (complexity={r.complexity})",
            search_result=r,
        )


class _CompressStrategy:
    """Beam search via ``compress_str`` / ``compress_latex`` — best for
    single-variable math; produces a canonical EML form and a clean tree.
    """

    name = "compress"

    def applies(self, text: str) -> bool:
        return True

    def parse(self, text: str) -> Optional[ParsedExpression]:
        from eml_math import compress_latex, compress_str, decompress, parse_eml_tree
        try:
            r = compress_latex(text) if "\\" in text else compress_str(text)
        except Exception:                                  # noqa: BLE001
            return None
        if r is None:
            return None
        # Two views: what the user typed, and what compress shrank it to.
        # The pill switch chooses between them at render time.
        compressed_eml = decompress(r, fmt="eml")
        compressed_tree = parse_eml_tree(f"EML: {compressed_eml}", pure_eml=True)
        compressed_normal = parse_eml_tree(f"EML: {compressed_eml}", expand_eml=True)
        try:
            typed_tree = parse_eml_tree(f"EML: {text}", pure_eml=True)
            typed_normal = parse_eml_tree(f"EML: {text}", expand_eml=True)
        except Exception:                                  # noqa: BLE001
            typed_tree = compressed_tree
            typed_normal = compressed_normal
        return ParsedExpression(
            eml=text,
            tree=typed_tree,
            normal_tree=typed_normal,
            info_line=(
                f"via compress  (complexity={r.complexity}  error={r.error:.2e})"
            ),
            search_result=r,
            compressed_tree=compressed_tree,
            compressed_normal_tree=compressed_normal,
            compressed_latex=decompress(r, fmt="latex"),
        )


class _DirectParseStrategy:
    """Last-resort: feed the raw text into ``parse_eml_tree``.

    Catches multivariate expressions like ``(1/x) + (y**3)`` that the beam
    searcher rejects. The resulting tree may carry an ``unknown`` kind, but
    it still renders and round-trips through the same hover layer.
    """

    name = "direct"

    def applies(self, text: str) -> bool:
        return True

    def parse(self, text: str) -> Optional[ParsedExpression]:
        from eml_math import parse_eml_tree
        try:
            tree = parse_eml_tree(f"EML: {text}", pure_eml=True)
            normal_tree = parse_eml_tree(f"EML: {text}", expand_eml=True)
        except Exception:                                  # noqa: BLE001
            return None
        return ParsedExpression(
            eml=text, tree=tree, normal_tree=normal_tree,
            info_line="parsed directly (no compression)",
        )


# ---------------------------------------------------------------------------
# Composite
# ---------------------------------------------------------------------------
class MultiParser:
    def __init__(self, strategies: Iterable[ParseStrategy]) -> None:
        self._strategies: List[ParseStrategy] = list(strategies)

    def parse(self, text: str) -> Optional[ParsedExpression]:
        text = _normalize_input(text)
        for strat in self._strategies:
            if not strat.applies(text):
                continue
            result = strat.parse(text)
            if result is not None:
                return result
        return None


def default_parser() -> MultiParser:
    """Order: named-symbol shortcut → compress search → direct parse."""
    return MultiParser((_NamedSymbolStrategy(), _CompressStrategy(), _DirectParseStrategy()))
