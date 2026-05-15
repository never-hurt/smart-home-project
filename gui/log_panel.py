# gui/log_panel.py — 暗色终端风格日志面板
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

THEME = {
    "bg_deep":      "#0d1117",
    "bg_card":      "#161b22",
    "border":       "#30363d",
    "text_primary": "#e6edf3",
    "text_secondary":"#8b949e",
}


class LogPanel:
    def __init__(self, parent, root):
        self.root = root

        self.frame = tk.Frame(parent, bg=THEME["bg_deep"])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6, 10))

        # 标题行
        title_bar = tk.Frame(self.frame, bg=THEME["bg_deep"])
        title_bar.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            title_bar, text="📋  系统操作日志",
            font=("微软雅黑", 11, "bold"),
            bg=THEME["bg_deep"], fg=THEME["text_primary"]
        ).pack(side=tk.LEFT)

        # 日志数量标记
        self._log_count = 0
        self._count_label = tk.Label(
            title_bar, text="", font=("Consolas", 9),
            bg=THEME["bg_deep"], fg=THEME["text_secondary"]
        )
        self._count_label.pack(side=tk.RIGHT)

        # 终端风格日志文本框
        self.log_text = scrolledtext.ScrolledText(
            self.frame,
            font=("Consolas", 9),
            bg="#0d1117",
            fg="#c9d1d9",
            insertbackground="#ffffff",
            bd=0,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=THEME["border"],
            highlightcolor=THEME["border"],
            state=tk.DISABLED,
            padx=10,
            pady=8,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志级别颜色（终端风格）
        self.log_text.tag_config("INFO", foreground="#7ee787")     # 绿色
        self.log_text.tag_config("WARN", foreground="#d29922")     # 橙黄
        self.log_text.tag_config("ERROR", foreground="#f85149")    # 红色
        self.log_text.tag_config("TIME", foreground="#484f58")     # 时间灰色

    def write_log(self, level: str, msg: str):
        def _write():
            self.log_text.config(state=tk.NORMAL)
            time_str = datetime.now().strftime("%H:%M:%S")
            tag = level if level in ["INFO", "WARN", "ERROR"] else "INFO"

            self.log_text.insert(tk.END, f"[{time_str}] ", "TIME")
            self.log_text.insert(tk.END, f"[{level}] {msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

            self._log_count += 1
            self._count_label.config(text=f"{self._log_count} 条")

        self.root.after(0, _write)