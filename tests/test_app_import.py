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

    def test_file_picker_binds_result_handler_without_constructor_keyword(self) -> None:
        gui = importlib.import_module("src.gui")

        class FilePicker:
            def __init__(self) -> None:
                self.on_result = None

        FakeFlet = type("FakeFlet", (), {"FilePicker": FilePicker})

        handler = object()
        picker = gui._create_file_picker(FakeFlet, handler)

        self.assertIs(picker.on_result, handler)

    def test_button_factory_uses_content_keyword_for_current_flet(self) -> None:
        gui = importlib.import_module("src.gui")

        class Button:
            def __init__(self, *, content=None, icon=None, on_click=None, disabled=None, style=None) -> None:
                self.content = content
                self.icon = icon
                self.on_click = on_click
                self.disabled = disabled
                self.style = style

        FakeFlet = type("FakeFlet", (), {"FilledButton": Button})
        handler = object()

        button = gui._create_button(
            FakeFlet,
            "FilledButton",
            "Start",
            icon="play",
            on_click=handler,
            disabled=True,
            style="style",
        )

        self.assertEqual(button.content, "Start")
        self.assertEqual(button.icon, "play")
        self.assertIs(button.on_click, handler)
        self.assertTrue(button.disabled)
        self.assertEqual(button.style, "style")

    def test_button_factory_falls_back_to_text_keyword_for_older_flet(self) -> None:
        gui = importlib.import_module("src.gui")

        class Button:
            def __init__(self, *, text=None, icon=None, on_click=None) -> None:
                self.text = text
                self.icon = icon
                self.on_click = on_click

        FakeFlet = type("FakeFlet", (), {"OutlinedButton": Button})
        handler = object()

        button = gui._create_button(FakeFlet, "OutlinedButton", "Open", icon="folder", on_click=handler)

        self.assertEqual(button.text, "Open")
        self.assertEqual(button.icon, "folder")
        self.assertIs(button.on_click, handler)

    def test_requirements_declares_flet(self) -> None:
        requirements = Path("requirements.txt").read_text(encoding="utf-8")
        self.assertIn("flet", requirements.lower())


if __name__ == "__main__":
    unittest.main()
