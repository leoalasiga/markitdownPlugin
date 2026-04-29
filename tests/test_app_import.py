import importlib
from pathlib import Path
import unittest


class AppImportTests(unittest.TestCase):
    def test_app_module_imports_without_gui_side_effects(self) -> None:
        module = importlib.import_module("app")
        self.assertTrue(callable(module.main))

    def test_gui_exposes_flet_app_entrypoint(self) -> None:
        gui = importlib.import_module("src.gui")
        self.assertTrue(callable(gui.main))
        self.assertTrue(hasattr(gui, "ConverterApp"))

    def test_requirements_declares_flet(self) -> None:
        requirements = Path("requirements.txt").read_text(encoding="utf-8")
        self.assertIn("flet", requirements.lower())


if __name__ == "__main__":
    unittest.main()
