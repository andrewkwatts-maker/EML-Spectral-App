"""Constants screen — 167 names from `eml_spectral.list_constants` (31 spectral + 136 math)."""
from __future__ import annotations

from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.list import OneLineListItem
from kivymd.uix.screen import MDScreen


class ConstantsScreen(MDScreen):
    list_widget = ObjectProperty(None)
    detail_label = ObjectProperty(None)
    search_field = ObjectProperty(None)
    detail_text = StringProperty("Tap a constant to see its datasheet.")

    _all_names: list[str] = []

    def on_pre_enter(self) -> None:
        self._populate()

    def _populate(self, filter_text: str = "") -> None:
        if self.list_widget is None:
            return
        try:
            from eml_spectral import list_constants
        except ImportError:
            self.detail_text = "eml-spectral not installed"
            return

        if not self._all_names:
            try:
                self._all_names = list_constants()
            except Exception as exc:                  # noqa: BLE001
                self.detail_text = f"list_constants error: {exc}"
                return

        f = (filter_text or "").strip().lower()
        names = [n for n in self._all_names if f in n.lower()] if f else self._all_names

        self.list_widget.clear_widgets()
        for n in names:
            item = OneLineListItem(text=n)
            item.bind(on_release=lambda _w, name=n: self._show_detail(name))
            self.list_widget.add_widget(item)

    def filter_changed(self, value: str) -> None:
        self._populate(value)

    def _show_detail(self, name: str) -> None:
        try:
            from eml_spectral import Get
            d = Get(name)
            if not isinstance(d, dict):
                self.detail_text = repr(d)
                return
            lines = [f"Name:        {d.get('name', name)}"]
            for k in ("value", "formula", "kind", "description", "source",
                      "complexity", "eml_tree"):
                if k in d:
                    lines.append(f"{k.capitalize():12s} {d[k]}")
            self.detail_text = "\n".join(lines)
        except Exception as exc:                      # noqa: BLE001
            self.detail_text = f"{type(exc).__name__}: {exc}"
