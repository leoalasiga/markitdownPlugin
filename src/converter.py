import tempfile
from pathlib import Path

from src.libreoffice import convert_doc_to_docx
from src.markitdown_adapter import convert_docx_to_markdown
from src.models import ConversionResult
from src.utils import build_output_path, is_doc_file, is_supported_file


def write_markdown(output_path: str | Path, markdown: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def convert_one(
    source_path: str | Path,
    output_dir: str | Path | None,
    markdown_converter=None,
    doc_bridge=None,
    writer=None,
) -> ConversionResult:
    source = Path(source_path)
    if not source.exists():
        return ConversionResult(source, None, False, "Source file does not exist.")
    if not is_supported_file(source):
        return ConversionResult(source, None, False, "Unsupported file type.")

    markdown_converter = markdown_converter or convert_docx_to_markdown
    doc_bridge = doc_bridge or convert_doc_to_docx
    writer = writer or write_markdown
    output_path = build_output_path(source, output_dir)

    try:
        if is_doc_file(source):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_docx = doc_bridge(source, temp_dir)
                markdown = markdown_converter(temp_docx)
        else:
            markdown = markdown_converter(source)

        writer(output_path, markdown)
        return ConversionResult(source, output_path, True, "Conversion completed.")
    except Exception as exc:  # pragma: no cover - covered by targeted unit tests later
        return ConversionResult(source, output_path, False, str(exc))
