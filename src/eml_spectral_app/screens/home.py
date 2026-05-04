"""Single-page screen: free-type math input + live render with hover.

Pure orchestration. Parsing → :mod:`services.parser`. Format conversion →
:mod:`services.formats`. Hit-testing → :class:`widgets.svg_view.TreeImageView`.
LaTeX preview rendering → :class:`widgets.latex_preview.LatexPreview`.
The screen wires them together (debounce + clipboard + status text).
"""
from __future__ import annotations

from typing import Any, Optional

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen

from eml_spectral_app.services.famous import all_famous
from eml_spectral_app.services.formats import format_all, normal_math
from eml_spectral_app.services.parser import MultiParser, default_parser
from eml_spectral_app.widgets.latex_preview import LatexPreview
from eml_spectral_app.widgets.svg_view import TreeImageView


_DEBOUNCE_S = 0.25
_HOVER_HINT = "Hover a node in the tree to see its details"


class HomeScreen(MDScreen):
    name = StringProperty("home")

    expr_field = ObjectProperty(None)
    latex_preview: LatexPreview = ObjectProperty(None)
    tree_view: TreeImageView = ObjectProperty(None)
    chip_row = ObjectProperty(None)

    eml_field = ObjectProperty(None)
    latex_field = ObjectProperty(None)
    python_field = ObjectProperty(None)
    json_field = ObjectProperty(None)

    status = StringProperty("Type a math expression — `sin`/`cos`/etc are on the pad")
    hover_info = StringProperty(_HOVER_HINT)

    # Pill switch — False = show the user's typed expression. True = show
    # the compressed search result. LaTeX preview and EML graph swap
    # together so the two views stay in sync.
    show_compressed = BooleanProperty(False)

    _parser: MultiParser = None  # type: ignore[assignment]
    _parse_event: Any = None
    _last_parsed: Any = None

    def __init__(self, parser: Optional[MultiParser] = None, **kw):
        self._parser = parser or default_parser()
        super().__init__(**kw)

    # ------------------------------------------------------------------
    # bindings
    # ------------------------------------------------------------------
    def on_kv_post(self, base_widget) -> None:        # noqa: D401
        if self.expr_field is not None:
            self.expr_field.bind(text=self._on_text_changed)
        if self.tree_view is not None:
            self.tree_view.bind(on_node_hover=self._on_node_hover)
        self._populate_chip_row()
        self._schedule_parse()

    def _populate_chip_row(self) -> None:
        """Add one ``ExampleChip`` per famous equation in eml-math.

        Done in Python rather than KV so the catalogue stays in sync with
        ``eml_math.FAMOUS`` automatically — adding a new famous equation
        upstream surfaces here on next launch with no code change.
        """
        if self.chip_row is None:
            return
        from kivy.factory import Factory
        for label, expression, _ in all_famous():
            chip = Factory.ExampleChip()
            chip.text = label
            chip.expression = expression
            self.chip_row.add_widget(chip)

    # Pill switch handler — re-renders LaTeX + tree from whichever side
    # of the toggle is now selected.
    def set_compressed(self, on: bool) -> None:
        if self.show_compressed == on:
            return
        self.show_compressed = on
        self._schedule_parse()

    def _on_text_changed(self, _instance, _value) -> None:
        self._schedule_parse()

    def _schedule_parse(self) -> None:
        if self._parse_event is not None:
            self._parse_event.cancel()
        self._parse_event = Clock.schedule_once(lambda *_: self._parse_now(), _DEBOUNCE_S)

    # ------------------------------------------------------------------
    # parse + render
    # ------------------------------------------------------------------
    def _parse_now(self) -> None:
        text = self._current_text()
        if not text:
            self._clear_outputs("(empty)")
            return

        parsed = None
        try:
            parsed = self._parser.parse(text)
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"

        # The LaTeX preview renders even when the parser failed — sympy
        # often handles input the eml-math compressor can't.
        self._refresh_latex_preview(text, parsed)

        if parsed is None:
            self._clear_tree(f"Could not parse: {text!r}")
            return

        self._last_parsed = parsed
        try:
            formats = format_all(parsed)
        except Exception as exc:                       # noqa: BLE001
            self._clear_outputs(f"format: {exc}")
            return

        self._populate_outputs(formats)
        self.status = f"OK — {parsed.info_line}"
        # Pill switch: show the compressed tree when "Compressed" is on
        # (and a compressed view is actually available — multivariate input
        # has only the typed tree).
        active_tree = (
            parsed.compressed_tree
            if self.show_compressed and parsed.compressed_tree is not None
            else parsed.tree
        )
        self._render_tree(active_tree)

    def _refresh_latex_preview(self, text: str, parsed: Optional[Any]) -> None:
        if self.latex_preview is None:
            return
        # When the pill is on AND compress succeeded, render the compressed
        # LaTeX directly; otherwise fall back to the typed-text path which
        # the LatexPreview widget already knows how to handle.
        if (self.show_compressed and parsed is not None
                and parsed.compressed_latex):
            from eml_spectral_app.services.latex_renderer import (
                render_latex_png,
            )
            from io import BytesIO
            from kivy.core.image import Image as CoreImage
            png = render_latex_png(parsed.compressed_latex)
            if png:
                self.latex_preview.texture = CoreImage(BytesIO(png), ext="png").texture
                return
        self.latex_preview.set_expression(text, parsed)

    def _populate_outputs(self, formats: dict) -> None:
        for field, key in (
            (self.eml_field, "eml"),
            (self.latex_field, "latex"),
            (self.python_field, "python"),
            (self.json_field, "json"),
        ):
            if field is not None:
                field.text = formats[key]

    def _render_tree(self, tree) -> None:
        if self.tree_view is None or tree is None:
            return
        try:
            self.tree_view.show_tree(tree)
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{self.status}    [render skipped: {exc}]"

    def _clear_tree(self, status: str) -> None:
        self.status = status
        if self.tree_view is not None:
            self.tree_view.show_tree(None)
        for f in (self.eml_field, self.latex_field, self.python_field, self.json_field):
            if f is not None:
                f.text = ""
        self.hover_info = _HOVER_HINT
        self._last_parsed = None

    def _clear_outputs(self, status: str) -> None:
        self._clear_tree(status)
        if self.latex_preview is not None:
            self.latex_preview.texture = None

    # ------------------------------------------------------------------
    # hover
    # ------------------------------------------------------------------
    def _on_node_hover(self, _view, node) -> None:
        self.hover_info = _format_hover(node)

    # ------------------------------------------------------------------
    # example chips: replace input with a curated formula
    # ------------------------------------------------------------------
    def load_example(self, expression: str) -> None:
        if self.expr_field is not None:
            self.expr_field.text = expression

    # ------------------------------------------------------------------
    # calculator-pad
    # ------------------------------------------------------------------
    def insert(self, fragment: str) -> None:
        if self.expr_field is None or not fragment:
            return
        self.expr_field.focus = True
        self.expr_field.insert_text(fragment)

    def backspace(self) -> None:
        if self.expr_field is None:
            return
        self.expr_field.focus = True
        self.expr_field.do_backspace()

    def clear(self) -> None:
        if self.expr_field is not None:
            self.expr_field.text = ""

    # ------------------------------------------------------------------
    # compress button — returns "normal math" (no `math.` prefix, no
    # lambda header). Bails when the compressor can't find a formula.
    # ------------------------------------------------------------------
    def compress_now(self) -> None:
        text = self._current_text()
        if not text:
            self.status = "Empty expression — nothing to compress"
            return
        try:
            from eml_math import compress_latex, compress_str
            r = compress_latex(text) if "\\" in text else compress_str(text)
        except Exception as exc:                       # noqa: BLE001
            self.status = f"Compress: {type(exc).__name__}: {exc}"
            return
        if r is None:
            self.status = "Compressor found no formula — leaving input as-is"
            return
        self.expr_field.text = r.formula
        # _on_text_changed reruns the live parse + render automatically.

    # ------------------------------------------------------------------
    # clipboard
    # ------------------------------------------------------------------
    def copy_field(self, field) -> None:
        if field is None:
            return
        Clipboard.copy(field.text or "")
        self.status = "Copied to clipboard"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _current_text(self) -> str:
        return (self.expr_field.text if self.expr_field else "").strip()


def _format_hover(node) -> str:
    if node is None:
        return _HOVER_HINT
    label = node.get("label") or "?"
    if len(label) > 40:
        label = label[:37] + "…"
    role = "leaf" if node.get("is_leaf") else "internal"
    return (
        f"node {node.get('id')}  "
        f"kind={node.get('kind')}  "
        f"depth={node.get('depth')}  "
        f"{role}  ·  {label}"
    )
