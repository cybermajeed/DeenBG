@echo off
setlocal EnableDelayedExpansion
title DeenBG Installer
net session >nul 2>&1
if %errorLevel% neq 0 (
    color 04
    echo Please run as Administrator.
    echo.
    pause
    exit
)

echo.
echo  ============================================================
echo    DeenBG ^| Quran Wallpaper Generator ^| Installer
echo  ============================================================
echo    BISMILLAH
echo  ============================================================
echo.


:: ── Python check ─────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH.
    echo  Download from https://www.python.org/downloads/
    echo  Check "Add Python to PATH" during installation.
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PV=%%v
echo  [OK] Python %PV% detected.

:: ── Packages ──────────────────────────────────────────────────
echo.
echo  Installing Python packages...
echo.
python -m pip install --upgrade pip --quiet
python -m pip install pillow requests arabic-reshaper python-bidi --quiet
if errorlevel 1 (
    echo  [ERROR] Package install failed. Run manually:
    echo    pip install pillow requests arabic-reshaper python-bidi
    pause & exit /b 1
)
echo  [OK] Packages installed.

:: ── Check fonts ───────────────────────────────────────────────
echo.
if exist "%~dp0fonts\Amiri-Regular.ttf" (
    echo  [OK] Amiri font found.
) else (
    echo  [WARN] Amiri-Regular.ttf not found in fonts\ folder.
    echo  Download from https://www.amirifont.org and place in fonts\
)
if exist "%~dp0fonts\Lato-Regular.ttf" (
    echo  [OK] Lato font found.
) else (
    echo  [WARN] Lato-Regular.ttf not found in fonts\ folder.
    echo  Download from https://fonts.google.com/specimen/Lato and place in fonts\
)

:: ── Quran data ────────────────────────────────────────────────
echo.
if exist "%~dp0data\quran.json" (
    echo  [OK] Quran database already exists.
) else (
    echo  Downloading Quran database - one-time, requires internet...
    python "%~dp0fetch_quran_data.py"
    if errorlevel 1 (
        echo  [ERROR] Failed to download Quran data. Check internet connection.
        pause & exit /b 1
    )
)

:: ── Setup wizard ─────────────────────────────────────────────
echo.
echo  ============================================================
echo   Running setup wizard...
echo  ============================================================
python "%~dp0setup_wizard.py"

:: ── Task Scheduler ────────────────────────────────────────────
echo.
set /p SCHED="Register with Task Scheduler? (y/n) [y]: "
if /i "!SCHED!"=="" set SCHED=y
if /i "!SCHED!"=="y" (
    set /p MINS="  Repeat every N minutes? (leave blank for logon-only): "
    if "!MINS!"=="" (
        python "%~dp0install_task.py"
    ) else (
        python "%~dp0install_task.py" --interval !MINS!
    )
)

:: ── Run now ───────────────────────────────────────────────────
echo.
set /p NOW="Generate first wallpaper now? (y/n) [y]: "
if /i "!NOW!"=="" set NOW=y
if /i "!NOW!"=="y" (
    echo.
    echo  Generating wallpaper...
    python "%~dp0wallpaper_generator.py"
)

echo.
echo  ============================================================
echo   DeenBG is ready!
echo   Your wallpaper will update at every system login.
echo  ============================================================
echo.
pause
