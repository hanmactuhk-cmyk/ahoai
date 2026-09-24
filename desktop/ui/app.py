import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from desktop.services.job_manager import JobManager
from desktop.services.bridge import Bridge


APP = "Hn38videoAItool"


def config_path():
    return Path(os.environ.get("APPDATA", str(Path.home()))) / APP / "config.json"


def load_config():
    p = config_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "mode": "demo",
        "base_url": "",
        "api_key": "",
        "output_dir": str(Path.home() / "Videos" / APP),
    }


def save_config(cfg):
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP)
        self.root.geometry("1000x720")
        self.root.minsize(900, 620)

        self.config = load_config()
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)

        self.rows = {}
        self.bridge = Bridge()
        self.bridge.start()
        self.manager = JobManager(self.config, self.on_job_update)

        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            pass

        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text=APP, font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header, text="  Desktop Automation", foreground="#666").pack(
            side="left", pady=(7, 0)
        )
        ttk.Button(header, text="Cài đặt API", command=self.settings).pack(side="right")

        box = ttk.LabelFrame(self.root, text="Tạo tác vụ", padding=10)
        box.pack(fill="x", padx=12, pady=(0, 10))

        ttk.Label(box, text="Prompt").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self.prompt = tk.Text(box, height=5, wrap="word")
        self.prompt.grid(row=0, column=1, columnspan=5, sticky="ew", padx=5, pady=5)

        ttk.Label(box, text="Thời lượng").grid(row=1, column=0, sticky="w", padx=5)
        self.duration = ttk.Combobox(
            box, values=["5", "10", "15", "20"], state="readonly", width=10
        )
        self.duration.set("10")
        self.duration.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(box, text="Tỷ lệ").grid(row=1, column=2, sticky="w", padx=5)
        self.aspect = ttk.Combobox(
            box, values=["16:9", "9:16", "1:1"], state="readonly", width=10
        )
        self.aspect.set("16:9")
        self.aspect.grid(row=1, column=3, sticky="w", padx=5)

        ttk.Button(box, text="Thêm vào hàng đợi", command=self.add_job).grid(
            row=1, column=5, sticky="e", padx=5
        )
        box.columnconfigure(1, weight=1)
        box.columnconfigure(4, weight=1)

        queue = ttk.LabelFrame(self.root, text="Hàng đợi", padding=8)
        queue.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        cols = ("id", "prompt", "duration", "aspect", "status", "progress", "error")
        self.tree = ttk.Treeview(queue, columns=cols, show="headings")
        names = {
            "id": "ID", "prompt": "Prompt", "duration": "Giây",
            "aspect": "Tỷ lệ", "status": "Trạng thái", "progress": "%",
            "error": "Lỗi"
        }
        widths = {
            "id": 80, "prompt": 360, "duration": 60, "aspect": 70,
            "status": 100, "progress": 55, "error": 250
        }
        for c in cols:
            self.tree.heading(c, text=names[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")

        sb = ttk.Scrollbar(queue, orient="vertical", command=self.tree.yview)
        sb.pack(fill="y", side="right")
        self.tree.configure(yscrollcommand=sb.set)

        actions = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        actions.pack(fill="x")
        ttk.Button(actions, text="Hủy tất cả", command=self.cancel_all).pack(side="left")
        ttk.Button(actions, text="Thử lại job chọn", command=self.retry_selected).pack(
            side="left", padx=8
        )
        ttk.Button(actions, text="Thư mục output", command=self.open_output).pack(side="left")

        logbox = ttk.LabelFrame(self.root, text="Log", padding=8)
        logbox.pack(fill="x", padx=12, pady=(0, 12))
        self.log = tk.Text(logbox, height=7, state="disabled")
        self.log.pack(fill="x")

        self.log_line("App khởi động OK.")
        self.log_line("Demo Mode: có thể test ngay, không cần API.")
        self.log_line("Bridge: http://127.0.0.1:18923/health")

    def log_line(self, text):
        def write():
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(0, write)

    def add_job(self):
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Thiếu prompt", "Hãy nhập prompt.")
            return
        job = self.manager.add(prompt, int(self.duration.get()), self.aspect.get())
        self.prompt.delete("1.0", "end")
        self.log_line(f"Đã thêm job {job.local_id}.")

    def on_job_update(self, job):
        def update():
            values = (
                job.local_id, job.prompt[:80], job.duration, job.aspect,
                job.status, job.progress, job.error
            )
            if job.local_id in self.rows:
                self.tree.item(self.rows[job.local_id], values=values)
            else:
                self.rows[job.local_id] = self.tree.insert("", "end", values=values)

            if job.status in ("completed", "failed", "cancelled"):
                suffix = f" - {job.error}" if job.error else ""
                self.log_line(f"Job {job.local_id}: {job.status}{suffix}")

        self.root.after(0, update)

    def cancel_all(self):
        self.manager.cancel_all()
        self.log_line("Đã yêu cầu hủy job.")

    def retry_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Chọn job", "Hãy chọn job trước.")
            return
        job_id = str(self.tree.item(selected[0], "values")[0])
        self.manager.retry(job_id)
        self.log_line(f"Retry {job_id}")

    def open_output(self):
        path = self.config["output_dir"]
        Path(path).mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def settings(self):
        win = tk.Toplevel(self.root)
        win.title("Cài đặt API")
        win.geometry("540x330")
        win.transient(self.root)
        win.grab_set()

        mode = tk.StringVar(value=self.config.get("mode", "demo"))
        base = tk.StringVar(value=self.config.get("base_url", ""))
        key = tk.StringVar(value=self.config.get("api_key", ""))
        output = tk.StringVar(value=self.config.get("output_dir", ""))

        ttk.Label(win, text="Chế độ").pack(anchor="w", padx=15, pady=(15, 4))
        ttk.Combobox(
            win, textvariable=mode, values=["demo", "api"], state="readonly"
        ).pack(fill="x", padx=15)

        ttk.Label(win, text="Base URL").pack(anchor="w", padx=15, pady=(10, 4))
        ttk.Entry(win, textvariable=base).pack(fill="x", padx=15)

        ttk.Label(win, text="API Key").pack(anchor="w", padx=15, pady=(10, 4))
        ttk.Entry(win, textvariable=key, show="*").pack(fill="x", padx=15)

        ttk.Label(win, text="Output folder").pack(anchor="w", padx=15, pady=(10, 4))
        row = ttk.Frame(win)
        row.pack(fill="x", padx=15)
        ttk.Entry(row, textvariable=output).pack(side="left", fill="x", expand=True)
        ttk.Button(
            row, text="...",
            command=lambda: output.set(filedialog.askdirectory() or output.get())
        ).pack(side="left", padx=5)

        def save():
            self.config.update({
                "mode": mode.get(),
                "base_url": base.get().strip(),
                "api_key": key.get().strip(),
                "output_dir": output.get().strip() or str(Path.home() / "Videos" / APP)
            })
            save_config(self.config)
            messagebox.showinfo(
                "Đã lưu",
                "Đã lưu. Job mới sẽ dùng cấu hình backend mới."
            )
            win.destroy()

        ttk.Button(win, text="Lưu", command=save).pack(pady=18)

    def close(self):
        try:
            self.manager.cancel_all()
            self.bridge.stop()
        finally:
            self.root.destroy()

    def run(self):
        self.root.mainloop()
