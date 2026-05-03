"""Smoke tests — import surfaces, verify each screen class loads."""
from __future__ import annotations

import importlib

import pytest


def test_app_import():
    mod = importlib.import_module("eml_spectral_app.app")
    assert hasattr(mod, "EMLSpectralApp")


def test_version_is_string():
    import eml_spectral_app
    v = eml_spectral_app.__version__
    assert isinstance(v, str)
    assert v.count(".") >= 2


@pytest.mark.parametrize("name", [
    "home", "spectral_flow", "spacetime", "metrics",
    "algebras", "lattices", "constants", "about",
])
def test_screen_classes_import(name):
    mod = importlib.import_module(f"eml_spectral_app.screens.{name}")
    expected = {
        "home": "HomeScreen",
        "spectral_flow": "SpectralFlowScreen",
        "spacetime": "SpacetimeScreen",
        "metrics": "MetricsScreen",
        "algebras": "AlgebrasScreen",
        "lattices": "LatticesScreen",
        "constants": "ConstantsScreen",
        "about": "AboutScreen",
    }[name]
    assert hasattr(mod, expected), f"{name} module missing {expected}"


def test_app_class_instantiable():
    """Build an app object without calling .run() (no display required)."""
    from eml_spectral_app.app import EMLSpectralApp
    app = EMLSpectralApp()
    assert app.title.startswith("EML-Spectral-App")
