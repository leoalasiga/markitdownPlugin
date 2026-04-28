# MarkItDown Windows Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Windows Tkinter desktop app that converts `.doc` and `.docx` files into Markdown, using LibreOffice as a `.doc` bridge and MarkItDown for Markdown conversion.

**Architecture:** Keep the GUI thin and move conversion work into small service modules. Use a background worker thread plus a queue so conversion stays responsive while the UI shows per-file status, logs, and a final summary. Package the result as a Windows `.exe` with PyInstaller.

**Tech Stack:** Python 3.11+, Tkinter, MarkItDown, LibreOffice (`soffice`), pytest, PyInstaller

---

### Task 1: Scaffold the project structure

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `app.py`
- Create: `src/__init__.py`
- Create: `src/models.py`
- Create: `src/utils.py`
- Create: `tests/test_utils.py`

**Step 1: Write the failing test**

```python
from src.utils import is_supported_file, build_output_path


def test_is_supported_file_accepts_doc_and_docx():
    assert is_supported_file("a.doc") is True
    assert is_supported_file("b.docx") is True
    assert is_supported_file("c.txt") is False


def test_build_output_path_uses_custom_directory():
    result = build_output_path("/tmp/invoice.docx", "/exports")
    assert str(result).endswith("/exports/invoice.md")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_utils.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing function errors.

**Step 3: Write minimal implementation**

```python
from pathlib import Path


def is_supported_file(path: str) -> bool:
    return Path(path).suffix.lower() in {".doc", ".docx"}


def build_output_path(source_path: str, output_dir: str | None) -> Path:
    source = Path(source_path)
    base_dir = Path(output_dir) if output_dir else source.parent
    return base_dir / f"{source.stem}.md"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_utils.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add requirements.txt README.md app.py src/__init__.py src/models.py src/utils.py tests/test_utils.py
git commit -m "feat: scaffold markitdown desktop converter"
```

### Task 2: Implement the MarkItDown adapter

**Files:**
- Create: `src/markitdown_adapter.py`
- Create: `tests/test_markitdown_adapter.py`
- Modify: `requirements.txt`

**Step 1: Write the failing test**

```python
from unittest.mock import Mock

from src.markitdown_adapter import convert_docx_to_markdown


def test_convert_docx_to_markdown_returns_text(tmp_path):
    source = tmp_path / "sample.docx"
    source.write_text("placeholder")
    fake_converter = Mock()
    fake_converter.convert.return_value.text_content = "# Title"

    result = convert_docx_to_markdown(source, fake_converter)

    assert result == "# Title"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_markitdown_adapter.py -v`
Expected: FAIL because adapter does not exist.

**Step 3: Write minimal implementation**

```python
from markitdown import MarkItDown


def convert_docx_to_markdown(source_path, converter=None):
    engine = converter or MarkItDown()
    result = engine.convert(str(source_path))
    return result.text_content
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_markitdown_adapter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/markitdown_adapter.py tests/test_markitdown_adapter.py requirements.txt
git commit -m "feat: add markitdown conversion adapter"
```

### Task 3: Implement LibreOffice `.doc` bridging

**Files:**
- Create: `src/libreoffice.py`
- Create: `tests/test_libreoffice.py`

**Step 1: Write the failing test**

```python
from src.libreoffice import build_soffice_command


