# MarkItDown Windows Tool

[English](README.md) | [简体中文](README.zh-CN.md)

Desktop utility for converting `.doc` and `.docx` files into Markdown.

## Features

- Single-window desktop app built with Tkinter
- Supports one or many input files
- Converts `.docx` directly with MarkItDown
- Converts `.doc` via headless LibreOffice, then sends the temporary `.docx` through MarkItDown
- Saves Markdown beside the source file by default
- Optional custom output folder
- Batch-safe error handling with per-file status and run summary

## Requirements

- Python 3.11+
- `markitdown`
- `pyinstaller` for packaging
- LibreOffice installed and `soffice` available in `PATH` if you want `.doc` support

## Install Dependencies

On Windows:

```powershell
py -m pip install -r requirements.txt
```

## Run Locally

```powershell
py app.py
```

Or on Windows, just double-click:

- `run_windows.bat`

## Run Tests

The current automated tests use the Python standard library `unittest` runner:

```powershell
set PYTHONPATH=.
py -m unittest discover -s tests -v
```

On macOS or Linux:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## Build Windows EXE

```powershell
pyinstaller markitdown_tool.spec
```

Or on Windows, just double-click:

- `build_windows.bat`

Expected output:

- `dist/MarkItDownTool.exe`

## Notes About `.doc`

- `.docx` works through MarkItDown directly.
- `.doc` requires LibreOffice because this app first converts `.doc` to a temporary `.docx`.
- If LibreOffice is missing, the app will stop before the run starts and show a clear message.

## Fast Start On Windows

1. Install Python 3.11+.
2. If you need `.doc` support, install LibreOffice.
3. Open this project folder.
4. Double-click `run_windows.bat`.

If you want a standalone `.exe`:

1. Double-click `build_windows.bat`.
2. Wait for the build to finish.
3. Open `dist/MarkItDownTool.exe`.
