[app]

title = EML-Spectral-App
package.name = emlspectralapp
package.domain = org.emlspectral.app

source.dir = src
source.include_exts = py,png,jpg,kv,atlas,svg,ttf,otf,json
source.include_patterns = eml_spectral_app/kv/*.kv,eml_spectral_app/assets/*

version = 1.3.1

requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,eml-math,eml-spectral

orientation = portrait
fullscreen = 0

icon.filename = src/eml_spectral_app/assets/icon.png
presplash.filename = src/eml_spectral_app/assets/splash.png
android.permissions = INTERNET

android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.private_storage = True

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
