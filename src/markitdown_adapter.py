from pathlib import Path


def convert_docx_to_markdown(source_path: str | Path, converter=None) -> str:
    engine = converter
    if engine is None:
        from markitdown import MarkItDown

        engine = MarkItDown()
    result = engine.convert(str(source_path))
    return result.text_content
