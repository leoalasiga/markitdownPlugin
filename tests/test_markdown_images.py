import tempfile
import unittest
from pathlib import Path

from src.markdown_images import process_markdown


class MarkdownImagesTests(unittest.TestCase):
    def test_process_markdown_extracts_angle_wrapped_data_uri(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"

            content, stats = process_markdown(
                "![](<data:image/png;base64,aGk=>)",
                images_dir,
                "images",
            )

            self.assertEqual(content, "![](images/image_001.png)")
            self.assertEqual(stats.matched, 1)
            self.assertEqual((images_dir / "image_001.png").read_bytes(), b"hi")

    def test_process_markdown_removes_word_object_placeholder_before_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"

            content, stats = process_markdown(
                "\ufffd![](data:image/png;base64,aGk=)",
                images_dir,
                "images",
            )

            self.assertEqual(content, "![](images/image_001.png)")
            self.assertEqual(stats.matched, 1)
            self.assertEqual((images_dir / "image_001.png").read_bytes(), b"hi")

    def test_process_markdown_extracts_data_uri_with_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"

            content, stats = process_markdown(
                '![](data:image/png;base64,aGk= "workflow")',
                images_dir,
                "images",
            )

            self.assertEqual(content, "![](images/image_001.png)")
            self.assertEqual(stats.matched, 1)
            self.assertEqual((images_dir / "image_001.png").read_bytes(), b"hi")

    def test_process_markdown_extracts_html_img_data_uri(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            images_dir = Path(temp_dir) / "images"

            content, stats = process_markdown(
                '<img alt="workflow" src="data:image/png;base64,aGk=" />',
                images_dir,
                "images",
            )

            self.assertEqual(content, "![workflow](images/image_001.png)")
            self.assertEqual(stats.matched, 1)
            self.assertEqual((images_dir / "image_001.png").read_bytes(), b"hi")


if __name__ == "__main__":
    unittest.main()
