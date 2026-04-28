import unittest

from src.utils import build_output_path, is_supported_file


class UtilsTests(unittest.TestCase):
    def test_is_supported_file_accepts_doc_and_docx(self) -> None:
        self.assertTrue(is_supported_file("a.doc"))
        self.assertTrue(is_supported_file("b.docx"))
        self.assertFalse(is_supported_file("c.txt"))

    def test_build_output_path_uses_custom_directory(self) -> None:
        result = build_output_path("/tmp/invoice.docx", "/exports")
        self.assertEqual(str(result), "/exports/invoice.md")


if __name__ == "__main__":
    unittest.main()
