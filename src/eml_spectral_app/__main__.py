"""Entry point: ``python -m eml_spectral_app`` or via the ``eml-spectral-app`` script."""
from __future__ import annotations


def main() -> None:
    from eml_spectral_app.app import EMLSpectralApp
    EMLSpectralApp().run()


if __name__ == "__main__":
    main()
