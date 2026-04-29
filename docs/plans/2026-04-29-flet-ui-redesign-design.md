# Flet UI Redesign Design

## Goal

Replace the Tkinter desktop shell with a modern Flet interface while keeping the existing conversion pipeline unchanged.

## Decision

Use a single-page Flet desktop app. The app continues to enter through `app.py`, which imports `src.gui.main`. `src.gui` becomes the Flet UI layer and delegates conversion to `src.converter.convert_one`, LibreOffice detection to `src.libreoffice.find_soffice`, and output folder selection logic to `src.utils`.

## User Experience

The first screen is the tool itself, not a landing page. It has a compact sidebar, a main conversion workspace, and a log/progress area.

- Sidebar: product name, conversion section, lightweight placeholders for history and settings.
- Header: concise title, purpose, and status summary.
- File area: card-style file list with status chips for waiting, queued, converting, success, failed, and skipped.
- Output area: segmented choice between saving beside source files and saving to a chosen folder.
- Actions: prominent start button, clear button, and open output folder button.
- Feedback: progress bar, summary text, and timestamped log.

## Data Flow

User-selected files are stored as `Path` objects in app state and rendered as Flet controls. Starting a conversion validates the file list, output mode, and LibreOffice availability for `.doc` files. Conversion runs in a background thread and posts UI events into a queue. The Flet page polls that queue and updates status chips, progress, and logs on the UI thread.

## Error Handling

Validation failures show a clear dialog and do not start work. Per-file conversion failures mark only that row as failed and continue the batch. Missing LibreOffice is reported before the batch starts when any `.doc` file is present. Unsupported or duplicate files are skipped with a log entry.

## Testing

Automated tests should verify that the app entry point imports without starting a GUI and that the Flet dependency is declared. Existing converter tests remain the behavioral safety net for document conversion.

## Scope

This change intentionally does not add conversion history, Markdown preview, OCR, task queue persistence, or plugin support. The UI leaves room for those features without implementing them now.
