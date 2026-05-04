@echo off
REM ============================================================================
REM build_exe.bat — Windows executable for EML-Spectral-App via PyInstaller
REM
REM Output: dist\EML-Spectral-App.exe
REM ============================================================================
setlocal

set "PY=%PY%"
if "%PY%"=="" set "PY=python"

echo Installing build dependencies and project ...
%PY% -m pip install --upgrade pip pyinstaller
%PY% -m pip install -e .

echo.
echo Running PyInstaller ...
REM Build from EML-Spectral-App.spec — the spec uses Kivy's official
REM PyInstaller integration (kivy_deps + kivy.tools.packaging.pyinstaller_hooks)
REM because --collect-all kivy crashes on Kivy 2.3 / Python 3.13 (kivy.garden
REM is a legacy namespace package with a non-list __path__).
%PY% -m PyInstaller --noconfirm EML-Spectral-App.spec

echo.
if exist dist\EML-Spectral-App.exe (
    echo BUILD OK  --  dist\EML-Spectral-App.exe
) else (
    echo BUILD FAILED.
    exit /b 1
)
endlocal
