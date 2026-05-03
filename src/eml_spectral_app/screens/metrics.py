"""Metrics screen — pick a named GR metric, evaluate ds² / proper time / curvature."""
from __future__ import annotations

from kivy.properties import ObjectProperty, StringProperty
from kivymd.uix.screen import MDScreen


_FACTORIES = {
    "flat":               (lambda **kw: ("flat",),                    {}),
    "schwarzschild":      (lambda rs=2.0, **kw: ("schwarzschild", rs), {"rs": "2.0"}),
    "flrw":               (lambda **kw: ("flrw",),                    {}),
    "ads5_x_s5":          (lambda **kw: ("ads5_x_s5",),               {}),
    "calabi_yau_3":       (lambda **kw: ("calabi_yau_3",),            {}),
    "klebanov_strassler": (lambda **kw: ("klebanov_strassler",),      {}),
    "heterotic_e8x8":     (lambda **kw: ("heterotic_e8x8",),          {}),
    "g2_holonomy":        (lambda **kw: ("g2_holonomy",),             {}),
}


class MetricsScreen(MDScreen):
    x_field = ObjectProperty(None)
    y_field = ObjectProperty(None)
    dx_field = ObjectProperty(None)
    dy_field = ObjectProperty(None)
    metric_field = ObjectProperty(None)
    rs_field = ObjectProperty(None)
    output_label = ObjectProperty(None)
    status = StringProperty("Pick a metric and evaluate")

    def compute(self) -> None:                        # noqa: D401
        try:
            from eml_math import EMLPoint
            from eml_spectral import MetricTensor
            name = (self.metric_field.text or "schwarzschild").strip()
            x = float(self.x_field.text or 3.0)
            y = float(self.y_field.text or 1.0)
            dx = float(self.dx_field.text or 0.01)
            dy = float(self.dy_field.text or 0.0)
            p = EMLPoint(x, y)

            if name == "schwarzschild":
                rs = float(self.rs_field.text or 2.0)
                m = MetricTensor.schwarzschild(rs=rs)
                tag = f"schwarzschild(rs={rs})"
            elif hasattr(MetricTensor, name):
                m = getattr(MetricTensor, name)()
                tag = name
            else:
                self.status = f"Unknown metric: {name!r}"
                return

            ds2 = m.ds2(p, dx=dx, dy=dy)
            try:
                pt = m.proper_time(p, dx=dx, dy=dy)
            except Exception:                         # noqa: BLE001
                pt = float("nan")
            try:
                curved = m.is_curved(p)
            except Exception:                         # noqa: BLE001
                curved = "?"
            self.output_label.text = "\n".join([
                f"metric:       {tag}",
                f"point:        EMLPoint({x}, {y})",
                f"displacement: dx={dx}, dy={dy}",
                f"",
                f"ds² = {ds2:.6g}",
                f"proper time τ = √|ds²| = {pt:.6g}",
                f"is_curved at p? {curved}",
            ])
            self.status = "OK"
        except Exception as exc:                       # noqa: BLE001
            self.status = f"{type(exc).__name__}: {exc}"
