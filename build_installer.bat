@echo off
setlocal EnableDelayedExpansion
title DeenBG Build
color 0A
echo.
echo  ========================================================
echo    DeenBG  ^|  Building Standalone Installer (.exe)
echo  ========================================================
echo.
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found in PATH.
    echo  Install Python 3.10+ from https://www.python.org/downloads/
    pause & exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PV=%%v
echo  [OK] Python %PV%
echo.
echo  Installing build dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install --upgrade pyinstaller pillow arabic-reshaper python-bidi requests --quiet
if errorlevel 1 ( echo  [ERROR] pip install failed. & pause & exit /b 1 )
echo  [OK] All dependencies ready.
echo.
echo  Verifying files...
if not exist "%~dp0installer_gui.py" ( echo  [ERROR] installer_gui.py missing. & pause & exit /b 1 )
echo  [OK] installer_gui.py found.
if exist "%~dp0fonts\Amiri-Regular.ttf" (echo  [OK] Amiri font) else (echo  [WARN] Amiri font missing)
if exist "%~dp0fonts\Lato-Regular.ttf"  (echo  [OK] Lato font)  else (echo  [WARN] Lato font missing)
if exist "%~dp0data\quran.json"         (echo  [OK] quran.json - will be embedded) else (echo  [WARN] quran.json missing - installer will download at install time)
if exist "%~dp0docs\logo\icon.ico"      (echo  [OK] icon.ico) else (echo  [WARN] icon.ico missing)
echo.

for /f "delims=" %%p in ('python -c "import site; print(site.getusersitepackages())" 2^>nul') do set "SP=%%p"
if exist "!SP!\tcl" (
    set "PATH=!SP!;!PATH!"
    set "TCL_LIBRARY=!SP!\tcl\tcl8.6"
    set "TK_LIBRARY=!SP!\tcl\tk8.6"
    echo  [OK] Tcl/Tk environment configured.
)

echo  Compiling "DeenBG Installer.exe" (this takes 1-3 minutes)...
echo.
pyinstaller --onefile --windowed --name "DeenBG Installer" --icon "docs\logo\icon.ico" --add-data "fonts;fonts" --add-data "data;data" --add-data "docs\logo;docs\logo" --hidden-import PIL._tkinter_finder --hidden-import arabic_reshaper --hidden-import bidi.algorithm --collect-all arabic_reshaper --collect-all bidi --noconfirm installer_gui.py
if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. See PyInstaller output above.
    pause & exit /b 1
)
echo.
echo  ========================================================
echo    Build Complete!  "dist\DeenBG Installer.exe"
echo    Distribute this single file. No Python needed!
echo  ========================================================
echo.
if exist "dist\DeenBG Installer.exe" ( explorer dist )
pause
