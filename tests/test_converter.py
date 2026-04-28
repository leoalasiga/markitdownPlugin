import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.converter import convert_one


class ConverterTests(unittest.TestCase):
    def test_convert_one_routes_docx_without_libreoffice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "report.docx"
            source.write_text("placeholder", encoding="utf-8")
            writer = Mock()
            markdown_converter = Mock(return_value="# Report")

            result = convert_one(
                source_path=source,
                output_dir=None,
                markdown_converter=markdown_converter,
                doc_bridge=None,
                writer=writer,
            )

        self.assertTrue(result.success)
        writer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
