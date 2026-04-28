# Contributing

Thanks for your interest in improving this project.

## Development Setup

1. Install Python 3.11 or newer.
2. Install project dependencies:

```powershell
py -m pip install -r requirements.txt
```

3. If you want to test `.doc` conversion, install LibreOffice and make sure `soffice` is available in `PATH`.

## Running the App

```powershell
py app.py
```

## Running Tests

Windows:

```powershell
set PYTHONPATH=.
py -m unittest discover -s tests -v
```

macOS or Linux:

```bash
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## Pull Request Notes

- Keep changes focused and easy to review.
- Update `README.md` and `README.zh-CN.md` if user-facing behavior changes.
- Update `CHANGELOG.md` when shipping a visible feature.
- If you change build or packaging behavior, update the Windows instructions too.

## Bug Reports

When opening an issue, include:

- your OS version
- Python version
- whether LibreOffice is installed
- whether the file is `.doc` or `.docx`
- the error message shown in the app log
