"""KivyMD application root for EML-Spectral-App.

Single-page calculator + EML renderer (mirroring the math-app). The whole
UI is ``HomeScreen``, loaded from ``kv/home.kv``.
"""
from __future__ import annotations

from pathlib import Path

from kivy.lang import Builder
from kivymd.app import MDApp

from eml_spectral_app import __version__
# Eager imports so the Factory knows the custom widgets before kv parses.
from eml_spectral_app.widgets.latex_preview import LatexPreview  # noqa: F401
from eml_spectral_app.widgets.svg_view import TreeImageView  # noqa: F401

_KV_DIR = Path(__file__).parent / "kv"


class EMLSpectralApp(MDApp):
    title = f"EML-Spectral-App v{__version__}"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"

        Builder.load_file(str(_KV_DIR / "root.kv"))
        Builder.load_file(str(_KV_DIR / "home.kv"))

        from eml_spectral_app.screens.home import HomeScreen
        return HomeScreen()


def run() -> None:
    EMLSpectralApp().run()


if __name__ == "__main__":
    run()
