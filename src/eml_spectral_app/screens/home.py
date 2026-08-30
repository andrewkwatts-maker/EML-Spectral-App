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


class HomeScreen(MDScreen):
    name = StringProperty("home")

    expr_field = ObjectProperty(None)
    latex_preview_normal: LatexPreview = ObjectProperty(None)
    latex_preview_eml: LatexPreview = ObjectProperty(None)
    tree_view: TreeImageView = ObjectProperty(None)
    chip_row = ObjectProperty(None)
    # eml_field / latex_field / python_field / json_field were the inline
    # output fields in the previous layout; replaced by the four CopyChip
    # buttons that read root.copy_eml / .copy_latex / .copy_python /
    # .copy_json. Properties removed deliberately.

    # Plain string properties — the bottom output strip uses CopyChip
    # buttons keyed on these instead of inline TextField widgets.
    copy_eml = StringProperty("")
    copy_latex = StringProperty("")
    copy_python = StringProperty("")
    copy_json = StringProperty("")

    status = StringProperty("Type a math expression — right-click the input for function names")

    # Pill switch — False = show the user's typed expression. True = show
    # the compressed search result. LaTeX preview and EML graph swap
    # together so the two views stay in sync.
    show_compressed = BooleanProperty(False)

    # Tree orientation — one of "down" / "up" / "left" / "right". The
    # arrow buttons above the graph card flip this; TreeImageView reads it
    # via its own ``direction`` property.
    tree_direction = StringProperty("down")
    # Topology-only mode: hide every node's label box (hover still works).
    show_labels = BooleanProperty(True)
    # When on, numeric literals (> 1) are expanded into EML sub-graphs
    # via eml_math.expand_numeric_constants — useful for showing the
    # user how a value like 7 is built from EML primitives.
    expand_constants = BooleanProperty(False)

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

    # Direction switcher handler — flips the tree's flow.
    def set_direction(self, direction: str) -> None:
        if direction == self.tree_direction:
            return
        self.tree_direction = direction
        if self.tree_view is not None:
            self.tree_view.direction = direction
        self._schedule_parse()

    # Label-visibility toggle — hides the per-node label boxes; the hover
    # layer keeps working because layout dicts still carry subexpr fields.
    def toggle_labels(self) -> None:
        self.show_labels = not self.show_labels
        if self.tree_view is not None:
            self.tree_view.show_labels = self.show_labels
        self._schedule_parse()

    # "Expand constants" toggle — replaces each numeric literal > 1 with
    # its EML-compressed sub-graph so the user can see how the value is
    # built from EML primitives.
    def toggle_expand_constants(self) -> None:
        self.expand_constants = not self.expand_constants
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
            parsed = self._parser.parse(text, expand_constants=self.expand_constants)
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
        """Update both LaTeX panes — left = normal-math (patterns matched),
        right = literal EML primitive form."""
        if parsed is None:
            if self.latex_preview_normal is not None:
                self.latex_preview_normal.set_expression(text, None)
            if self.latex_preview_eml is not None:
                self.latex_preview_eml.set_latex("")
            return

        compressed = self.show_compressed and parsed.compressed_tree is not None
        normal_tree = parsed.compressed_normal_tree if compressed else parsed.normal_tree
        eml_tree = parsed.compressed_tree if compressed else parsed.tree

        # Normal-math pane: prefer the parallel expand_eml tree's to_latex
        # (mul/div/pow patterns recognised). Fall back to the
        # text→LaTeX path used previously.
        if self.latex_preview_normal is not None:
            try:
                normal_latex = normal_tree.to_latex() if normal_tree is not None else ""
            except Exception:                              # noqa: BLE001
                normal_latex = ""
            if normal_latex:
                self.latex_preview_normal.set_latex(normal_latex)
            else:
                self.latex_preview_normal.set_expression(text, parsed)

        # EML pane: literal pure-EML LaTeX from the graph's tree.
        if self.latex_preview_eml is not None:
            try:
                eml_latex = eml_tree.to_latex() if eml_tree is not None else ""
            except Exception:                              # noqa: BLE001
                eml_latex = ""
            self.latex_preview_eml.set_latex(eml_latex)

    def _populate_outputs(self, formats: dict) -> None:
        # Stash the format strings on the screen — the CopyChip buttons
        # in the bottom strip pick these up via root.copy_eml etc.
        self.copy_eml = formats["eml"]
        self.copy_latex = formats["latex"]
        self.copy_python = formats["python"]
        self.copy_json = formats["json"]

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
        self.copy_eml = ""
        self.copy_latex = ""
        self.copy_python = ""
        self.copy_json = ""
        self._last_parsed = None

    def _clear_outputs(self, status: str) -> None:
        self._clear_tree(status)
        if self.latex_preview_normal is not None:
            self.latex_preview_normal.texture = None
        if self.latex_preview_eml is not None:
            self.latex_preview_eml.texture = None

    # ------------------------------------------------------------------
    # hover — drives the two LaTeX preview panes. Hovering a node swaps
    # both panes to that subtree's normal-math + literal-EML LaTeX;
    # leaving the graph reverts them to the whole-formula view.
    # ------------------------------------------------------------------
    def _on_node_hover(self, _view, node) -> None:
        if node is None:
            self._refresh_latex_preview(self._current_text(), self._last_parsed)
            self.status = (
                f"OK — {self._last_parsed.info_line}"
                if self._last_parsed is not None
                else self.status
            )
            return
        normal = node.get("subexpr_normal") or ""
        eml = node.get("subexpr_eml") or ""
        if self.latex_preview_normal is not None:
            self.latex_preview_normal.set_latex(normal)
        if self.latex_preview_eml is not None:
            self.latex_preview_eml.set_latex(eml)
        label = node.get("label") or "?"
        kind = node.get("kind") or "?"
        depth = node.get("depth")
        self.status = f"hover: {node.get('id')}  kind={kind}  depth={depth}  label={label}"

    # ------------------------------------------------------------------
    # example chips: replace input with a curated formula
    # ------------------------------------------------------------------
    def load_example(self, expression: str) -> None:
        if self.expr_field is not None:
            self.expr_field.text = expression

    # ------------------------------------------------------------------
    # input field
    # ------------------------------------------------------------------
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
    def copy_text(self, text: str, label: str = "") -> None:
        """Copy *text* to the clipboard. Shows a status pip with *label*."""
        Clipboard.copy(text or "")
        self.status = f"Copied {label} to clipboard" if label else "Copied"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _current_text(self) -> str:
        return (self.expr_field.text if self.expr_field else "").strip()


