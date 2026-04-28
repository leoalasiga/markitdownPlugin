@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" was not found.
  echo Install Python 3.11+ for Windows first, then run this script again.
  exit /b 1
)

py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install application dependencies.
  exit /b 1
)

py -m pip install pyinstaller
if errorlevel 1 (
  echo Failed to install PyInstaller.
  exit /b 1
)

pyinstaller --clean markitdown_tool.spec
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

echo.
echo Build complete.
echo EXE path: %cd%\dist\MarkItDownTool.exe
