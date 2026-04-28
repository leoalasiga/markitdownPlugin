import os
import queue
import subprocess
import threading
from pathlib import Path
from tkinter import END, BOTH, DISABLED, NORMAL, StringVar, Text, Tk, filedialog, messagebox
from tkinter import ttk

from src.converter import convert_one
from src.libreoffice import find_soffice
from src.utils import get_output_folder_for_open, is_doc_file, is_supported_file


class ConverterApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("MarkItDown Converter")
        self.root.geometry("900x620")
        self.root.minsize(780, 520)

        self.output_mode = StringVar(value="source")
        self.custom_output_dir = StringVar(value="")
        self.summary_text = StringVar(value="Ready.")

        self.file_rows: dict[str, str] = {}
        self.results_queue: queue.Queue[tuple[str, dict]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self._build_ui()
        self._schedule_queue_poll()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=BOTH, expand=True)

        hint_text = (
            "Tip: .docx converts directly. .doc needs LibreOffice installed and available as soffice."
        )
        ttk.Label(container, text=hint_text, foreground="#4b5563").pack(fill="x", pady=(0, 10))

        self._build_file_section(container)
        self._build_output_section(container)
        self._build_execution_section(container)

    def _build_file_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Files", padding=10)
        frame.pack(fill=BOTH, expand=True, pady=(0, 12))

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x", pady=(0, 10))

        self.add_button = ttk.Button(button_row, text="Add Files", command=self.add_files)
        self.add_button.pack(side="left")
        self.remove_button = ttk.Button(button_row, text="Remove Selected", command=self.remove_selected_files)
        self.remove_button.pack(side="left", padx=(8, 0))
        self.clear_button = ttk.Button(button_row, text="Clear List", command=self.clear_files)
        self.clear_button.pack(side="left", padx=(8, 0))

        columns = ("path", "status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        self.tree.heading("path", text="File")
        self.tree.heading("status", text="Status")
        self.tree.column("path", width=670, anchor="w")
        self.tree.column("status", width=140, anchor="center")
        self.tree.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1.0, rely=0.14, relheight=0.84, anchor="ne")

    def _build_output_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Output", padding=10)
        frame.pack(fill="x", pady=(0, 12))

        ttk.Radiobutton(
            frame,
            text="Save beside each source file",
            value="source",
            variable=self.output_mode,
            command=self._update_output_controls,
        ).grid(row=0, column=0, sticky="w")

        ttk.Radiobutton(
            frame,
            text="Save all files to this folder",
            value="custom",
            variable=self.output_mode,
            command=self._update_output_controls,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.output_dir_entry = ttk.Entry(frame, textvariable=self.custom_output_dir, width=80, state=DISABLED)
        self.output_dir_entry.grid(row=1, column=1, sticky="ew", padx=(12, 8), pady=(8, 0))

        self.choose_output_button = ttk.Button(
            frame,
            text="Choose Folder",
            command=self.choose_output_directory,
            state=DISABLED,
        )
        self.choose_output_button.grid(row=1, column=2, pady=(8, 0))

        frame.columnconfigure(1, weight=1)

    def _build_execution_section(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Execution", padding=10)
        frame.pack(fill=BOTH, expand=True)

        action_row = ttk.Frame(frame)
        action_row.pack(fill="x", pady=(0, 10))

        self.start_button = ttk.Button(action_row, text="Start Conversion", command=self.start_conversion)
        self.start_button.pack(side="left")

        self.open_output_button = ttk.Button(action_row, text="Open Output Folder", command=self.open_output_folder)
        self.open_output_button.pack(side="left", padx=(8, 0))

        ttk.Label(action_row, textvariable=self.summary_text).pack(side="left", padx=(16, 0))

        self.log_text = Text(frame, height=12, wrap="word", state=DISABLED)
        self.log_text.pack(fill=BOTH, expand=True)

    def run(self) -> None:
        self.root.mainloop()

    def add_files(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="Select Word files",
            filetypes=[("Word files", "*.doc *.docx"), ("All files", "*.*")],
        )
        for file_path in file_paths:
            self._add_file_row(Path(file_path))

    def remove_selected_files(self) -> None:
        for item_id in self.tree.selection():
            file_path = self.tree.set(item_id, "path")
            self.tree.delete(item_id)
            self.file_rows.pop(file_path, None)
        self._refresh_summary()

    def clear_files(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)
        self.file_rows.clear()
        self.summary_text.set("Ready.")

    def choose_output_directory(self) -> None:
        selected_dir = filedialog.askdirectory(title="Choose output folder")
        if selected_dir:
            self.custom_output_dir.set(selected_dir)

    def open_output_folder(self) -> None:
        source_paths = [Path(self.tree.set(item_id, "path")) for item_id in self.tree.get_children()]
        output_dir = get_output_folder_for_open(source_paths, self.output_mode.get(), self.custom_output_dir.get().strip())
        if not output_dir:
            messagebox.showinfo(
                "Output folder",
                "In source-folder mode, open output folder works after you add exactly one file. "
                "For multiple files, use a custom output folder.",
            )
            return

        target = Path(output_dir)
        if not target.exists():
            messagebox.showinfo("Output folder", "The selected output folder does not exist yet.")
            return

        if os.name == "nt":
            os.startfile(target)  # type: ignore[attr-defined]
            return

        subprocess.Popen(["xdg-open", str(target)])

    def start_conversion(self) -> None:
        source_paths = [Path(self.tree.set(item_id, "path")) for item_id in self.tree.get_children()]
        if not source_paths:
            messagebox.showwarning("No files", "Select at least one .doc or .docx file.")
            return

        if self.output_mode.get() == "custom":
            output_dir = self.custom_output_dir.get().strip()
            if not output_dir:
                messagebox.showwarning("Output folder", "Choose an output folder before starting.")
                return
            output_path = Path(output_dir)
            if not output_path.exists():
                messagebox.showwarning("Output folder", "The selected output folder does not exist.")
                return
        else:
            output_dir = None

        if any(is_doc_file(path) for path in source_paths) and not find_soffice():
            messagebox.showwarning(
                "LibreOffice required",
                "At least one .doc file needs LibreOffice. Install LibreOffice and make sure soffice is in PATH.",
            )
            return

        self._set_busy(True)
        self.summary_text.set("Running conversion...")
        self._append_log("Starting conversion run.")

        for item_id in self.tree.get_children():
            self.tree.set(item_id, "status", "Queued")

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
                self.results_queue.put(
                    (
                        "log",
                        {
                            "message": f"SUCCESS: {source_path.name} -> {result.output_path}",
                        },
                    )
                )
                self.results_queue.put(("status", {"path": str(source_path), "status": "Success"}))
            else:
                failure_count += 1
                if isinstance(result.message, str) and "LibreOffice soffice was not found" in result.message:
                    result.message = "LibreOffice was not found in PATH."
                self.results_queue.put(
                    (
                        "log",
                        {
                            "message": f"FAILED: {source_path.name} -> {result.message}",
                        },
                    )
                )
                self.results_queue.put(("status", {"path": str(source_path), "status": "Failed"}))

        self.results_queue.put(
            (
                "done",
                {
                    "success": success_count,
                    "failure": failure_count,
                },
            )
        )

    def _schedule_queue_poll(self) -> None:
        self.root.after(150, self._process_queue)

    def _process_queue(self) -> None:
        while True:
            try:
                event_type, payload = self.results_queue.get_nowait()
            except queue.Empty:
                break

            if event_type == "status":
                self._set_file_status(payload["path"], payload["status"])
            elif event_type == "log":
                self._append_log(payload["message"])
            elif event_type == "done":
                self._set_busy(False)
                success_count = payload["success"]
                failure_count = payload["failure"]
                self.summary_text.set(f"Finished. Success: {success_count}, Failed: {failure_count}")
                self._append_log(self.summary_text.get())

        self._schedule_queue_poll()

    def _set_busy(self, busy: bool) -> None:
        state = DISABLED if busy else NORMAL
        self.add_button.configure(state=state)
        self.remove_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.start_button.configure(state=state)
        self._update_output_controls(disable_override=busy)

    def _update_output_controls(self, disable_override: bool = False) -> None:
        custom_enabled = self.output_mode.get() == "custom" and not disable_override
        entry_state = NORMAL if custom_enabled else DISABLED
        button_state = NORMAL if custom_enabled else DISABLED
        self.output_dir_entry.configure(state=entry_state)
        self.choose_output_button.configure(state=button_state)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=NORMAL)
        self.log_text.insert(END, f"{message}\n")
        self.log_text.see(END)
        self.log_text.configure(state=DISABLED)

    def _add_file_row(self, path: Path) -> None:
        resolved = str(path)
        if not is_supported_file(resolved):
            self._append_log(f"Skipped unsupported file: {resolved}")
            return
        if resolved in self.file_rows:
            self._append_log(f"Skipped duplicate file: {resolved}")
            return

        item_id = self.tree.insert("", END, values=(resolved, "Waiting"))
        self.file_rows[resolved] = item_id
        self._refresh_summary()

    def _set_file_status(self, file_path: str, status: str) -> None:
        item_id = self.file_rows.get(file_path)
        if item_id:
            self.tree.set(item_id, "status", status)

    def _refresh_summary(self) -> None:
        count = len(self.tree.get_children())
        if count == 0:
            self.summary_text.set("Ready.")
            return
        self.summary_text.set(f"{count} file(s) selected.")


def main() -> None:
    app = ConverterApp()
    app.run()
