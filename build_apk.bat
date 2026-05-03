@echo off
REM ============================================================================
REM build_apk.bat — Android debug APK for EML-Spectral-App via buildozer (in WSL)
REM
REM Output: bin\eml-spectral-app-1.3.1-debug.apk
REM
REM Prerequisites (one-time, on WSL2 Ubuntu 22.04):
REM   sudo apt update && sudo apt install -y python3-pip openjdk-17-jdk \
REM       autoconf automake libtool pkg-config zlib1g-dev libncurses5-dev \
REM       libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
REM   pip3 install --user buildozer cython==0.29.36
REM ============================================================================
setlocal

set "WSL_DISTRO=%WSL_DISTRO%"
if "%WSL_DISTRO%"=="" set "WSL_DISTRO=Ubuntu"

set "WIN_DIR=%CD%"
set "WSL_DIR=%WIN_DIR:\=/%"
set "WSL_DIR=%WSL_DIR:H:=/mnt/h%"
set "WSL_DIR=%WSL_DIR:h:=/mnt/h%"
set "WSL_DIR=%WSL_DIR:C:=/mnt/c%"
set "WSL_DIR=%WSL_DIR:c:=/mnt/c%"

echo Building APK in WSL distro %WSL_DISTRO% under %WSL_DIR% ...
wsl -d %WSL_DISTRO% -- bash -lc "cd '%WSL_DIR%' && buildozer android debug"

if %ERRORLEVEL% NEQ 0 (
    echo BUILD FAILED.  Try: wsl -d %WSL_DISTRO% -- buildozer android debug --verbose
    exit /b 1
)
echo.
echo BUILD OK  ->  bin\
dir /b bin
endlocal
