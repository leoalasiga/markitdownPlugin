from pathlib import Path
import unittest


class PyInstallerSpecTests(unittest.TestCase):
    def test_spec_collects_magika_model_data(self) -> None:
        spec = Path("markitdown_tool.spec").read_text(encoding="utf-8")

        self.assertIn("collect_data_files", spec)
        self.assertIn('collect_data_files("magika")', spec)


if __name__ == "__main__":
    unittest.main()
