"""Tree renderer that draws every node label at its layout position.

eml-math's ``flow_png`` is a visual "ribbon" renderer designed for the
docs site: it routes curves directly leaf → output and treats internal
``exp / ln / add / sub`` junctions as anonymous joints. That hides the
EML primitive structure that ``expand_eml=True`` produces.

This renderer instead consumes ``tree.layout()`` (the canvas-space layout
dict) and draws the structure faithfully: one labelled box per node,
straight-then-curved edges between every parent and child. The output
PNG matches the layout 1:1 so the hover layer keeps working.

Pure I/O on bytes — no Kivy import.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Colors / typography — chosen to match the dark theme + KivyMD primary.
# ---------------------------------------------------------------------------
_BG_COLOR = (28, 28, 34, 255)
_EDGE_COLOR = (130, 140, 155, 255)
_LABEL_TEXT = (240, 240, 245, 255)
_OUT_TEXT = (170, 175, 185, 255)
_NODE_DEFAULT = (80, 80, 92, 255)
_NODE_LEAF_BG = (60, 60, 72, 255)


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
    """Layout colors come as 3-tuples in 0..255; alpha defaults to 255."""
    rgb = node.get("color")
    if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
        return (int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)
    return _NODE_DEFAULT


# ---------------------------------------------------------------------------
def render_tree_with_labels(
    tree: Any,
    *,
    width: int = 720,
    height: int = 440,
    direction: str = "down",
    font_size: int = 13,
    out_label: str = "Out",
) -> Tuple[bytes, Dict[str, Any]]:
    """Return ``(png_bytes, layout_dict)`` for *tree*.

    Every node is drawn as a labelled rounded box at its layout position;
    every edge is drawn as a Bezier-style curve between parent and child
    centres. The layout is the same one used by the hover hit-tester, so
    cursor → node detection still works against this image.
    """
    layout = tree.layout(direction=direction, canvas=(width, height))
    canvas_w = float(layout["canvas"]["width"])
    canvas_h = float(layout["canvas"]["height"])

    img = Image.new("RGBA", (int(canvas_w), int(canvas_h)), _BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)

    # ── coordinate map: keep y as-is so the layout's "down" direction
    # places leaves at the top of the image and the output (root) at the
    # bottom — matching how the user reads top→down to follow inputs→output.
    def to_pixel(nx: float, ny: float) -> Tuple[float, float]:
        return float(nx), float(ny)

    # ── 1) draw edges as smooth bezier curves ─────────────────────────────
    nodes_by_id = {n["id"]: n for n in layout.get("nodes", [])}
    for e in layout.get("edges", []):
        a = nodes_by_id.get(e.get("from"))
        b = nodes_by_id.get(e.get("to"))
        if not a or not b:
            continue
        ax, ay = to_pixel(a["x"], a["y"])
        bx, by = to_pixel(b["x"], b["y"])
        # Vertical bezier with the control points on the midline — cleaner
        # than straight diagonals when the canvas is tall.
        mid_y = (ay + by) / 2.0
        pts = []
        steps = 24
        for i in range(steps + 1):
            t = i / steps
            # cubic bezier: (ax, ay) → (ax, mid_y) → (bx, mid_y) → (bx, by)
            x = (
                (1 - t) ** 3 * ax
                + 3 * (1 - t) ** 2 * t * ax
                + 3 * (1 - t) * t ** 2 * bx
                + t ** 3 * bx
            )
            y = (
                (1 - t) ** 3 * ay
                + 3 * (1 - t) ** 2 * t * mid_y
                + 3 * (1 - t) * t ** 2 * mid_y
                + t ** 3 * by
            )
            pts.append((x, y))
        edge_color = _EDGE_COLOR
        c = e.get("color")
        if isinstance(c, (list, tuple)) and len(c) >= 3:
            edge_color = (int(c[0]), int(c[1]), int(c[2]), 255)
        draw.line(pts, fill=edge_color, width=3, joint="curve")

    # ── 2) draw labelled boxes for every node ─────────────────────────────
    pad_x, pad_y = 8, 4
    for n in layout.get("nodes", []):
        cx, cy = to_pixel(n["x"], n["y"])
        text = str(n.get("label") or "?")
        tw, th = _measure(draw, text, font)
        x0 = cx - tw / 2 - pad_x
        y0 = cy - th / 2 - pad_y
        x1 = cx + tw / 2 + pad_x
        y1 = cy + th / 2 + pad_y
        # Leaves get the layout colour as a soft tint; internal nodes get a
        # neutral grey so the structure reads cleanly.
        bg = _node_color(n) if n.get("is_leaf") else _NODE_DEFAULT
        # Slight alpha so edges peek through.
        bg = (bg[0], bg[1], bg[2], 235)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=bg)
        draw.text((cx - tw / 2, cy - th / 2 - 1), text, fill=_LABEL_TEXT, font=font)

    # ── 3) optional output label below the root ──────────────────────────
    if out_label:
        # Find root: node with no outgoing edge from→ matching it
        outgoing = {e.get("from") for e in layout.get("edges", [])}
        roots = [n for n in layout.get("nodes", []) if n["id"] not in outgoing]
        for r in roots:
            cx, cy = to_pixel(r["x"], r["y"])
            label_w, label_h = _measure(draw, out_label, font)
            draw.text(
                (cx - label_w / 2, cy + 16),
                out_label, fill=_OUT_TEXT, font=font,
            )

    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue(), layout
