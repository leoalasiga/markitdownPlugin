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
  echo Failed to install Python dependencies.
  exit /b 1
)

set PYTHONPATH=%cd%
py app.py
