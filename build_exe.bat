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
%PY% -m PyInstaller ^
    --noconfirm ^
    --name "EML-Spectral-App" ^
    --windowed ^
    --onefile ^
    --add-data "src\eml_spectral_app\kv;eml_spectral_app\kv" ^
    --add-data "src\eml_spectral_app\assets;eml_spectral_app\assets" ^
    --collect-all kivymd ^
    --collect-all kivy ^
    --collect-all eml_math ^
    --collect-all eml_spectral ^
    src\eml_spectral_app\__main__.py

echo.
if exist dist\EML-Spectral-App.exe (
    echo BUILD OK  ->  dist\EML-Spectral-App.exe
) else (
    echo BUILD FAILED.
    exit /b 1
)
endlocal
