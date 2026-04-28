import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.markitdown_adapter import convert_docx_to_markdown


class MarkItDownAdapterTests(unittest.TestCase):
    def test_convert_docx_to_markdown_returns_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.docx"
            source.write_text("placeholder", encoding="utf-8")
            fake_converter = Mock()
            fake_converter.convert.return_value.text_content = "# Title"

            result = convert_docx_to_markdown(source, fake_converter)

        self.assertEqual(result, "# Title")
        fake_converter.convert.assert_called_once_with(str(source), keep_data_uris=True)

    def test_convert_docx_to_markdown_supports_older_converter_api(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "sample.docx"
            source.write_text("placeholder", encoding="utf-8")
            fake_converter = Mock()
            fake_converter.convert.side_effect = [
                TypeError("unexpected keyword argument 'keep_data_uris'"),
                Mock(text_content="# Title"),
            ]

            result = convert_docx_to_markdown(source, fake_converter)

        self.assertEqual(result, "# Title")
        self.assertEqual(fake_converter.convert.call_count, 2)
        fake_converter.convert.assert_called_with(str(source))


if __name__ == "__main__":
    unittest.main()
