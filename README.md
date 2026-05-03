# EML-Spectral-App

**v1.3.1** — KivyMD visual explorer for the [`eml-spectral`](https://pypi.org/project/eml-spectral/) PyPI library (transitively pulls `eml-math`).

[![CI](https://github.com/andrewkwatts-maker/EML-Spectral-App/actions/workflows/ci.yml/badge.svg)](https://github.com/andrewkwatts-maker/EML-Spectral-App/actions/workflows/ci.yml)

A cross-platform GUI (Windows / Linux / macOS / Android) for the spectrum layer of the EML stack: Lorentz invariants, the Φ spectral flow, Clifford / Octonion / E₇ / E₈ algebras, named GR metrics, E₈ + Leech lattices, and the 167-name constants registry.

The app owns no math — every screen wires UI controls directly to the `eml-spectral` (and `eml-math`) public API.

---

## Screens

| Screen | What it does | eml-spectral API used |
|---|---|---|
| **Spectral Flow** | Iterate Φ from a seed `EMLPoint(x, y)`; show trajectory + topology invariant per step; find racetrack fixed points | `spectral_flow`, `racetrack_fixed_point`, `topology_invariant` |
| **Spacetime** | Lorentz invariants on a single point + boost; classify timelike / spacelike / lightlike | `spacetime.minkowski_delta / euclidean_delta / boost / rapidity / is_*` |
| **Metrics** | Pick a named GR metric (`flat`, `schwarzschild(rs)`, `flrw`, `ads5_x_s5`, `calabi_yau_3`, `klebanov_strassler`, `heterotic_e8x8`, `g2_holonomy`); evaluate ds², proper time, curvature | `MetricTensor.<factory>().ds2 / proper_time / is_curved` |
| **Algebras** | Octonion `e_i · e_j` via Fano plane; E₇ portal coupling 1/√6; E₈×E₈ heterotic racetrack | `basis_octonion`, `Octonion.__mul__ / norm`, `E7_56.ALPHA_LEAK`, `E8xE8().racetrack_potential` |
| **Lattices** | E₈ root + Leech kissing numbers; first N lattice points | `e8_lattice_points`, `leech_lattice_points`, `Get("e8_kissing")` etc. |
| **Constants** | Searchable list of all 167 names — 31 spectral + 136 math (delegated). Tap → datasheet | `list_constants`, `Get(name)` |

---

## Installation

```bash
pip install eml-spectral-app          # then: eml-spectral-app
# OR run from the repo:
git clone https://github.com/andrewkwatts-maker/EML-Spectral-App.git
cd EML-Spectral-App
pip install -e .
python -m eml_spectral_app
```

Required dependencies (pulled in automatically): `kivy>=2.3`, `kivymd>=1.2`, `Pillow>=10`, `eml-math>=1.3.1`, `eml-spectral>=1.3.1`.

---

## Building binaries

### Windows `.exe` (single-file)

```bat
build_exe.bat
.\dist\EML-Spectral-App.exe
```

### Android `.apk` (debug)

```bat
build_apk.bat
adb install -r .\bin\eml-spectral-app-1.3.1-debug.apk
```

Buildozer is Linux-only, so `build_apk.bat` shells into WSL2 (default distro `Ubuntu`; override with `set WSL_DISTRO=Ubuntu-22.04`). One-time WSL setup is at the top of `build_apk.bat`.

---

## Project layout

```
EML-Spectral-App/
├─ pyproject.toml
├─ buildozer.spec
├─ build_exe.bat
├─ build_apk.bat
├─ src/eml_spectral_app/
│  ├─ __init__.py               # __version__ = "1.3.1"
│  ├─ __main__.py
│  ├─ app.py                    # MDApp + ScreenManager
│  ├─ kv/                       # one .kv per screen
│  └─ screens/                  # one .py per screen
└─ tests/test_smoke.py
```

## Versioning

Lockstep with the EML stack: `eml-math 1.3.1`, `eml-spectral 1.3.1`, `metaphysica 1.3.1`, `periodica 1.3.1`.

## License

MIT — © Andrew K Watts.
