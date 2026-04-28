# MarkItDown Windows Tool Design

**Date:** 2026-04-28

**Summary:** Build a Windows desktop utility that converts `.doc` and `.docx` files into Markdown using Python. `.docx` files go directly through MarkItDown. `.doc` files are first converted to temporary `.docx` files with LibreOffice in headless mode, then passed through MarkItDown.

## Goals

- Provide a single-window desktop app that non-technical users can launch with a double-click.
- Support single-file and batch conversion for `.doc` and `.docx`.
- Output Markdown beside the source file by default, with an option to choose a custom output directory.
- Package the app as a Windows `.exe`.

## Non-Goals

- Rich text preview, Markdown preview, or editor features.
- Drag-and-drop in the first version.
- Per-file output naming rules beyond "same base name, `.md` extension".
- Native `.doc` parsing without LibreOffice.

## User Flow

1. User launches the app.
2. User selects one or more `.doc` or `.docx` files.
3. User either keeps the default output mode ("same folder as source") or selects a custom output directory.
4. User clicks `Start Conversion`.
5. App processes files one by one and updates status/log output in the UI.
6. User sees a final summary with success and failure counts.

## Architecture

The app will be split into a thin GUI layer and small service modules:

- `app.py`: process entry point.
- `src/gui.py`: Tkinter window, file list, output settings, progress/log display.
- `src/models.py`: dataclasses for conversion tasks and results.
- `src/converter.py`: orchestration for handling `.doc` and `.docx`.
- `src/libreoffice.py`: headless LibreOffice adapter for `.doc -> .docx`.
- `src/markitdown_adapter.py`: wrapper around the MarkItDown API.
- `src/utils.py`: path helpers and file-type helpers.

This keeps the UI independent from conversion logic so we can later swap UI frameworks or add drag-and-drop without rewriting the pipeline.

## Conversion Rules

### `.docx`

- Validate file exists.
- Convert directly with MarkItDown.
- Write Markdown to the target directory using the source stem and `.md` extension.

### `.doc`

- Check whether LibreOffice `soffice` is available.
- Convert the source `.doc` into a temporary `.docx` file in the system temp directory.
- Convert the temporary `.docx` with MarkItDown.
- Delete temporary files after success or failure.

## Output Rules

- Default mode: output Markdown beside each source file.
- Optional mode: output all Markdown files into a selected directory.
- Output file name: `<source_stem>.md`.
- If a name collision exists, overwrite in v1 for simplicity, but log the target path clearly before writing.

## UI Layout

Single window with three sections:

1. File list section
   - `Add Files`
   - `Remove Selected`
   - `Clear List`
   - Scrollable list/table with source path and status

2. Output settings section
   - Checkbox or radio mode for `Output beside source`
   - `Choose Output Folder` button enabled only when custom output mode is active
   - Read-only label showing current output strategy

3. Execution section
   - `Start Conversion`
   - `Open Output Folder` optional convenience button if custom output mode is selected
   - Read-only log text area
   - Summary label

## Error Handling

The app should show clear, actionable messages for:

- No files selected
- Unsupported file type
- Missing source file
- Output directory missing or not writable
- LibreOffice not installed or not discoverable
- LibreOffice conversion failure
- MarkItDown conversion failure
- Markdown write failure

In batch mode, one failure must not stop the remaining files. Each file gets an independent result.

## Responsiveness

- Run conversion work off the main Tkinter event loop by using a background worker thread.
- Send per-file status and log messages back to the UI safely with a queue and `after()` polling.
- Disable mutation controls while a conversion batch is running.

## Dependencies

- Python 3.11+
- `markitdown`
- `pyinstaller`
- Windows runtime with optional LibreOffice installation for `.doc`

## Packaging

- Package as a single Windows `.exe` with PyInstaller.
- Include an icon later if desired, but keep first version focused on correctness.
- Document build command and runtime assumptions in README.

## Testing Strategy

Manual verification for v1:

- Single `.docx` conversion to source directory
- Batch `.docx` conversion
- Mixed `.doc` and `.docx` conversion with LibreOffice installed
- Custom output directory
- Missing LibreOffice when selecting `.doc`
- Invalid output folder
- Corrupt input file

Light automated tests:

- Path and output resolution helpers
- File type routing
- LibreOffice command construction
- Conversion orchestration with mocked adapters

## Future Enhancements

- Drag-and-drop
- Remember last used output folder
- Open result file directly
- Per-file output locations
- Better overwrite behavior
