"""Home screen — six big tiles into the rest of the app."""
from __future__ import annotations

from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

from eml_spectral_app import __version__


class HomeScreen(MDScreen):
    version = StringProperty(__version__)
    eml_spectral_version = StringProperty("?")
    has_rust = StringProperty("?")

    def on_pre_enter(self) -> None:
        try:
            import eml_spectral
            self.eml_spectral_version = getattr(eml_spectral, "__version__", "?")
            self.has_rust = "yes" if getattr(eml_spectral, "_HAS_RUST", False) else "no"
        except ImportError:
            self.eml_spectral_version = "(not installed)"
            self.has_rust = "—"
