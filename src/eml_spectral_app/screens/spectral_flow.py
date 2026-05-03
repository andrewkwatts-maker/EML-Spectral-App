"""Spectral flow screen — iterate Phi from a seed EMLPoint."""
from __future__ import annotations

from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen


class SpectralFlowScreen(MDScreen):
    x_field = ObjectProperty(None)
    y_field = ObjectProperty(None)
    steps_field = ObjectProperty(None)
    output_label = ObjectProperty(None)
    invariant_label = ObjectProperty(None)
    status = StringProperty("Set seed (x, y) and step count, hit Run")

    def run_flow(self) -> None:                       # noqa: D401
        try:
            from eml_math import EMLPoint
            from eml_spectral import spectral_flow, topology_invariant
            x = float(self.x_field.text or 1.0)
            y = float(self.y_field.text or 1.0)
            n = int(self.steps_field.text or 5)
            seed = EMLPoint(x, y)
            traj = spectral_flow(seed, steps=n)
            inv = topology_invariant(seed)
            lines = []
            for i, p in enumerate(traj):
                lines.append(f"step {i:>3}:  x={p.x:>14.6g}   y={p.y:>14.6g}")
            self.output_label.text = "\n".join(lines)
            self.invariant_label.text = (
                f"topology_invariant (b3=24, χ_eff=144) = {inv:.6g}    "
                f"(should be ≈ 144 along every step)"
            )
            self.status = f"Φⁿ trajectory of length {n+1}"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"

    def find_fixed_point(self) -> None:               # noqa: D401
        try:
            from eml_math import EMLPoint
            from eml_spectral import racetrack_fixed_point
            x = float(self.x_field.text or 1.0)
            y = float(self.y_field.text or 1.0)
            seed = EMLPoint(x, y)
            fp = racetrack_fixed_point(seed)
            self.status = (
                f"racetrack fixed point ≈ ({fp.x:.6g}, {fp.y:.6g})"
                if fp is not None else
                "no fixed point found within tolerance"
            )
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"
