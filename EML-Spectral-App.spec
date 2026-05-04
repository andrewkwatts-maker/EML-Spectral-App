# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from kivy_deps import sdl2, glew, angle
from kivy.tools.packaging.pyinstaller_hooks import (
    get_deps_minimal,
    hookspath,
    runtime_hooks,
)

datas = [
    ('src\\eml_spectral_app\\kv', 'eml_spectral_app\\kv'),
]
binaries = []
hiddenimports = []

# kivymd ships its own KV / fonts that must be bundled.
tmp_ret = collect_all('kivymd')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# eml-math + eml-spectral kernels.
tmp_ret = collect_all('eml_math')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('eml_spectral')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# matplotlib renders the LaTeX preview via mathtext.
tmp_ret = collect_all('matplotlib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Kivy itself: use the official hooks instead of collect_all('kivy'), which
# crashes on Kivy 2.3 because kivy.garden is a legacy namespace package
# whose __path__ is a string, breaking pkgutil.iter_modules under 3.13.
kivy_deps_dict = get_deps_minimal(video=None, audio=None)
hiddenimports += kivy_deps_dict.get('hiddenimports', [])
kivy_excludes = kivy_deps_dict.get('excludes', []) + ['kivy.garden']

a = Analysis(
    ['src\\eml_spectral_app\\__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=hookspath(),
    hooksconfig={},
    runtime_hooks=runtime_hooks(),
    excludes=kivy_excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)],
    [],
    name='EML-Spectral-App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
