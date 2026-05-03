"""Lattices screen — E₈ root system + Leech lattice summary."""
from __future__ import annotations

from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen


class LatticesScreen(MDScreen):
    output_label = ObjectProperty(None)
    status = StringProperty("Pick a lattice")

    def show_e8(self) -> None:                        # noqa: D401
        try:
            from eml_spectral import e8_lattice_points, Get
            pts = e8_lattice_points()
            d_min = Get("e8_min_norm")
            d_kiss = Get("e8_kissing")
            d_dim = Get("octonion_dim")
            sample = "\n".join(
                f"  {i:>3}: {getattr(p, 'coords', p)}"
                for i, p in enumerate(pts[:8])
            )
            self.output_label.text = "\n".join([
                "E₈ root lattice",
                f"  ambient dimension : 8",
                f"  min vector norm   : {d_min['value']}  ({d_min['formula']})",
                f"  kissing number    : {d_kiss['value']}  ({d_kiss['formula']})",
                f"  total points loaded: {len(pts)}",
                "",
                "First 8 root vectors:",
                sample,
            ])
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"

    def show_leech(self) -> None:                     # noqa: D401
        try:
            from eml_spectral import leech_lattice_points, Get
            pts = leech_lattice_points()
            d_min = Get("leech_min_norm")
            d_kiss = Get("leech_kissing")
            self.output_label.text = "\n".join([
                "Leech lattice (24-dim sphere packing)",
                f"  ambient dimension : 24",
                f"  min vector norm   : {d_min['value']}  ({d_min['formula']})",
                f"  kissing number    : {d_kiss['value']}  (24-D sphere-packing optimum)",
                f"  total points loaded: {len(pts)}",
            ])
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"
