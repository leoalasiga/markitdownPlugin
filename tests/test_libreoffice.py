import unittest

from src.libreoffice import build_soffice_command


class LibreOfficeTests(unittest.TestCase):
    def test_build_soffice_command_targets_docx_output(self) -> None:
        command = build_soffice_command("C:/docs/a.doc", "C:/temp")
        self.assertIn("--headless", command)
        self.assertIn("--convert-to", command)
        self.assertIn("docx", command)


if __name__ == "__main__":
    unittest.main()
