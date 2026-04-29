import os
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.converter import convert_one
from src.libreoffice import find_soffice
from src.utils import get_output_folder_for_open, is_doc_file, is_supported_file


@dataclass
class FileItem:
    path: Path
    status: str = "Waiting"
    selected: bool = False


class ConverterApp:
    def __init__(self, page: Any, ft_module: Any) -> None:
        self.page = page
        self.ft = ft_module
        self.icons = getattr(self.ft, "Icons", getattr(self.ft, "icons", None))

        self.files: list[FileItem] = []
        self.output_mode = "source"
        self.custom_output_dir = ""
        self.running = False
        self.results_queue: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self.file_picker = self.ft.FilePicker(on_result=self._on_files_selected)
        self.folder_picker = self.ft.FilePicker(on_result=self._on_folder_selected)
        self.page.overlay.extend([self.file_picker, self.folder_picker])

        self.status_text = self.ft.Text("Ready", size=13, color="#64748b")
        self.summary_text = self.ft.Text("Add .doc or .docx files to begin.", size=14, color="#475569")
        self.file_list = self.ft.Column(spacing=10, scroll="auto", expand=True)
        self.log_list = self.ft.Column(spacing=8, scroll="auto", expand=True)
        self.progress = self.ft.ProgressBar(value=0, height=7, color="#0f9f9a", bgcolor="#e2e8f0")
        self.custom_output_field = self.ft.TextField(
            value="",
            hint_text="Choose an output folder",
            read_only=True,
            dense=True,
            border_radius=8,
            expand=True,
            bgcolor="#ffffff",
        )

        self.start_button = self.ft.FilledButton(
            text="Start Conversion",
            icon=self._icon("PLAY_ARROW"),
            on_click=self.start_conversion,
            style=self.ft.ButtonStyle(
                bgcolor="#0f766e",
                color="#ffffff",
                shape=self.ft.RoundedRectangleBorder(radius=8),
            ),
        )
        self.choose_folder_button = self.ft.OutlinedButton(
            text="Choose Folder",
            icon=self._icon("FOLDER_OPEN"),
            on_click=self.choose_output_directory,
            disabled=True,
        )
        self.clear_button = self.ft.OutlinedButton(
            text="Clear",
            icon=self._icon("DELETE_OUTLINE"),
            on_click=self.clear_files,
        )
        self.open_output_button = self.ft.OutlinedButton(
            text="Open Output",
            icon=self._icon("OPEN_IN_NEW"),
            on_click=self.open_output_folder,
        )

        self._configure_page()
        self._build_ui()
        self._append_log("Ready. Add Word files, choose output options, then start conversion.")
        self.page.run_thread(self._poll_results)

    def _configure_page(self) -> None:
        self.page.title = "MarkItDown Converter"
        self.page.window_width = 1120
        self.page.window_height = 760
        self.page.window_min_width = 940
        self.page.window_min_height = 640
        self.page.padding = 0
        self.page.bgcolor = "#eef3f7"
        self.page.theme_mode = "light"

    def _build_ui(self) -> None:
        self.page.controls.clear()
        self.page.add(
            self.ft.Row(
                controls=[
                    self._sidebar(),
                    self.ft.Container(
                        expand=True,
                        padding=self.ft.padding.symmetric(horizontal=28, vertical=24),
                        content=self.ft.Column(
                            controls=[
                                self._header(),
                                self._content_grid(),
                            ],
                            spacing=18,
                            expand=True,
                        ),
                    ),
                ],
                spacing=0,
                expand=True,
            )
        )
        self._refresh_all()

    def _sidebar(self) -> Any:
        nav_items = [
            ("AUTO_AWESOME", "Convert", True),
            ("HISTORY", "History", False),
            ("SETTINGS", "Settings", False),
        ]
        return self.ft.Container(
            width=232,
            bgcolor="#102a43",
            padding=self.ft.padding.symmetric(horizontal=18, vertical=22),
            content=self.ft.Column(
                controls=[
                    self.ft.Row(
                        controls=[
                            self.ft.Container(
                                width=38,
                                height=38,
                                border_radius=8,
                                bgcolor="#14b8a6",
                                alignment=self.ft.alignment.center,
                                content=self.ft.Icon(self._icon("DESCRIPTION"), color="#ffffff", size=22),
                            ),
                            self.ft.Column(
                                controls=[
                                    self.ft.Text("MarkItDown", size=18, weight="w700", color="#ffffff"),
                                    self.ft.Text("Document Studio", size=12, color="#9fb3c8"),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=10,
                    ),
                    self.ft.Container(height=18),
                    *[self._nav_item(icon, label, active) for icon, label, active in nav_items],
                    self.ft.Container(expand=True),
                    self.ft.Container(
                        padding=14,
                        border_radius=8,
                        bgcolor="#173a5e",
                        content=self.ft.Column(
                            controls=[
                                self.ft.Text("Engine", size=12, color="#9fb3c8"),
                                self.ft.Text("Flet + Python", size=14, color="#ffffff", weight="w600"),
                                self.ft.Text("MarkItDown core unchanged", size=12, color="#bfd3e6"),
                            ],
                            spacing=5,
                        ),
                    ),
                ],
                spacing=8,
                expand=True,
            ),
        )

    def _nav_item(self, icon_name: str, label: str, active: bool) -> Any:
        return self.ft.Container(
            height=44,
            border_radius=8,
            padding=self.ft.padding.symmetric(horizontal=12),
            bgcolor="#14b8a6" if active else None,
            content=self.ft.Row(
                controls=[
                    self.ft.Icon(self._icon(icon_name), size=19, color="#ffffff" if active else "#9fb3c8"),
                    self.ft.Text(label, size=14, color="#ffffff" if active else "#c8d8e8", weight="w600" if active else "w500"),
                ],
                spacing=10,
                vertical_alignment="center",
            ),
        )

    def _header(self) -> Any:
        return self.ft.Row(
            controls=[
                self.ft.Column(
                    controls=[
                        self.ft.Text("Document to Markdown", size=28, weight="w700", color="#102a43"),
                        self.ft.Text(
                            "Convert Word documents with a cleaner desktop workflow.",
                            size=14,
                            color="#64748b",
                        ),
                    ],
                    spacing=3,
                    expand=True,
                ),
                self.ft.Container(
                    padding=self.ft.padding.symmetric(horizontal=14, vertical=10),
                    border_radius=8,
                    bgcolor="#ffffff",
                    border=self.ft.border.all(1, "#dbe4ee"),
                    content=self.ft.Row(
                        controls=[
                            self.ft.Icon(self._icon("CHECK_CIRCLE_OUTLINE"), color="#0f9f9a", size=20),
                            self.status_text,
                        ],
                        spacing=8,
                    ),
                ),
            ],
            vertical_alignment="center",
        )

    def _content_grid(self) -> Any:
        return self.ft.Row(
            controls=[
                self.ft.Container(
                    expand=3,
                    content=self.ft.Column(
                        controls=[
                            self._file_card(),
                            self._output_card(),
                        ],
                        spacing=16,
                        expand=True,
                    ),
                ),
                self.ft.Container(
                    width=360,
                    content=self._activity_card(),
                ),
            ],
            spacing=18,
            expand=True,
        )

    def _file_card(self) -> Any:
        return self.ft.Container(
            expand=True,
            border_radius=8,
            bgcolor="#ffffff",
            border=self.ft.border.all(1, "#dbe4ee"),
            padding=18,
            content=self.ft.Column(
                controls=[
                    self.ft.Row(
                        controls=[
                            self.ft.Column(
                                controls=[
                                    self.ft.Text("Files", size=18, weight="w700", color="#102a43"),
                                    self.ft.Text("Supports .doc and .docx. Duplicates are skipped.", size=13, color="#64748b"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            self.ft.FilledButton(
                                text="Add Files",
                                icon=self._icon("UPLOAD_FILE"),
                                on_click=self.add_files,
                                style=self.ft.ButtonStyle(
                                    bgcolor="#102a43",
                                    color="#ffffff",
                                    shape=self.ft.RoundedRectangleBorder(radius=8),
                                ),
                            ),
                        ],
                        vertical_alignment="center",
                    ),
                    self.ft.Container(
                        height=112,
                        border_radius=8,
                        bgcolor="#f8fafc",
                        border=self.ft.border.all(1, "#cbd5e1"),
                        on_click=self.add_files,
                        content=self.ft.Column(
                            controls=[
                                self.ft.Icon(self._icon("DRIVE_FOLDER_UPLOAD"), color="#0f766e", size=34),
                                self.ft.Text("Click to select Word documents", size=15, weight="w600", color="#102a43"),
                                self.ft.Text("Batch conversion is supported.", size=12, color="#64748b"),
                            ],
                            spacing=4,
                            alignment="center",
                            horizontal_alignment="center",
                        ),
                    ),
                    self.file_list,
                ],
                spacing=14,
                expand=True,
            ),
        )

    def _output_card(self) -> Any:
        return self.ft.Container(
            border_radius=8,
            bgcolor="#ffffff",
            border=self.ft.border.all(1, "#dbe4ee"),
            padding=18,
            content=self.ft.Column(
                controls=[
                    self.ft.Text("Output", size=18, weight="w700", color="#102a43"),
                    self.ft.RadioGroup(
                        value=self.output_mode,
                        on_change=self._on_output_mode_change,
                        content=self.ft.Column(
                            controls=[
                                self.ft.Radio(value="source", label="Save beside each source file"),
                                self.ft.Radio(value="custom", label="Save every file to one folder"),
                            ],
                            spacing=2,
                        ),
                    ),
                    self.ft.Row(
                        controls=[self.custom_output_field, self.choose_folder_button],
                        spacing=10,
                        vertical_alignment="center",
                    ),
                ],
                spacing=10,
            ),
        )

    def _activity_card(self) -> Any:
        return self.ft.Container(
            border_radius=8,
            bgcolor="#ffffff",
            border=self.ft.border.all(1, "#dbe4ee"),
            padding=18,
            content=self.ft.Column(
                controls=[
                    self.ft.Text("Run", size=18, weight="w700", color="#102a43"),
                    self.summary_text,
                    self.progress,
                    self.ft.Row(
                        controls=[
                            self.start_button,
                            self.clear_button,
                        ],
                        spacing=10,
                    ),
                    self.open_output_button,
                    self.ft.Divider(height=18, color="#e2e8f0"),
                    self.ft.Text("Activity", size=14, weight="w700", color="#102a43"),
                    self.log_list,
                ],
                spacing=12,
                expand=True,
            ),
        )

    def add_files(self, _event: Any = None) -> None:
        if self.running:
            return
        self.file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=["doc", "docx"],
            dialog_title="Select Word files",
        )

    def _on_files_selected(self, event: Any) -> None:
        if not event.files:
            return
        existing = {str(item.path) for item in self.files}
        for selected in event.files:
            if not selected.path:
                continue
            path = Path(selected.path)
            resolved = str(path)
            if not is_supported_file(resolved):
                self._append_log(f"Skipped unsupported file: {resolved}")
                continue
            if resolved in existing:
                self._append_log(f"Skipped duplicate file: {resolved}")
                continue
            self.files.append(FileItem(path=path))
            existing.add(resolved)
        self._refresh_all()

    def choose_output_directory(self, _event: Any = None) -> None:
        if self.running:
            return
        self.folder_picker.get_directory_path(dialog_title="Choose output folder")

    def _on_folder_selected(self, event: Any) -> None:
        if event.path:
            self.custom_output_dir = event.path
            self.custom_output_field.value = event.path
            self._refresh_all()

    def _on_output_mode_change(self, event: Any) -> None:
        self.output_mode = event.control.value
        self._refresh_all()

    def clear_files(self, _event: Any = None) -> None:
        if self.running:
            return
        self.files.clear()
        self._append_log("Cleared selected files.")
        self._refresh_all()

    def remove_file(self, path: Path) -> None:
        if self.running:
            return
        self.files = [item for item in self.files if item.path != path]
        self._append_log(f"Removed: {path.name}")
        self._refresh_all()

    def open_output_folder(self, _event: Any = None) -> None:
        source_paths = [item.path for item in self.files]
        output_dir = get_output_folder_for_open(source_paths, self.output_mode, self.custom_output_dir.strip())
        if not output_dir:
            self._show_message(
                "Output folder",
                "In source-folder mode, open output folder works after adding exactly one file. For multiple files, use one output folder.",
            )
            return

        target = Path(output_dir)
        if not target.exists():
            self._show_message("Output folder", "The selected output folder does not exist yet.")
            return

        if os.name == "nt":
            os.startfile(target)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])

    def start_conversion(self, _event: Any = None) -> None:
        if self.running:
            return
        source_paths = [item.path for item in self.files]
        if not source_paths:
            self._show_message("No files", "Select at least one .doc or .docx file.")
            return

        output_dir: str | None
        if self.output_mode == "custom":
            output_dir = self.custom_output_dir.strip()
            if not output_dir:
                self._show_message("Output folder", "Choose an output folder before starting.")
                return
            if not Path(output_dir).exists():
                self._show_message("Output folder", "The selected output folder does not exist.")
                return
        else:
            output_dir = None

        if any(is_doc_file(path) for path in source_paths) and not find_soffice():
            self._show_message(
                "LibreOffice required",
                "At least one .doc file needs LibreOffice. Install LibreOffice and make sure soffice is in PATH.",
            )
            return

        for item in self.files:
            item.status = "Queued"
        self.running = True
        self._append_log("Starting conversion run.")
        self._refresh_all()

        self.worker_thread = threading.Thread(
            target=self._run_conversion_batch,
            args=(source_paths, output_dir),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_conversion_batch(self, source_paths: list[Path], output_dir: str | None) -> None:
        success_count = 0
        failure_count = 0

        for source_path in source_paths:
            self.results_queue.put(("status", {"path": str(source_path), "status": "Converting"}))
            result = convert_one(source_path=source_path, output_dir=output_dir)
            if result.success:
                success_count += 1
                self.results_queue.put(("status", {"path": str(source_path), "status": "Success"}))
                self.results_queue.put(("log", {"message": f"SUCCESS: {source_path.name} -> {result.output_path}"}))
            else:
                failure_count += 1
                message = result.message
                if isinstance(message, str) and "LibreOffice soffice was not found" in message:
                    message = "LibreOffice was not found in PATH."
                self.results_queue.put(("status", {"path": str(source_path), "status": "Failed"}))
                self.results_queue.put(("log", {"message": f"FAILED: {source_path.name} -> {message}"}))

        self.results_queue.put(("done", {"success": success_count, "failure": failure_count}))

    def _poll_results(self) -> None:
        while True:
            changed = False
            while True:
                try:
                    event_type, payload = self.results_queue.get_nowait()
                except queue.Empty:
                    break

                changed = True
                if event_type == "status":
                    self._set_file_status(payload["path"], payload["status"])
                elif event_type == "log":
                    self._append_log(payload["message"], update=False)
                elif event_type == "done":
                    self.running = False
                    self._append_log(
                        f"Finished. Success: {payload['success']}, Failed: {payload['failure']}",
                        update=False,
                    )

            if changed:
                self._refresh_all()
            time.sleep(0.15)

    def _set_file_status(self, file_path: str, status: str) -> None:
        for item in self.files:
            if str(item.path) == file_path:
                item.status = status
                return

    def _refresh_all(self) -> None:
        self._refresh_file_list()
        self._refresh_controls()
        self._refresh_summary()
        self.page.update()

    def _refresh_file_list(self) -> None:
        if not self.files:
            self.file_list.controls = [
                self.ft.Container(
                    height=72,
                    border_radius=8,
                    bgcolor="#f8fafc",
                    alignment=self.ft.alignment.center,
                    content=self.ft.Text("No files selected yet.", size=13, color="#64748b"),
                )
            ]
            return
        self.file_list.controls = [self._file_row(item) for item in self.files]

    def _file_row(self, item: FileItem) -> Any:
        return self.ft.Container(
            border_radius=8,
            bgcolor="#f8fafc",
            border=self.ft.border.all(1, "#e2e8f0"),
            padding=self.ft.padding.symmetric(horizontal=12, vertical=10),
            content=self.ft.Row(
                controls=[
                    self.ft.Icon(self._file_icon(item.path), color="#0f766e", size=24),
                    self.ft.Column(
                        controls=[
                            self.ft.Text(item.path.name, size=14, weight="w700", color="#102a43", no_wrap=True),
                            self.ft.Text(str(item.path.parent), size=12, color="#64748b", no_wrap=True),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    self._status_chip(item.status),
                    self.ft.IconButton(
                        icon=self._icon("CLOSE"),
                        icon_color="#64748b",
                        tooltip="Remove",
                        disabled=self.running,
                        on_click=lambda _event, path=item.path: self.remove_file(path),
                    ),
                ],
                spacing=10,
                vertical_alignment="center",
            ),
        )

    def _status_chip(self, status: str) -> Any:
        colors = {
            "Waiting": ("#e2e8f0", "#475569"),
            "Queued": ("#dbeafe", "#1d4ed8"),
            "Converting": ("#ccfbf1", "#0f766e"),
            "Success": ("#dcfce7", "#15803d"),
            "Failed": ("#fee2e2", "#b91c1c"),
        }
        bgcolor, color = colors.get(status, ("#e2e8f0", "#475569"))
        return self.ft.Container(
            width=96,
            height=28,
            border_radius=8,
            bgcolor=bgcolor,
            alignment=self.ft.alignment.center,
            content=self.ft.Text(status, size=12, color=color, weight="w700"),
        )

    def _refresh_controls(self) -> None:
        custom_mode = self.output_mode == "custom"
        self.custom_output_field.disabled = not custom_mode
        self.choose_folder_button.disabled = self.running or not custom_mode
        self.start_button.disabled = self.running
        self.clear_button.disabled = self.running or not self.files
        self.open_output_button.disabled = self.running

    def _refresh_summary(self) -> None:
        total = len(self.files)
        finished = sum(1 for item in self.files if item.status in {"Success", "Failed"})
        failures = sum(1 for item in self.files if item.status == "Failed")
        successes = sum(1 for item in self.files if item.status == "Success")

        if self.running:
            self.status_text.value = "Running conversion"
            self.summary_text.value = f"{finished}/{total} files processed"
        elif total == 0:
            self.status_text.value = "Ready"
            self.summary_text.value = "Add .doc or .docx files to begin."
        elif finished == total and total > 0 and (successes or failures):
            self.status_text.value = "Finished"
            self.summary_text.value = f"Finished. Success: {successes}, Failed: {failures}"
        else:
            self.status_text.value = "Ready"
            self.summary_text.value = f"{total} file(s) selected."

        self.progress.value = 0 if total == 0 else finished / total

    def _append_log(self, message: str, update: bool = True) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_list.controls.append(
            self.ft.Container(
                border_radius=8,
                bgcolor="#f8fafc",
                padding=self.ft.padding.symmetric(horizontal=10, vertical=8),
                content=self.ft.Column(
                    controls=[
                        self.ft.Text(timestamp, size=11, color="#94a3b8"),
                        self.ft.Text(message, size=12, color="#334155", selectable=True),
                    ],
                    spacing=2,
                ),
            )
        )
        if len(self.log_list.controls) > 80:
            self.log_list.controls = self.log_list.controls[-80:]
        if update:
            self.page.update()

    def _show_message(self, title: str, message: str) -> None:
        dialog = self.ft.AlertDialog(
            modal=True,
            title=self.ft.Text(title),
            content=self.ft.Text(message),
            actions=[
                self.ft.TextButton(
                    "OK",
                    on_click=lambda _event: self._close_dialog(dialog),
                )
            ],
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _close_dialog(self, dialog: Any) -> None:
        dialog.open = False
        self.page.update()

    def _file_icon(self, path: Path) -> Any:
        return self._icon("ARTICLE") if path.suffix.lower() == ".docx" else self._icon("DESCRIPTION")

    def _icon(self, name: str) -> Any:
        if self.icons is None:
            return name
        return getattr(self.icons, name, name)


def _load_flet() -> Any:
    try:
        import flet as ft
    except ModuleNotFoundError as exc:
        if exc.name == "flet":
            raise ModuleNotFoundError(
                "Flet is not installed. Run: py -m pip install -r requirements.txt"
            ) from exc
        raise
    return ft


def _run(page: Any) -> None:
    ft = _load_flet()
    ConverterApp(page, ft)


def main() -> None:
    ft = _load_flet()
    ft.app(target=lambda page: ConverterApp(page, ft))
