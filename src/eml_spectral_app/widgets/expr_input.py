"""ExprInput — MDTextField with a right-click function-name context menu.

Replaces the calculator pad. The chip row above the input still shows the
famous-equation gallery; this widget adds a discoverable shortcut for the
math function names a user might forget how to type (``sin(``, ``log10(``,
``sqrt(`` and so on).

Implementation: override ``on_touch_down`` to intercept right-clicks
inside our bounds and pop an ``MDDropdownMenu`` whose ``caller`` is the
input field itself. Selecting an item inserts the fragment at the
current caret via ``insert_text``.
"""
from __future__ import annotations

from typing import List, Tuple

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield import MDTextField


# (display label, fragment to insert)
_DEFAULT_ITEMS: List[Tuple[str, str]] = [
    ("sin",     "sin("),
    ("cos",     "cos("),
    ("tan",     "tan("),
    ("ln",      "log("),
    ("log10",   "log10("),
    ("exp",     "exp("),
    ("sqrt",    "sqrt("),
    ("abs",     "abs("),
    ("π",       "pi"),
    ("e",       "e"),
    ("^ (power)", "**"),
    ("(",       "("),
    (")",       ")"),
    (",",       ", "),
]


class ExprInput(MDTextField):
    """Free-text math input with a right-click function menu."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self._menu: MDDropdownMenu = None  # type: ignore[assignment]

    # ------------------------------------------------------------------
    # input handling
    # ------------------------------------------------------------------
    def on_touch_down(self, touch):
        if (
            getattr(touch, "button", None) == "right"
            and self.collide_point(*touch.pos)
        ):
            self.focus = True
            self._open_context_menu()
            return True
        return super().on_touch_down(touch)

    # ------------------------------------------------------------------
    # menu plumbing
    # ------------------------------------------------------------------
    def _open_context_menu(self) -> None:
        if self._menu is None:
            self._menu = MDDropdownMenu(
                caller=self,
                items=self._build_menu_items(),
                width_mult=4,
                max_height="320dp",
            )
        else:
            self._menu.caller = self
        self._menu.open()

    def _build_menu_items(self) -> list:
        return [
            {
                "text": label,
                "viewclass": "OneLineListItem",
                "height": 36,
                "on_release": lambda f=fragment: self._insert_and_close(f),
            }
            for label, fragment in _DEFAULT_ITEMS
        ]

    def _insert_and_close(self, fragment: str) -> None:
        if self._menu is not None:
            self._menu.dismiss()
        # MDTextField inherits Kivy TextInput's insert_text — respects caret.
        self.insert_text(fragment)
