import os
import queue
import subprocess
import threading
from pathlib import Path
from tkinter import END, BOTH, DISABLED, NORMAL, IntVar, StringVar, Text, Tk, filedialog, messagebox
from tkinter import ttk

from src.converter import convert_one
from src.libreoffice import find_soffice
from src.utils import get_output_folder_for_open, is_doc_file, is_supported_file


class ConverterApp:
    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("MarkItDown 文档转换工具")
        self.root.geometry("960x700")
        self.root.minsize(820, 580)
        self.root.configure(bg="#f4f6f8")

        self.output_mode = StringVar(value="source")
        self.custom_output_dir = StringVar(value="")
        self.summary_text = StringVar(value="等待添加文件")
        self.progress_value = IntVar(value=0)

        self.file_rows: dict[str, str] = {}
        self.results_queue: queue.Queue[tuple[str, dict]] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.total_files = 0
        self.completed_files = 0

        self._configure_styles()
        self._build_ui()
        self._schedule_queue_poll()

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        font_family = "Microsoft YaHei UI" if os.name == "nt" else "DejaVu Sans"
        mono_family = "Consolas" if os.name == "nt" else "DejaVu Sans Mono"
        self.font_family = font_family
        self.mono_family = mono_family

        style.configure("App.TFrame", background="#f4f6f8")
        style.configure("Panel.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Soft.TFrame", background="#eef2f7")
        style.configure("Header.TLabel", background="#f4f6f8", foreground="#111827", font=(font_family, 18, "bold"))
        style.configure("Subtle.TLabel", background="#f4f6f8", foreground="#64748b", font=(font_family, 10))
        style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#111827", font=(font_family, 11, "bold"))
        style.configure("PanelHint.TLabel", background="#ffffff", foreground="#64748b", font=(font_family, 9))
        style.configure("Status.TLabel", background="#eef2f7", foreground="#334155", font=(font_family, 10, "bold"))
        style.configure("Primary.TButton", font=(font_family, 10, "bold"), padding=(16, 8))
        style.configure("Secondary.TButton", font=(font_family, 10), padding=(12, 8))
        style.configure("TRadiobutton", background="#ffffff", foreground="#334155", font=(font_family, 9))
        style.map("TRadiobutton", background=[("active", "#ffffff")])
        style.configure("Treeview", rowheight=30, font=(font_family, 9), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=(font_family, 9, "bold"), foreground="#334155")
        style.configure("Horizontal.TProgressbar", troughcolor="#e5e7eb", background="#2563eb", thickness=8)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=18, style="App.TFrame")
        container.pack(fill=BOTH, expand=True)

        header = ttk.Frame(container, style="App.TFrame")
        header.pack(fill="x", pady=(0, 14))

        title_area = ttk.Frame(header, style="App.TFrame")
        title_area.pack(side="left", fill="x", expand=True)
        ttk.Label(title_area, text="Word 转 Markdown", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            title_area,
            text=".docx 可直接转换，.doc 需要已安装 LibreOffice 并能访问 soffice",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        summary_pill = ttk.Frame(header, padding=(14, 8), style="Soft.TFrame")
        summary_pill.pack(side="right")
        ttk.Label(summary_pill, textvariable=self.summary_text, style="Status.TLabel").pack()

        self._build_file_section(container)
        self._build_output_section(container)
        self._build_execution_section(container)

    def _build_file_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, padding=14, style="Panel.TFrame")
        frame.pack(fill=BOTH, expand=True, pady=(0, 12))

        self._build_section_header(
            frame,
            "1. 选择文件",
            "支持批量添加 .doc 和 .docx，列表里会显示每个文件的转换状态。",
        )

        button_row = ttk.Frame(frame, style="Panel.TFrame")
        button_row.pack(fill="x", pady=(0, 12))

        self.add_button = ttk.Button(button_row, text="添加文件", command=self.add_files, style="Primary.TButton")
        self.add_button.pack(side="left")
        self.remove_button = ttk.Button(
            button_row,
            text="移除选中",
            command=self.remove_selected_files,
            style="Secondary.TButton",
        )
        self.remove_button.pack(side="left", padx=(8, 0))
        self.clear_button = ttk.Button(button_row, text="清空列表", command=self.clear_files, style="Secondary.TButton")
        self.clear_button.pack(side="left", padx=(8, 0))

        columns = ("path", "status")
        tree_frame = ttk.Frame(frame, style="Panel.TFrame")
        tree_frame.pack(fill=BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        self.tree.heading("path", text="文件")
        self.tree.heading("status", text="状态")
        self.tree.column("path", width=670, anchor="w")
        self.tree.column("status", width=140, anchor="center")
        self.tree.pack(side="left", fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def _build_output_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, padding=14, style="Panel.TFrame")
        frame.pack(fill="x", pady=(0, 12))

        self._build_section_header(frame, "2. 设置输出位置", "默认放在源文件旁边；批量转换时建议统一输出到一个文件夹。")

        body = ttk.Frame(frame, style="Panel.TFrame")
        body.pack(fill="x")

        ttk.Radiobutton(
            body,
            text="保存到每个源文件所在目录",
            value="source",
            variable=self.output_mode,
            command=self._update_output_controls,
        ).grid(row=0, column=0, sticky="w")

        ttk.Radiobutton(
            body,
            text="全部保存到指定文件夹",
            value="custom",
            variable=self.output_mode,
            command=self._update_output_controls,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.output_dir_entry = ttk.Entry(body, textvariable=self.custom_output_dir, width=80, state=DISABLED)
        self.output_dir_entry.grid(row=1, column=1, sticky="ew", padx=(12, 8), pady=(8, 0))

        self.choose_output_button = ttk.Button(
            body,
            text="选择文件夹",
            command=self.choose_output_directory,
            state=DISABLED,
            style="Secondary.TButton",
        )
        self.choose_output_button.grid(row=1, column=2, pady=(8, 0))

        body.columnconfigure(1, weight=1)

    def _build_execution_section(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, padding=14, style="Panel.TFrame")
        frame.pack(fill=BOTH, expand=True)

        self._build_section_header(frame, "3. 运行状态", "开始转换后，这里会显示进度、结果和错误原因。")

        action_row = ttk.Frame(frame, style="Panel.TFrame")
        action_row.pack(fill="x", pady=(0, 12))

        self.start_button = ttk.Button(
            action_row,
            text="开始转换",
            command=self.start_conversion,
            style="Primary.TButton",
        )
        self.start_button.pack(side="left")

        self.open_output_button = ttk.Button(
            action_row,
            text="打开输出目录",
            command=self.open_output_folder,
            style="Secondary.TButton",
        )
        self.open_output_button.pack(side="left", padx=(8, 0))

        progress_wrap = ttk.Frame(action_row, style="Panel.TFrame")
        progress_wrap.pack(side="left", fill="x", expand=True, padx=(16, 0))
        self.progress_bar = ttk.Progressbar(
            progress_wrap,
            variable=self.progress_value,
            maximum=1,
            mode="determinate",
            style="Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", pady=(9, 0))

        log_frame = ttk.Frame(frame, padding=1, style="Soft.TFrame")
        log_frame.pack(fill=BOTH, expand=True)

        self.log_text = Text(
            log_frame,
            height=9,
            wrap="word",
            state=DISABLED,
            borderwidth=0,
            padx=12,
            pady=10,
            bg="#0f172a",
            fg="#dbeafe",
            insertbackground="#dbeafe",
            font=(self.mono_family, 9),
        )
        self.log_text.pack(side="left", fill=BOTH, expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side="right", fill="y")

        self.log_text.tag_configure("info", foreground="#bfdbfe")
        self.log_text.tag_configure("success", foreground="#86efac")
        self.log_text.tag_configure("error", foreground="#fca5a5")
        self.log_text.tag_configure("muted", foreground="#94a3b8")
        self._append_log("等待开始转换。添加文件后点击“开始转换”。", level="muted")

    def _build_section_header(self, parent: ttk.Frame, title: str, hint: str) -> None:
        ttk.Label(parent, text=title, style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(parent, text=hint, style="PanelHint.TLabel").pack(anchor="w", pady=(2, 12))

    def run(self) -> None:
        self.root.mainloop()

    def add_files(self) -> None:
        file_paths = filedialog.askopenfilenames(
            title="选择 Word 文件",
            filetypes=[("Word 文件", "*.doc *.docx"), ("所有文件", "*.*")],
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
        self.summary_text.set("等待添加文件")
        self.progress_value.set(0)

    def choose_output_directory(self) -> None:
        selected_dir = filedialog.askdirectory(title="选择输出文件夹")
        if selected_dir:
            self.custom_output_dir.set(selected_dir)

    def open_output_folder(self) -> None:
        source_paths = [Path(self.tree.set(item_id, "path")) for item_id in self.tree.get_children()]
        output_dir = get_output_folder_for_open(source_paths, self.output_mode.get(), self.custom_output_dir.get().strip())
        if not output_dir:
            messagebox.showinfo(
                "输出目录",
                "使用源文件目录模式时，需要先添加一个文件才能直接打开输出目录。"
                "如果要批量处理多个文件，请选择统一输出文件夹。",
            )
            return

        target = Path(output_dir)
        if not target.exists():
            messagebox.showinfo("输出目录", "选择的输出目录还不存在。")
            return

        if os.name == "nt":
            os.startfile(target)  # type: ignore[attr-defined]
            return

        subprocess.Popen(["xdg-open", str(target)])

    def start_conversion(self) -> None:
        source_paths = [Path(self.tree.set(item_id, "path")) for item_id in self.tree.get_children()]
        if not source_paths:
            messagebox.showwarning("没有文件", "请至少选择一个 .doc 或 .docx 文件。")
            return

        if self.output_mode.get() == "custom":
            output_dir = self.custom_output_dir.get().strip()
            if not output_dir:
                messagebox.showwarning("输出目录", "开始转换前，请先选择输出文件夹。")
                return
            output_path = Path(output_dir)
            if not output_path.exists():
                messagebox.showwarning("输出目录", "选择的输出文件夹不存在。")
                return
        else:
            output_dir = None

        if any(is_doc_file(path) for path in source_paths) and not find_soffice():
            messagebox.showwarning(
                "需要 LibreOffice",
                "至少有一个 .doc 文件需要 LibreOffice。请安装 LibreOffice，并确认 soffice 已加入 PATH。",
            )
            return

        self._set_busy(True)
        self.total_files = len(source_paths)
        self.completed_files = 0
        self.progress_bar.configure(maximum=max(self.total_files, 1))
        self.progress_value.set(0)
        self.summary_text.set(f"转换中 0/{self.total_files}")
        self._append_log(f"开始转换，共 {self.total_files} 个文件。", level="info")

        for item_id in self.tree.get_children():
            self.tree.set(item_id, "status", "排队中")

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
            self.results_queue.put(("status", {"path": str(source_path), "status": "转换中"}))
            result = convert_one(source_path=source_path, output_dir=output_dir)
            if result.success:
                success_count += 1
                self.results_queue.put(
                    (
                        "log",
                        {
                            "message": f"成功  {source_path.name} -> {result.output_path}",
                            "level": "success",
                        },
                    )
                )
                self.results_queue.put(("status", {"path": str(source_path), "status": "成功"}))
            else:
                failure_count += 1
                if isinstance(result.message, str) and "LibreOffice soffice was not found" in result.message:
                    result.message = "未在 PATH 中找到 LibreOffice。"
                self.results_queue.put(
                    (
                        "log",
                        {
                            "message": f"失败  {source_path.name} -> {result.message}",
                            "level": "error",
                        },
                    )
                )
                self.results_queue.put(("status", {"path": str(source_path), "status": "失败"}))

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
                if payload["status"] in {"成功", "失败"}:
                    self.completed_files += 1
                    self.progress_value.set(self.completed_files)
                    self.summary_text.set(f"转换中 {self.completed_files}/{self.total_files}")
            elif event_type == "log":
                self._append_log(payload["message"], payload.get("level", "info"))
            elif event_type == "done":
                self._set_busy(False)
                success_count = payload["success"]
                failure_count = payload["failure"]
                self.summary_text.set(f"完成：成功 {success_count}，失败 {failure_count}")
                level = "success" if failure_count == 0 else "error"
                self._append_log(self.summary_text.get(), level=level)

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

    def _append_log(self, message: str, level: str = "info") -> None:
        self.log_text.configure(state=NORMAL)
        prefix = {
            "success": "OK",
            "error": "!!",
            "muted": "--",
        }.get(level, "..")
        line = f"{prefix} {message}\n"
        start_index = self.log_text.index(END)
        self.log_text.insert(END, line)
        end_index = self.log_text.index(END)
        self.log_text.tag_add(level, start_index, end_index)
        self.log_text.see(END)
        self.log_text.configure(state=DISABLED)

    def _add_file_row(self, path: Path) -> None:
        resolved = str(path)
        if not is_supported_file(resolved):
            self._append_log(f"已跳过不支持的文件：{resolved}", level="muted")
            return
        if resolved in self.file_rows:
            self._append_log(f"已跳过重复文件：{resolved}", level="muted")
            return

        item_id = self.tree.insert("", END, values=(resolved, "等待"))
        self.file_rows[resolved] = item_id
        self._refresh_summary()

    def _set_file_status(self, file_path: str, status: str) -> None:
        item_id = self.file_rows.get(file_path)
        if item_id:
            self.tree.set(item_id, "status", status)

    def _refresh_summary(self) -> None:
        count = len(self.tree.get_children())
        if count == 0:
            self.summary_text.set("等待添加文件")
            return
        self.summary_text.set(f"已选择 {count} 个文件")


def main() -> None:
    app = ConverterApp()
    app.run()
