"""LatexPreview — a thin Kivy ``Image`` that displays a rendered LaTeX PNG.

Owns no parsing logic. The screen pushes raw expression text into
:meth:`set_expression`; the widget calls
:func:`services.latex_renderer.to_latex_source` then ``render_latex_png``
and turns the bytes into a Kivy texture. Empty / unparseable input clears
the texture instead of crashing.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Optional

from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image as KivyImage

from eml_spectral_app.services.latex_renderer import render_latex_png, to_latex_source


class LatexPreview(KivyImage):
    """Image widget that always shows the most recent LaTeX render."""

    def set_expression(self, text: str, parsed: Optional[Any] = None) -> None:
        latex = to_latex_source(text, parsed)
        png = render_latex_png(latex) if latex else None
        if not png:
            self.texture = None
            return
        self.texture = CoreImage(BytesIO(png), ext="png").texture
