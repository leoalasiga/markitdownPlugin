from pathlib import Path


SUPPORTED_EXTENSIONS = {".doc", ".docx"}


def is_supported_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def is_doc_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".doc"


def is_docx_file(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".docx"


def build_output_path(source_path: str | Path, output_dir: str | Path | None) -> Path:
    source = Path(source_path)
    base_dir = Path(output_dir) if output_dir else source.parent
    return base_dir / f"{source.stem}.md"
