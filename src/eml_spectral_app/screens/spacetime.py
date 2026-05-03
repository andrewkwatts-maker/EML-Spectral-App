"""Spacetime screen — Lorentz invariants + boost on a single EMLPoint."""
from __future__ import annotations

from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen


class SpacetimeScreen(MDScreen):
    x_field = ObjectProperty(None)
    y_field = ObjectProperty(None)
    rapidity_field = ObjectProperty(None)
    output_label = ObjectProperty(None)
    status = StringProperty("Set (x, y, rapidity), hit Compute")

    def compute(self) -> None:                        # noqa: D401
        try:
            from eml_math import EMLPoint
            from eml_spectral import spacetime
            x = float(self.x_field.text or 1.0)
            y = float(self.y_field.text or 1.0)
            phi = float(self.rapidity_field.text or 0.5)
            p = EMLPoint(x, y)
            mink = spacetime.minkowski_delta(p)
            eucl = spacetime.euclidean_delta(p)
            tl = spacetime.is_timelike(p)
            sl = spacetime.is_spacelike(p)
            ll = spacetime.is_lightlike(p)
            kind = "timelike" if tl else "spacelike" if sl else "lightlike" if ll else "?"
            try:
                rap = spacetime.rapidity(p)
            except Exception:                         # noqa: BLE001
                rap = float("nan")
            try:
                boosted = spacetime.boost(p, phi)
                bx, by = boosted.x, boosted.y
                bm = spacetime.minkowski_delta(boosted)
            except Exception as exc:                  # noqa: BLE001
                bx = by = bm = float("nan")
                kind += f"  (boost error: {exc})"
            lines = [
                f"Δ_M (Minkowski) = {mink:.6g}",
                f"Δ_E (Euclidean) = {eucl:.6g}",
                f"causal type     = {kind}",
                f"intrinsic rapidity = {rap:.6g}",
                "",
                f"after boost(φ = {phi}):",
                f"  x' = {bx:.6g}",
                f"  y' = {by:.6g}",
                f"  Δ_M' = {bm:.6g}    (should match Δ_M)",
            ]
            self.output_label.text = "\n".join(lines)
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"
