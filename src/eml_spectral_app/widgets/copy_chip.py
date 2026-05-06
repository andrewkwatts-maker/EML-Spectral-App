"""CopyChip — title-as-trigger button with hover preview tooltip.

The bottom output strip used to be four cards with the format text
visible inline; that crowded the UI when the JSON dump grew. ``CopyChip``
replaces each card with a single chip whose label *is* the trigger:
clicking it copies the format string to the clipboard, and hovering
shows the content as an MDTooltip so the user can see exactly what
they're about to grab.

Implementation note: KV doesn't allow multi-inheritance via the ``+``
operator, so we compose ``MDTooltip`` + ``MDFlatButton`` here in Python
and let the KV file style the resulting class via ``<CopyChip>``.
"""
from __future__ import annotations

from kivy.properties import StringProperty
from kivymd.uix.button import MDFlatButton
from kivymd.uix.tooltip import MDTooltip


class CopyChip(MDTooltip, MDFlatButton):
    """Button with a hover-tooltip showing the *preview* it will copy."""

    preview = StringProperty("")
