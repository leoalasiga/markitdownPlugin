# Flet UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the Tkinter UI with a modern Flet desktop interface while reusing the current document conversion pipeline.

**Architecture:** `app.py` remains the import-safe entry point and calls `src.gui.main`. `src.gui` owns Flet controls, app state, background-thread orchestration, and UI event polling. Conversion behavior stays in `src.converter`, `src.libreoffice`, and `src.utils`.

**Tech Stack:** Python 3.11+, Flet, MarkItDown, LibreOffice bridge, unittest, PyInstaller.

---

### Task 1: Dependency And Import Contract

**Files:**
- Modify: `requirements.txt`
- Modify: `tests/test_app_import.py`

**Step 1: Write the failing test**

Add a test that asserts the Flet dependency is declared:

```python
from pathlib import Path


def test_requirements_declares_flet(self) -> None:
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    self.assertIn("flet", requirements.lower())
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests.test_app_import -v`

Expected: FAIL because `requirements.txt` does not yet mention Flet.

**Step 3: Write minimal implementation**

Add `flet>=0.25.0` to `requirements.txt`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=. python3 -m unittest tests.test_app_import -v`

Expected: PASS.

### Task 2: Flet GUI Shell

**Files:**
- Replace: `src/gui.py`

**Step 1: Write the failing test**

Extend `tests/test_app_import.py` to assert that `src.gui` exposes `main` and `ConverterApp`:

```python
def test_gui_exposes_flet_app_entrypoint(self) -> None:
    gui = importlib.import_module("src.gui")
    self.assertTrue(callable(gui.main))
    self.assertTrue(hasattr(gui, "ConverterApp"))
```

**Step 2: Run test to verify it fails or errors for the old Tkinter contract**

Run: `PYTHONPATH=. python3 -m unittest tests.test_app_import -v`

Expected: current import still works, but implementation is still Tkinter. Use this as a guard while replacing the module.

**Step 3: Write implementation**

Replace Tkinter code in `src/gui.py` with:

- `ConverterApp` class that accepts a Flet `Page`.
- State for selected files, output mode, custom output directory, running state, logs, queue, and worker thread.
- A modern layout with sidebar, header, output controls, file picker, file list, progress, action row, and log list.
- `ft.FilePicker` for file selection and `ft.FilePicker.get_directory_path()` for output folder selection.
- Background conversion thread using existing `convert_one`.
- Queue polling via `page.run_thread` or periodic timer-compatible page updates.

**Step 4: Run import tests**

Run: `PYTHONPATH=. python3 -m unittest tests.test_app_import -v`

Expected: PASS.

### Task 3: App Entry And Packaging

**Files:**
- Modify: `app.py`
- Modify: `markitdown_tool.spec`
- Modify: `tests/test_pyinstaller_spec.py`

**Step 1: Write failing packaging test**

Add assertions that PyInstaller hidden imports include Flet:

```python
self.assertIn('"flet"', spec)
```

**Step 2: Run packaging test to verify it fails**

Run: `PYTHONPATH=. python3 -m unittest tests.test_pyinstaller_spec -v`

Expected: FAIL because the spec only includes `markitdown`.

**Step 3: Update implementation**

Keep `app.py` import-safe and let `src.gui.main()` call `ft.app(target=...)`. Add `"flet"` to `hiddenimports` in `markitdown_tool.spec`.

**Step 4: Run packaging test**

Run: `PYTHONPATH=. python3 -m unittest tests.test_pyinstaller_spec -v`

Expected: PASS.

### Task 4: Documentation And Full Verification

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`

**Step 1: Update docs**

Describe the Flet UI, modern desktop shell, and unchanged conversion behavior. Replace references to Tkinter with Flet.

**Step 2: Run full tests**

Run: `PYTHONPATH=. python3 -m unittest discover -s tests -v`

Expected: all tests pass.

**Step 3: Optional smoke check**

Run: `PYTHONPATH=. python3 -c "import app; print(callable(app.main))"`

Expected: prints `True`.
