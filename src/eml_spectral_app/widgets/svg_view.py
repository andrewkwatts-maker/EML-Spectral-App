"""TreeImageView — renders an EML tree to a Kivy texture and reports hovers.

Render path: ``EMLTreeNode → eml_math.flow_png → PNG bytes →
kivy.core.image.CoreImage → texture → kivy.uix.image.Image``.

Hover path: cursor → widget-local coords → image-rect-local coords →
layout-canvas coords → :func:`services.hit_test.nearest_node`. The widget
owns coordinate transforms (Kivy concern) and delegates the actual
"which node is nearest" question to a pure function (SRP).

The PNG bytes are kept verbatim, so the copy / export path emits exactly
what eml-math drew.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Optional

from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.image import Image as KivyImage

from eml_spectral_app.services.hit_test import nearest_node, project_widget_to_canvas
from eml_spectral_app.services.tree_render import render_tree_with_labels


class TreeImageView(KivyImage):
    """Kivy ``Image`` that renders an EML tree PNG and dispatches hovers.

    Events
    ------
    on_node_hover(node):
        Fired when the hovered node changes. ``node`` is the layout-node
        dict (eml-math ``eml-layout/v1`` schema) or ``None`` when the
        cursor leaves the image / no node is close enough.
    """

    __events__ = ("on_node_hover",)

    direction = StringProperty("down")
    edge_style = StringProperty("curve")
    width_px = NumericProperty(720)
    height_px = NumericProperty(440)
    # When False the renderer draws topology-only (dots, no labels). The
    # hover layer keeps working — useful for users who just want the
    # shape and rely on hover for details.
    show_labels = BooleanProperty(True)

    _last_tree: Optional[Any] = None
    _last_png: Optional[bytes] = None
    _last_layout: Optional[Dict[str, Any]] = None
    _hover_id: Optional[str] = None

    def __init__(self, **kw):
        super().__init__(**kw)
        Window.bind(mouse_pos=self._on_mouse_pos)

    # ------------------------------------------------------------------
    # rendering
    # ------------------------------------------------------------------
    def show_tree(self, tree: Any, **flow_opts: Any) -> None:
        """Render *tree* (every node label visible) and capture the layout
        dict for hover hit-testing."""
        if tree is None:
            self._reset()
            return

        # render_tree_with_labels composites flow_png with a label overlay
        # for every non-leaf node — flow_png alone hides internal labels.
        png, layout = render_tree_with_labels(
            tree,
            width=int(self.width_px),
            height=int(self.height_px),
            direction=self.direction,
            show_labels=self.show_labels,
        )
        self._last_tree = tree
        self._last_png = png
        self._last_layout = layout
        self.texture = CoreImage(BytesIO(png), ext="png").texture

    def show_png_bytes(self, png: bytes) -> None:
        """Display arbitrary PNG bytes (no layout — hover is disabled)."""
        if not png:
            self._reset()
            return
        self._last_png = png
        self._last_layout = None
        self.texture = CoreImage(BytesIO(png), ext="png").texture

    def _reset(self) -> None:
        self.texture = None
        self._last_tree = None
        self._last_png = None
        self._last_layout = None
        self._set_hover(None)

    @property
    def last_png(self) -> Optional[bytes]:
        return self._last_png

    @property
    def last_tree(self):
        return self._last_tree

    # ------------------------------------------------------------------
    # hover hit-test
    # ------------------------------------------------------------------
    def on_node_hover(self, node: Optional[Dict[str, Any]]) -> None:
        """Default handler — KV listeners override this."""

    def _set_hover(self, node: Optional[Dict[str, Any]]) -> None:
        new_id = node["id"] if node else None
        if new_id == self._hover_id:
            return
        self._hover_id = new_id
        self.dispatch("on_node_hover", node)

    def _image_rect(self) -> Optional[tuple]:
        """``(ox, oy, w, h)`` of the actual image inside this widget,
        accounting for ``keep_ratio`` letterboxing.
        """
        if self.texture is None:
            return None
        nw, nh = self.norm_image_size
        if nw <= 0 or nh <= 0:
            return None
        ox = self.x + (self.width - nw) / 2.0
        oy = self.y + (self.height - nh) / 2.0
        return ox, oy, nw, nh

    def _on_mouse_pos(self, _win, pos) -> None:
        if self._last_layout is None or not self.get_root_window():
            return
        local = self.to_widget(*pos, relative=False)
        rect = self._image_rect()
        if rect is None:
            self._set_hover(None)
            return
        ox, oy, nw, nh = rect
        ix = local[0] - ox
        iy = local[1] - oy
        if not (0.0 <= ix <= nw and 0.0 <= iy <= nh):
            self._set_hover(None)
            return
        canvas_pt = project_widget_to_canvas(self._last_layout, ix, iy, nw, nh)
        if canvas_pt is None:
            self._set_hover(None)
            return
        self._set_hover(nearest_node(self._last_layout, *canvas_pt))
