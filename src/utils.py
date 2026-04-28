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


def get_output_folder_for_open(
    source_paths: list[Path],
    output_mode: str,
    custom_output_dir: str | Path | None,
) -> Path | None:
    if output_mode == "custom":
        if not custom_output_dir:
            return None
        return Path(custom_output_dir)

    if len(source_paths) == 1:
        return source_paths[0].parent

    return None
