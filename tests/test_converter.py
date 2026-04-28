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

    def test_convert_one_extracts_inline_images_next_to_output_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "report.docx"
            source.write_text("placeholder", encoding="utf-8")
            markdown_converter = Mock(
                return_value="# Report\n\n![chart](data:image/png;base64,aGVsbG8=)\n"
            )

            result = convert_one(
                source_path=source,
                output_dir=root / "exports",
                markdown_converter=markdown_converter,
            )

            output_path = root / "exports" / "report.md"
            image_path = root / "exports" / "images" / "image_001.png"

            self.assertTrue(result.success)
            self.assertEqual(result.output_path, output_path)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "# Report\n\n![chart](images/image_001.png)\n",
            )
            self.assertEqual(image_path.read_bytes(), b"hello")


if __name__ == "__main__":
    unittest.main()
