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


if __name__ == "__main__":
    unittest.main()
