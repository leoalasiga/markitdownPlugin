from pathlib import Path
import unittest

from src.utils import (
    MARKITDOWN_NATIVE_EXTENSIONS,
    build_output_path,
    get_output_folder_for_open,
    is_supported_file,
)


class UtilsTests(unittest.TestCase):
    def test_is_supported_file_accepts_markitdown_local_formats(self) -> None:
        self.assertTrue(is_supported_file("a.doc"))
        self.assertTrue(is_supported_file("b.docx"))
        for extension in MARKITDOWN_NATIVE_EXTENSIONS:
            self.assertTrue(is_supported_file(f"sample{extension}"))
        self.assertFalse(is_supported_file("c.exe"))

    def test_build_output_path_uses_custom_directory(self) -> None:
        result = build_output_path("/tmp/invoice.docx", "/exports")
        self.assertEqual(str(result), "/exports/invoice.md")

    def test_get_output_folder_for_open_uses_custom_directory(self) -> None:
        result = get_output_folder_for_open(
            [Path("/tmp/invoice.docx")],
            output_mode="custom",
            custom_output_dir="/exports",
        )
        self.assertEqual(result, Path("/exports"))

    def test_get_output_folder_for_open_uses_source_parent_for_single_file(self) -> None:
        result = get_output_folder_for_open(
            [Path("/tmp/reports/invoice.docx")],
            output_mode="source",
            custom_output_dir="",
        )
        self.assertEqual(result, Path("/tmp/reports"))

    def test_get_output_folder_for_open_returns_none_for_multi_source_mode(self) -> None:
        result = get_output_folder_for_open(
            [Path("/tmp/a.docx"), Path("/tmp/b.docx")],
            output_mode="source",
            custom_output_dir="",
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
