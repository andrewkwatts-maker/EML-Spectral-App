"""About screen — version + links."""
from __future__ import annotations

from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

from eml_spectral_app import __version__


class AboutScreen(MDScreen):
    version = StringProperty(__version__)
    eml_spectral_version = StringProperty("?")
    eml_math_version = StringProperty("?")

    def on_pre_enter(self) -> None:
        try:
            import eml_spectral
            self.eml_spectral_version = getattr(eml_spectral, "__version__", "?")
        except ImportError:
            self.eml_spectral_version = "(not installed)"
        try:
            import eml_math
            self.eml_math_version = getattr(eml_math, "__version__", "?")
        except ImportError:
            self.eml_math_version = "(not installed)"
