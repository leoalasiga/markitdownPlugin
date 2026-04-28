import shutil
import subprocess
from pathlib import Path


class LibreOfficeNotFoundError(RuntimeError):
    """Raised when soffice is not available in PATH."""


def build_soffice_command(source_path: str | Path, output_dir: str | Path) -> list[str]:
    return [
        "soffice",
        "--headless",
        "--convert-to",
        "docx",
        "--outdir",
        str(output_dir),
        str(source_path),
    ]


def find_soffice() -> str | None:
    return shutil.which("soffice")


def convert_doc_to_docx(source_path: str | Path, output_dir: str | Path) -> Path:
    soffice_path = find_soffice()
    if not soffice_path:
        raise LibreOfficeNotFoundError("LibreOffice soffice was not found in PATH.")

    source = Path(source_path)
    command = build_soffice_command(source, output_dir)
    command[0] = soffice_path
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "Unknown LibreOffice error."
        raise RuntimeError(f"LibreOffice conversion failed: {stderr}")

    converted_path = Path(output_dir) / f"{source.stem}.docx"
    if not converted_path.exists():
        raise RuntimeError("LibreOffice did not produce the expected DOCX file.")
    return converted_path