def test_build_soffice_command_targets_docx_output():
    command = build_soffice_command("C:/docs/a.doc", "C:/temp")
    assert "--headless" in command
    assert "--convert-to" in command
    assert "docx" in command
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_libreoffice.py -v`
Expected: FAIL because module/function is missing.

**Step 3: Write minimal implementation**

```python
def build_soffice_command(source_path: str, output_dir: str) -> list[str]:
    return [
        "soffice",
        "--headless",
        "--convert-to",
        "docx",
        "--outdir",
        output_dir,
        source_path,
    ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_libreoffice.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/libreoffice.py tests/test_libreoffice.py
git commit -m "feat: add libreoffice doc conversion bridge"
```

### Task 4: Implement the conversion orchestrator

**Files:**
- Create: `src/converter.py`
- Modify: `src/models.py`
- Create: `tests/test_converter.py`

**Step 1: Write the failing test**

```python
from unittest.mock import Mock

from src.converter import convert_one


def test_convert_one_routes_docx_without_libreoffice(tmp_path):
    source = tmp_path / "report.docx"
    source.write_text("placeholder")
    writer = Mock()
    markdown_converter = Mock(return_value="# Report")

    result = convert_one(
        source_path=source,
        output_dir=None,
        markdown_converter=markdown_converter,
        doc_bridge=None,
        writer=writer,
    )

    assert result.success is True
    writer.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_converter.py -v`
Expected: FAIL because orchestrator does not exist.

**Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path

from src.utils import build_output_path


@dataclass
class ConversionResult:
    source_path: Path
    output_path: Path | None
    success: bool
    message: str


def convert_one(source_path, output_dir, markdown_converter, doc_bridge, writer):
    output_path = build_output_path(str(source_path), output_dir)
    markdown = markdown_converter(source_path)
    writer(output_path, markdown)
    return ConversionResult(source_path=Path(source_path), output_path=output_path, success=True, message="ok")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_converter.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/converter.py src/models.py tests/test_converter.py
git commit -m "feat: add conversion orchestration"
```

### Task 5: Build the Tkinter GUI

**Files:**
- Create: `src/gui.py`
- Modify: `app.py`

**Step 1: Write the failing test**

Skip automated GUI tests in v1. Instead define a manual acceptance check:

```text
Launch app.py and verify:
1. Window opens without traceback
2. Add Files button accepts .doc and .docx
3. Output mode toggles custom directory controls
4. Start Conversion is disabled while a batch is running
```

**Step 2: Run check to verify it fails**

Run: `python app.py`
Expected: FAIL because GUI module does not exist.

**Step 3: Write minimal implementation**

```python
def main():
    app = ConverterApp()
    app.run()
```

Implement:
- file list UI
- output mode controls
- log area
- worker thread and queue polling
- start button state management

**Step 4: Run check to verify it passes**

Run: `python app.py`
Expected: Window opens and controls behave as designed.

**Step 5: Commit**

```bash
git add app.py src/gui.py
git commit -m "feat: add desktop conversion interface"
```

### Task 6: Package and document the app

**Files:**
- Create: `makeitdown.spec` or `markitdown_tool.spec`
- Modify: `README.md`

**Step 1: Write the failing test**

Define a packaging acceptance check:

```text
PyInstaller build should produce a Windows .exe that starts and performs a sample .docx conversion.
```

**Step 2: Run check to verify it fails**

Run: `pyinstaller --onefile app.py`
Expected: FAIL or incomplete because spec/dependencies/docs are not ready.

**Step 3: Write minimal implementation**

Document:
- dependency installation
- LibreOffice requirement for `.doc`
- local run command
- build command
- expected `.exe` output path

Create PyInstaller spec or command instructions needed for repeatable builds.

**Step 4: Run check to verify it passes**

Run: `pyinstaller --onefile --name MarkItDownTool app.py`
Expected: build finishes and outputs `dist/MarkItDownTool.exe` on Windows.

**Step 5: Commit**

```bash
git add README.md markitdown_tool.spec
git commit -m "build: package desktop converter for windows"
```

### Task 7: Verify end-to-end behavior

**Files:**
- Modify: `README.md` if verification reveals missing setup notes

**Step 1: Write the failing test**

Define the end-to-end checklist:

```text
1. Convert one .docx to source directory
2. Convert multiple .docx files to custom output directory
3. Convert one .doc with LibreOffice installed
4. Attempt .doc conversion without LibreOffice and verify clear error
```

**Step 2: Run check to verify it fails**

Run the desktop app and manually execute the four scenarios.
Expected: Any mismatch is recorded and fixed before completion.

**Step 3: Write minimal implementation**

Adjust UI copy, logging, or path handling to resolve any failures found during verification.

**Step 4: Run check to verify it passes**

Run the same four manual scenarios again.
Expected: All scenarios pass.

**Step 5: Commit**

```bash
git add README.md app.py src/gui.py src/converter.py src/libreoffice.py src/markitdown_adapter.py src/utils.py
git commit -m "test: verify end-to-end desktop conversion flow"
```
