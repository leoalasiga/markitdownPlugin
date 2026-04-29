from pathlib import Path
import unittest


class PyInstallerSpecTests(unittest.TestCase):
    def test_spec_collects_magika_model_data_explicitly(self) -> None:
        spec = Path("markitdown_tool.spec").read_text(encoding="utf-8")

        self.assertIn("collect_data_files", spec)
        self.assertIn('collect_data_files("magika")', spec)
        self.assertIn("find_spec", spec)
        self.assertIn("standard_v3_3", spec)
        self.assertIn("model.onnx", spec)
        self.assertIn('"flet"', spec)


if __name__ == "__main__":
    unittest.main()
