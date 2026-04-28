from pathlib import Path


def convert_docx_to_markdown(source_path: str | Path, converter=None) -> str:
    engine = converter
    if engine is None:
        from markitdown import MarkItDown

        engine = MarkItDown()
    try:
        result = engine.convert(str(source_path), keep_data_uris=True)
    except TypeError as exc:
        if "keep_data_uris" not in str(exc):
            raise
        result = engine.convert(str(source_path))
    return result.text_content
