"""Tree renderer that draws every node label at its layout position.

eml-math's ``flow_png`` is a visual "ribbon" renderer designed for the
docs site: it routes curves directly leaf → output and treats internal
``exp / ln / add / sub`` junctions as anonymous joints. That hides the
EML primitive structure that ``expand_eml=True`` produces.

This renderer instead consumes ``tree.layout()`` (the canvas-space layout
dict) and draws the structure faithfully:

  - one rounded label box per node at its layout position,
  - smooth bezier edges between every parent and child, with control
    points oriented for the layout's flow direction (vertical for
    "down"/"up", horizontal for "left"/"right"),
  - 2× supersampling so edges and label boxes look crisp on the dark
    theme — PIL.ImageDraw.line is aliased by default, so we draw at 2×
    and resample down with LANCZOS for free anti-aliasing,
  - optional label hiding (``show_labels=False``) — handy for users who
    just want to see the topology and rely on hover for details.

Pure I/O on bytes — no Kivy import.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Colors / typography — chosen to match the dark theme + KivyMD primary.
# ---------------------------------------------------------------------------
_BG_COLOR = (28, 28, 34, 255)
_EDGE_COLOR = (130, 140, 155, 255)
_LABEL_TEXT = (240, 240, 245, 255)
_OUT_TEXT = (170, 175, 185, 255)
_NODE_DEFAULT = (80, 80, 92, 255)


def _load_font(size: int) -> ImageFont.ImageFont:
    for name in (
        "segoeui.ttf",                 # Windows
        "DejaVuSans.ttf",              # Linux / bundled with matplotlib
        "Arial.ttf",
        "Helvetica.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _measure(draw: ImageDraw.ImageDraw, text: str,
             font: ImageFont.ImageFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _node_color(node: Dict[str, Any]) -> Tuple[int, int, int, int]:
    rgb = node.get("color")
    if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
        return (int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)
    return _NODE_DEFAULT


def _attach_subexpressions(tree: Any, layout: Dict[str, Any]) -> None:
    """Walk the tree DFS pre-order (matching ``compute_layout``) and stash
    the subtree's literal pure-EML LaTeX onto each layout node so the
    hover layer can show what subexpression sits at that point."""
    layout_nodes = layout.get("nodes") or []
    if not layout_nodes:
        return
    flat: List[Any] = []
    def walk(n: Any) -> None:
        flat.append(n)
        for c in getattr(n, "children", ()) or ():
            walk(c)
    walk(tree)
    if len(flat) != len(layout_nodes):
        return
    for n, t in zip(layout_nodes, flat):
        try:
            n["subexpr_eml"] = t.to_latex()
            n["subexpr_normal"] = pure_eml_to_normal_latex(t)
        except Exception:                                  # noqa: BLE001
            n["subexpr_eml"] = n.get("label", "")
            n["subexpr_normal"] = n.get("label", "")


# ---------------------------------------------------------------------------
# Pure-EML subtree → readable normal-math LaTeX
#
# eml-math's ``EMLTreeNode.to_latex`` only pattern-matches when run on an
# expand_eml=True tree (where exp/ln/add/sub primitives are visible). For a
# pure_eml tree (every internal node labelled ``eml``) it falls back to the
# verbose nested form. This walker recognises the sentinel-collapsed cases
# so per-node hover sees something readable instead of the full primitive
# chain at every level.
# ---------------------------------------------------------------------------
def pure_eml_to_normal_latex(node: Any) -> str:
    if not getattr(node, "children", None):
        label = (node.label or "").strip()
        if label == "0":
            return "0"
        if label == "1":
            return "1"
        return label
    op = node.label
    children = node.children
    if op == "eml" and len(children) == 2:
        L, R = children
        l_is_one = (R.label == "1" and not getattr(R, "children", None))
        r_is_zero = (L.label == "0" and not getattr(L, "children", None))
        # eml(L, 1) = exp(L) - ln(1) = exp(L)
        if R.label == "1" and not getattr(R, "children", None):
            return rf"e^{{{pure_eml_to_normal_latex(L)}}}"
        # eml(0, R) = exp(0) - ln(R)... ⊥ collapses exp(⊥) = 0, giving -ln(R)
        if L.label == "0" and not getattr(L, "children", None):
            return rf"-\ln\!\left({pure_eml_to_normal_latex(R)}\right)"
        # general eml(L, R) = exp(L) - ln(R)
        return (
            rf"\left(e^{{{pure_eml_to_normal_latex(L)}}}"
            rf" - \ln\!\left({pure_eml_to_normal_latex(R)}\right)\right)"
        )
    # Compound / unknown — emit a callable form.
    args = [pure_eml_to_normal_latex(c) for c in children]
    return rf"\mathrm{{{op}}}\!\left({', '.join(args)}\right)"


# ---------------------------------------------------------------------------
def render_tree_with_labels(
    tree: Any,
    *,
    width: int = 720,
    height: int = 440,
    direction: str = "down",
    font_size: int = 13,
    show_labels: bool = True,
    out_label: str = "Out",
    supersample: int = 2,
) -> Tuple[bytes, Dict[str, Any]]:
    """Return ``(png_bytes, layout_dict)`` for *tree*.

    Each layout node receives ``subexpr_eml`` and ``subexpr_normal``
    LaTeX strings used by the hover overlay.

    ``supersample`` draws at N× the layout canvas size and resamples down
    with LANCZOS so the bezier curves and rounded boxes are anti-aliased
    on output (PIL.ImageDraw is aliased by default).
    """
    layout = tree.layout(direction=direction, canvas=(width, height))
    canvas_w = float(layout["canvas"]["width"])
    canvas_h = float(layout["canvas"]["height"])
    _attach_subexpressions(tree, layout)

    s = max(1, int(supersample))
    img_w = int(canvas_w * s)
    img_h = int(canvas_h * s)
    img = Image.new("RGBA", (img_w, img_h), _BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size * s)

    def to_pixel(nx: float, ny: float) -> Tuple[float, float]:
        # Layout coords are y-down (compute_layout fills y from 0 → canvas_h
        # with the root at the trailing edge of the chosen direction).
        return float(nx) * s, float(ny) * s

    # ── 1) draw edges with direction-aware bezier control points ─────────
    nodes_by_id = {n["id"]: n for n in layout.get("nodes", [])}
    horizontal = direction in ("left", "right")
    for e in layout.get("edges", []):
        a = nodes_by_id.get(e.get("from"))
        b = nodes_by_id.get(e.get("to"))
        if not a or not b:
            continue
        ax, ay = to_pixel(a["x"], a["y"])
        bx, by = to_pixel(b["x"], b["y"])
        # Control points sit on the midline along the *flow* axis. For
        # vertical flow that's mid_y; for horizontal flow that's mid_x.
        if horizontal:
            mid = (ax + bx) / 2.0
            c1 = (mid, ay)
            c2 = (mid, by)
        else:
            mid = (ay + by) / 2.0
            c1 = (ax, mid)
            c2 = (bx, mid)
        steps = 24
        pts: List[Tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            u = 1 - t
            x = (u ** 3) * ax + 3 * (u ** 2) * t * c1[0] + 3 * u * (t ** 2) * c2[0] + (t ** 3) * bx
            y = (u ** 3) * ay + 3 * (u ** 2) * t * c1[1] + 3 * u * (t ** 2) * c2[1] + (t ** 3) * by
            pts.append((x, y))
        edge_color = _EDGE_COLOR
        c = e.get("color")
        if isinstance(c, (list, tuple)) and len(c) >= 3:
            edge_color = (int(c[0]), int(c[1]), int(c[2]), 255)
        draw.line(pts, fill=edge_color, width=int(3 * s), joint="curve")

    # ── 2) draw labelled boxes (or just dots when labels hidden) ─────────
    pad_x, pad_y = 8 * s, 4 * s
    for n in layout.get("nodes", []):
        cx, cy = to_pixel(n["x"], n["y"])
        if show_labels:
            text = str(n.get("label") or "?")
            tw, th = _measure(draw, text, font)
            x0 = cx - tw / 2 - pad_x
            y0 = cy - th / 2 - pad_y
            x1 = cx + tw / 2 + pad_x
            y1 = cy + th / 2 + pad_y
            bg = _node_color(n) if n.get("is_leaf") else _NODE_DEFAULT
            bg = (bg[0], bg[1], bg[2], 235)
            draw.rounded_rectangle((x0, y0, x1, y1), radius=int(6 * s), fill=bg)
            # Use the textbbox to place the text precisely centred —
            # pre-3.10 PIL's anchor argument is unreliable on Windows
            # bundled fonts, so we measure and offset manually.
            draw.text(
                (cx - tw / 2, cy - th / 2),
                text,
                fill=_LABEL_TEXT,
                font=font,
            )
        else:
            # Topology-only mode: small filled dot per node.
            r = int(4 * s)
            bg = _node_color(n) if n.get("is_leaf") else _NODE_DEFAULT
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg)

    # ── 3) "Out" label at the root (the node with no outgoing edge) ──────
    if out_label:
        outgoing = {e.get("from") for e in layout.get("edges", [])}
        roots = [n for n in layout.get("nodes", []) if n["id"] not in outgoing]
        out_font = _load_font(int(font_size * s * 1.0))
        for r in roots:
            cx, cy = to_pixel(r["x"], r["y"])
            label_w, label_h = _measure(draw, out_label, out_font)
            # Place the label below or beside the root depending on flow.
            if direction == "up":
                draw.text((cx - label_w / 2, cy - 28 * s - label_h),
                          out_label, fill=_OUT_TEXT, font=out_font)
            elif direction == "left":
                draw.text((cx - 24 * s - label_w, cy - label_h / 2),
                          out_label, fill=_OUT_TEXT, font=out_font)
            elif direction == "right":
                draw.text((cx + 24 * s, cy - label_h / 2),
                          out_label, fill=_OUT_TEXT, font=out_font)
            else:                                          # "down" (default)
                draw.text((cx - label_w / 2, cy + 18 * s),
                          out_label, fill=_OUT_TEXT, font=out_font)

    if s > 1:
        img = img.resize(
            (int(canvas_w), int(canvas_h)), resample=Image.LANCZOS,
        )
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue(), layout
