@echo off
setlocal
python -m pip install --upgrade pip
python -m pip install -r requirements
python -m pip install pyinstaller
python -m compileall desktop
if errorlevel 1 exit /b 1
python -m PyInstaller --clean --noconfirm Hn38videoAItool.spec
if errorlevel 1 exit /b 1
echo.
echo BUILD OK:
echo dist\Hn38videoAItool.exe
