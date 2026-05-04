"""Convert math expression strings to typeset LaTeX PNGs.

Two stages, each swappable:

    text  ──► ``to_latex_source(text, parsed)``  ──► LaTeX string
                                                          │
              ``render_latex_png(latex, …)``  ──► PNG bytes

LaTeX generation always goes through eml-math — the app stays "dumb" and
the library is the single source of truth for math syntax. Rendering uses
matplotlib's mathtext via the Agg backend (no display, no window) so the
PNG renders inside the bundled exe.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Optional, Tuple

# matplotlib must run head-less inside the bundled exe.
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt   # noqa: E402


def to_latex_source(text: str, parsed: Optional[Any] = None) -> Optional[str]:
    """Best-effort text → LaTeX. Returns ``None`` on total failure.

    Order of preference:
      1. Parsed tree's :py:meth:`EMLTreeNode.to_latex` (fastest, exact).
      2. ``decompress(search_result, fmt='latex')`` for backwards compat
         when only a SearchResult is at hand.
      3. A last-chance ``parse_eml_tree`` to cover the case where the
         caller didn't pass a parsed view (e.g. text edits during the
         first paint cycle).
    """
    if parsed is not None and getattr(parsed, "tree", None) is not None:
        try:
            return parsed.tree.to_latex()
        except Exception:                              # noqa: BLE001
            pass
    if parsed is not None and getattr(parsed, "search_result", None) is not None:
        from eml_math import decompress
        try:
            return decompress(parsed.search_result, fmt="latex")
        except Exception:                              # noqa: BLE001
            pass

    candidate = (text or "").strip().replace("^", "**")
    if not candidate:
        return None
    from eml_math import parse_eml_tree
    try:
        tree = parse_eml_tree(f"EML: {candidate}", expand_eml=False)
        return tree.to_latex()
    except Exception:                                  # noqa: BLE001
        return None


def render_latex_png(
    latex: str,
    *,
    fontsize: int = 26,
    color: str = "white",
    figsize: Tuple[float, float] = (8.0, 1.4),
    dpi: int = 140,
) -> Optional[bytes]:
    """Render a LaTeX string to PNG bytes (transparent background)."""
    if not latex:
        return None
    fig = plt.figure(figsize=figsize, dpi=dpi)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.axis("off")
    try:
        ax.text(
            0.5, 0.5, f"${latex}$",
            ha="center", va="center",
            fontsize=fontsize, color=color,
        )
        buf = BytesIO()
        fig.savefig(buf, format="png", transparent=True, bbox_inches="tight",
                    pad_inches=0.08)
        return buf.getvalue()
    except Exception:                                  # noqa: BLE001
        return None
    finally:
        plt.close(fig)
