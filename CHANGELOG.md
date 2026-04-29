# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-04-29

First stable release of the MarkItDown Windows desktop converter.

### Added

- Modern Flet desktop interface with a compact conversion workspace, file list, status chips, progress, and run log
- Inline image extraction from Markdown data URIs so converted documents can keep embedded image assets beside the output file
- PyInstaller data collection for bundled Magika model files used by MarkItDown

### Changed

- Replaced the earlier Tkinter shell with the Flet app while keeping the document conversion pipeline unchanged
- Updated documentation to describe the current Flet desktop UI and Windows usage flow

### Fixed

- Compatibility with current Flet 0.84 APIs for button content, file picker result handling, alignment, and window settings
- Handling for wrapped inline image data URIs and Word object placeholders during Markdown image extraction

## [0.1.0] - 2026-04-28

First usable release of the MarkItDown Windows desktop converter.

### Added

- Tkinter desktop app for converting `.doc` and `.docx` files into Markdown
- Batch file selection with per-file status and run summary
- Default output to the source folder, plus optional custom output folder
- `.docx` conversion through MarkItDown
- `.doc` conversion through LibreOffice headless mode, then MarkItDown
- Windows helper scripts: `run_windows.bat` and `build_windows.bat`
- PyInstaller spec for building `MarkItDownTool.exe`
- Basic automated tests for path helpers, LibreOffice command generation, conversion routing, and safe app import

### Notes

- `.docx` works directly after installing Python dependencies.
- `.doc` requires LibreOffice and a working `soffice` command in `PATH`.
- In environments without Tkinter, the app exits with a clear setup message instead of crashing during import.
