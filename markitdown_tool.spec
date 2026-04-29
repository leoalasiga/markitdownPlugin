# -*- mode: python ; coding: utf-8 -*-

from importlib.util import find_spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


def collect_magika_datas():
    magika_spec = find_spec("magika")
    if magika_spec is None or not magika_spec.submodule_search_locations:
        raise SystemExit("magika package not found. Run: py -m pip install -r requirements.txt")

    package_dir = Path(next(iter(magika_spec.submodule_search_locations)))
    model_dir = package_dir / "models" / "standard_v3_3"
    required_files = [
        model_dir / "model.onnx",
        model_dir / "config.min.json",
    ]
    missing_files = [str(path) for path in required_files if not path.is_file()]
    if missing_files:
        raise SystemExit(
            "magika model files missing from the build environment: "
            + ", ".join(missing_files)
        )

    datas = collect_data_files("magika")
    for path in sorted((package_dir / "models").rglob("*")):
        if path.is_file():
            datas.append((str(path), str(path.parent.relative_to(package_dir.parent))))
    return sorted(set(datas))


magika_datas = collect_magika_datas()


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=magika_datas,
    hiddenimports=["markitdown", "flet"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MarkItDownTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
