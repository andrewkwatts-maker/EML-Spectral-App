"""KivyMD application root for EML-Spectral-App.

Loads every .kv file from ``kv/``, registers the eight screens. The
``Algebras`` screen uses tabs internally; spectral / spacetime / metric /
lattice / constants screens are top-level entries.
"""
from __future__ import annotations

from pathlib import Path

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

from eml_spectral_app import __version__

_KV_DIR = Path(__file__).parent / "kv"


class EMLSpectralApp(MDApp):
    title = f"EML-Spectral-App v{__version__}"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"

        for kv in sorted(_KV_DIR.glob("*.kv"), key=lambda p: p.name == "root.kv"):
            Builder.load_file(str(kv))

        from eml_spectral_app.screens.home import HomeScreen
        from eml_spectral_app.screens.spectral_flow import SpectralFlowScreen
        from eml_spectral_app.screens.spacetime import SpacetimeScreen
        from eml_spectral_app.screens.metrics import MetricsScreen
        from eml_spectral_app.screens.algebras import AlgebrasScreen
        from eml_spectral_app.screens.lattices import LatticesScreen
        from eml_spectral_app.screens.constants import ConstantsScreen
        from eml_spectral_app.screens.about import AboutScreen

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(SpectralFlowScreen(name="spectral_flow"))
        sm.add_widget(SpacetimeScreen(name="spacetime"))
        sm.add_widget(MetricsScreen(name="metrics"))
        sm.add_widget(AlgebrasScreen(name="algebras"))
        sm.add_widget(LatticesScreen(name="lattices"))
        sm.add_widget(ConstantsScreen(name="constants"))
        sm.add_widget(AboutScreen(name="about"))
        return sm


def run() -> None:
    EMLSpectralApp().run()


if __name__ == "__main__":
    run()
