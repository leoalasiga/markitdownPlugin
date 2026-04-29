import importlib
import asyncio
from pathlib import Path
from types import SimpleNamespace
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

    def test_file_picker_skips_removed_result_handler_for_flet_084(self) -> None:
        gui = importlib.import_module("src.gui")

        class FilePicker:
            __slots__ = ()

        FakeFlet = type("FakeFlet", (), {"FilePicker": FilePicker})

        picker = gui._create_file_picker(FakeFlet, object())

        self.assertFalse(hasattr(picker, "on_result"))

    def test_alignment_center_prefers_flet_084_constant(self) -> None:
        gui = importlib.import_module("src.gui")
        center = object()
        FakeFlet = type(
            "FakeFlet",
            (),
            {
                "Alignment": type("Alignment", (), {"CENTER": center}),
                "alignment": SimpleNamespace(),
            },
        )

        self.assertIs(gui._alignment_center(FakeFlet), center)

    def test_alignment_center_falls_back_to_legacy_module_constant(self) -> None:
        gui = importlib.import_module("src.gui")
        center = object()
        FakeFlet = type("FakeFlet", (), {"alignment": SimpleNamespace(center=center)})

        self.assertIs(gui._alignment_center(FakeFlet), center)

    def test_window_settings_use_flet_084_page_window(self) -> None:
        gui = importlib.import_module("src.gui")
        page = SimpleNamespace(window=SimpleNamespace())

        gui._set_window_value(page, "window_width", "width", 1120)

        self.assertEqual(page.window.width, 1120)
        self.assertFalse(hasattr(page, "window_width"))

    def test_converter_app_builds_with_flet_084_surface(self) -> None:
        gui = importlib.import_module("src.gui")

        class Control:
            def __init__(self, *args, **kwargs) -> None:
                self.args = args
                self.controls = list(kwargs.pop("controls", []))
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def update(self) -> None:
                pass

        class FilePicker:
            __slots__ = ()

            async def pick_files(self, **_kwargs):
                return []

            async def get_directory_path(self, **_kwargs):
                return None

        class FakePage:
            def __init__(self) -> None:
                self.overlay = []
                self.controls = []
                self.window = SimpleNamespace()

            def add(self, control) -> None:
                self.controls.append(control)

            def update(self) -> None:
                pass

            def run_thread(self, _handler) -> None:
                pass

            def show_dialog(self, dialog) -> None:
                self.dialog = dialog
                dialog.open = True

            def pop_dialog(self) -> None:
                self.dialog.open = False

        FakeFlet = type(
            "FakeFlet",
            (),
            {
                "Alignment": type("Alignment", (), {"CENTER": "center"}),
                "AlertDialog": Control,
                "ButtonStyle": Control,
                "Column": Control,
                "Container": Control,
                "Divider": Control,
                "FilePicker": FilePicker,
                "FilledButton": Control,
                "Icon": Control,
                "IconButton": Control,
                "OutlinedButton": Control,
                "ProgressBar": Control,
                "Radio": Control,
                "RadioGroup": Control,
                "RoundedRectangleBorder": Control,
                "Row": Control,
                "Text": Control,
                "TextButton": Control,
                "TextField": Control,
                "border": SimpleNamespace(all=lambda *args: ("border", args)),
                "padding": SimpleNamespace(symmetric=lambda **kwargs: ("padding", kwargs)),
            },
        )

        app = gui.ConverterApp(FakePage(), FakeFlet)

        self.assertEqual(app.center_alignment, "center")
        self.assertEqual(app.page.overlay, [])
        self.assertEqual(app.page.window.width, 1120)
        self.assertTrue(app.page.controls)

    def test_flet_084_file_picker_results_are_consumed_directly(self) -> None:
        gui = importlib.import_module("src.gui")

        class FilePicker:
            async def pick_files(self, **_kwargs):
                return [SimpleNamespace(path="/tmp/example.docx")]

        app = SimpleNamespace(
            running=False,
            file_picker=FilePicker(),
            files=[],
            _refresh_all=lambda: None,
            _append_log=lambda _message: None,
        )
        app._add_selected_files = gui.ConverterApp._add_selected_files.__get__(app)

        asyncio.run(gui.ConverterApp.add_files(app))

        self.assertEqual([item.path.name for item in app.files], ["example.docx"])

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
        self.assertIn("flet>=0.84.0,<0.90.0", requirements.lower())


if __name__ == "__main__":
    unittest.main()
