"""Algebras screen — Octonion / EMLMultivector / FreudenthalTripleSystem playground."""
from __future__ import annotations

from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen


class AlgebrasScreen(MDScreen):
    a_idx_field = ObjectProperty(None)
    b_idx_field = ObjectProperty(None)
    output_label = ObjectProperty(None)
    status = StringProperty("Pick two octonion basis indices and multiply")

    def octonion_mul(self) -> None:                   # noqa: D401
        try:
            from eml_spectral import basis_octonion
            i = int(self.a_idx_field.text or 1)
            j = int(self.b_idx_field.text or 2)
            a = basis_octonion(i)
            b = basis_octonion(j)
            prod = a * b
            ip = a + b
            self.output_label.text = "\n".join([
                f"e_{i} = {a}",
                f"e_{j} = {b}",
                f"",
                f"e_{i} · e_{j} = {prod}",
                f"|product|     = {prod.norm():.6g}",
                f"",
                f"e_{i} + e_{j} = {ip}",
                f"|sum|          = {ip.norm():.6g}",
            ])
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"

    def show_e7_alpha_leak(self) -> None:             # noqa: D401
        try:
            from eml_spectral import E7_56
            self.output_label.text = "\n".join([
                "E₇ ⊃ E₆ × U(1) portal coupling",
                "",
                f"α_leak = {E7_56.ALPHA_LEAK}",
                f"       = 1/√6  (Clebsch-Gordan coefficient — algebraic, no fit)",
            ])
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"

    def show_e8_racetrack(self) -> None:              # noqa: D401
        try:
            from eml_spectral import E8xE8
            d = E8xE8().racetrack_potential()
            lines = ["E₈ × E₈ heterotic racetrack:"]
            for k in ("epsilon_derived", "lambda_eff", "T_min", "N1", "N2",
                      "stabilized"):
                if k in d:
                    lines.append(f"  {k:18} = {d[k]}")
            self.output_label.text = "\n".join(lines)
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"
