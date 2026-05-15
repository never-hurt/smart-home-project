import tkinter as tk
from tkinter import messagebox
from gui.device_panel import DevicePanel
from gui.log_panel import LogPanel
from device.device_manager import DeviceStateMachine
from control.cmd_parser import CmdParser
from control.voice_listener import VoiceListener

# ═══════════════════════════════════════════════════════════════
#  设计系统 — 现代智能家居暗色主题
# ═══════════════════════════════════════════════════════════════
THEME = {
    "bg_deep":      "#0d1117",   # 最深背景
    "bg_card":      "#161b22",   # 卡片/面板背景
    "bg_surface":   "#1c2333",   # 浮层表面
    "bg_input":     "#21283a",   # 输入区域
    "border":       "#30363d",   # 边框
    "border_glow":  "#58a6ff",   # 高亮边框
    "accent":       "#00d4aa",   # 主强调色 (科技绿)
    "accent_warm":  "#ffa940",   # 暖强调色 (琥珀)
    "danger":       "#f85149",   # 危险/错误
    "text_primary": "#e6edf3",   # 主文字
    "text_secondary":"#8b949e",  # 次要文字
    "text_white":   "#ffffff",
    "shadow":       "#00000044",
}

# 通用字体
FONT_TITLE  = ("微软雅黑", 16, "bold")
FONT_HEADER = ("微软雅黑", 11, "bold")
FONT_BODY   = ("微软雅黑", 10)
FONT_SMALL  = ("微软雅黑", 9)


# ---------------------- 现代圆角扁平按钮 ----------------------
class BeautifulButton(tk.Button):
    """保留原有构造函数签名 + 全部回调行为，仅升级视觉效果"""
    def __init__(self, parent, text, command=None, **kwargs):
        self._variant = kwargs.pop("variant", "default")  # default / accent / danger / warm
        self.default_bg = kwargs.pop("bg", None)
        self.default_fg = kwargs.pop("fg", None)

        # ---------- 按 variant 设定配色 ----------
        variant_map = {
            "default": ("#21283a", "#c9d1d9", "#30363d", "#58a6ff", "#30363d"),
            "accent":  ("#00d4aa", "#0d1117", "#00d4aa", "#00e6bf", "#00d4aa"),
            "danger":  ("#f85149", "#ffffff", "#f85149", "#ff6b6b", "#f85149"),
            "warm":    ("#ffa940", "#0d1117", "#ffa940", "#ffbe5c", "#ffa940"),
        }
        bg, fg, bd, hover_bg, active_bg = variant_map.get(self._variant, variant_map["default"])

        if self.default_bg is None:
            self.default_bg = bg
        if self.default_fg is None:
            self.default_fg = fg
        self.hover_bg  = hover_bg
        self.active_bg = active_bg
        self.border_color = bd

        super().__init__(
            parent, text=text, command=command,
            bg=self.default_bg, fg=self.default_fg,
            activebackground=self.active_bg, activeforeground=self.default_fg,
            font=("微软雅黑", 10, "bold"),
            width=10, height=1,
            bd=0,          # 扁平无边框
            relief=tk.FLAT,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=self.border_color,
            highlightcolor=self.hover_bg,
            padx=8, pady=4,
            **kwargs
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        if str(self["state"]) != "disabled":
            self.config(bg=self.hover_bg, highlightbackground=self.hover_bg)

    def _on_leave(self, event):
        self.config(bg=self.default_bg, highlightbackground=self.border_color)


# ---------------------- 主窗口类 ----------------------
class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("🏠 智能家居语音交互控制系统")
        self.root.geometry("950x780")
        self.root.resizable(False, False)
        self.root.configure(bg=THEME["bg_deep"])

        self.state_machine = DeviceStateMachine()
        self.cmd_parser = CmdParser()

        self._create_header()
        self.device_panel = DevicePanel(self.root, self.root)
        self._create_control_bar()
        self.log_panel = LogPanel(self.root, self.root)

        self.voice_listener = None
        # 追踪监听按钮引用用于状态切换
        self._voice_btn = None

    # ---------- 顶部标题栏 ----------
    def _create_header(self):
        header = tk.Frame(self.root, bg=THEME["bg_deep"], height=56)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)

        # 左侧装饰线 + 标题
        accent_line = tk.Frame(header, bg=THEME["accent"], width=4, height=28)
        accent_line.place(x=16, y=14)

        tk.Label(
            header, text="🏠  智能家居 · 语音交互控制中心",
            font=FONT_TITLE, bg=THEME["bg_deep"], fg=THEME["text_primary"]
        ).place(x=30, y=10)

        # 右侧状态指示点
        self._status_dot = tk.Canvas(header, width=12, height=12,
                                      bg=THEME["bg_deep"], highlightthickness=0)
        self._status_dot.place(x=910, y=22)
        self._dot = self._status_dot.create_oval(2, 2, 10, 10, fill=THEME["accent"], outline="")

        tk.Label(header, text="系统就绪", font=FONT_SMALL,
                 bg=THEME["bg_deep"], fg=THEME["text_secondary"]).place(x=818, y=19)

    # ---------- 底部控制栏（卡片式分组布局） ----------
    def _create_control_bar(self):
        bar = tk.Frame(self.root, bg=THEME["bg_card"],
                        height=130, highlightbackground=THEME["border"],
                        highlightthickness=1)
        bar.pack(fill=tk.X, padx=12, pady=(4, 6))
        bar.pack_propagate(False)

        inner = tk.Frame(bar, bg=THEME["bg_card"])
        inner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # ----- 灯光组 -----
        light_card = self._make_control_card(inner, "💡  灯光控制")
        light_card.pack(side=tk.LEFT, padx=18)

        BeautifulButton(light_card, text="🔆 打开灯光",
                        command=self.on_light_on, variant="warm").pack(side=tk.LEFT, padx=4)
        BeautifulButton(light_card, text="🔅 关闭灯光",
                        command=self.on_light_off, variant="default").pack(side=tk.LEFT, padx=4)

        # ----- 语音组 -----
        voice_card = self._make_control_card(inner, "🎤  语音控制")
        voice_card.pack(side=tk.LEFT, padx=18)

        self._voice_btn = BeautifulButton(voice_card, text="🎙  开始监听",
                                           command=self.start_voice, variant="accent")
        self._voice_btn.pack(side=tk.LEFT, padx=4)

        # ----- 空调组 -----
        air_card = self._make_control_card(inner, "❄️  空调控制")
        air_card.pack(side=tk.LEFT, padx=18)

        row1 = tk.Frame(air_card, bg=THEME["bg_card"])
        row1.pack(pady=2)
        BeautifulButton(row1, text="❄ 打开空调",
                        command=self.on_air_on, variant="accent").pack(side=tk.LEFT, padx=4)
        BeautifulButton(row1, text="⏻ 关闭空调",
                        command=self.on_air_off, variant="danger").pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(air_card, bg=THEME["bg_card"])
        row2.pack(pady=2)
        self.btn_temp_up = BeautifulButton(row2, text="🔼 温度调高",
                                            command=self.on_temp_up, variant="warm")
        self.btn_temp_up.pack(side=tk.LEFT, padx=4)
        self.btn_temp_down = BeautifulButton(row2, text="🔽 温度调低",
                                              command=self.on_temp_down, variant="default")
        self.btn_temp_down.pack(side=tk.LEFT, padx=4)

        self.btn_temp_up.config(state=tk.DISABLED)
        self.btn_temp_down.config(state=tk.DISABLED)

    def _make_control_card(self, parent, title):
        card = tk.Frame(parent, bg=THEME["bg_surface"],
                         highlightbackground=THEME["border"],
                         highlightthickness=1, padx=10, pady=8)
        tk.Label(card, text=title, font=FONT_SMALL,
                 bg=THEME["bg_surface"], fg=THEME["text_secondary"]).pack(anchor=tk.W, pady=(0, 4))
        return card

    # ═══════════════════════════════════════════════════════
    #  所有回调函数 — 功能 100% 不变
    # ═══════════════════════════════════════════════════════
    def on_light_on(self):
        self._execute_gui_cmd("打开灯光")

    def on_light_off(self):
        self._execute_gui_cmd("关闭灯光")

    def on_air_on(self):
        self._execute_gui_cmd("打开空调")

    def on_air_off(self):
        self._execute_gui_cmd("关闭空调")

    def on_temp_up(self):
        self._execute_gui_cmd("温度调高")

    def on_temp_down(self):
        self._execute_gui_cmd("温度调低")

    # ---------------------- 语音控制 ----------------------
    def start_voice(self):
        self.voice_listener = VoiceListener(
            root=self.root,
            on_recognize_callback=self.on_voice_recognized,
            on_listen_complete=self.ask_continue,
            on_error=self._on_voice_error,
            on_status=self._on_voice_status
        )
        self.voice_listener.start()
        self.log_panel.write_log("INFO", "语音监听已启动，请说话")
        self._set_voice_btn_state(listening=True)

    def stop_voice(self):
        if self.voice_listener:
            self.voice_listener.stop_listening()
            self.voice_listener = None
        self.log_panel.write_log("INFO", "已停止语音监听")
        self._set_voice_btn_state(listening=False)

    def _set_voice_btn_state(self, listening: bool):
        if self._voice_btn is None:
            return
        if listening:
            self._voice_btn._variant = "danger"
            self._voice_btn.default_bg = "#f85149"
            self._voice_btn.default_fg = "#ffffff"
            self._voice_btn.hover_bg = "#ff6b6b"
            self._voice_btn.active_bg = "#f85149"
            self._voice_btn.border_color = "#f85149"
            self._voice_btn.config(text="⏹  停止监听", bg="#f85149", fg="#ffffff",
                                   highlightbackground="#f85149")
        else:
            self._voice_btn._variant = "accent"
            self._voice_btn.default_bg = "#00d4aa"
            self._voice_btn.default_fg = "#0d1117"
            self._voice_btn.hover_bg = "#00e6bf"
            self._voice_btn.active_bg = "#00d4aa"
            self._voice_btn.border_color = "#00d4aa"
            self._voice_btn.config(text="🎙  开始监听", bg="#00d4aa", fg="#0d1117",
                                   highlightbackground="#00d4aa")

    def _on_voice_error(self, title, msg):
        messagebox.showerror(title, msg)

    def _on_voice_status(self, status_type, message):
        if status_type == "recording":
            self.log_panel.write_log("INFO", f"🎤 {message}")
        elif status_type == "recognizing":
            self.log_panel.write_log("INFO", f"🔍 {message}")
        elif status_type == "matched":
            if "❌" in message:
                self.log_panel.write_log("WARN", message)
            else:
                self.log_panel.write_log("INFO", message)
        elif status_type == "error":
            self.log_panel.write_log("ERROR", message)

    def ask_continue(self):
        result = messagebox.askyesno(
            "语音识别完成",
            "🎤 本次语音识别已完成\n\n"
            "是否继续进行语音识别？\n\n"
            "点击「是」— 继续监听下一条指令\n"
            "点击「否」— 退出语音识别模式"
        )
        if result:
            self.start_voice()
        else:
            self.stop_voice()
            self.log_panel.write_log("INFO", "已退出语音识别模式")

    def on_voice_recognized(self, raw_text: str, matched_cmd: str):
        if raw_text:
            self.log_panel.write_log("INFO", f"🎤 语音原文：{raw_text}")
        if "[识别失败]" in matched_cmd or "[监听异常]" in matched_cmd:
            self.log_panel.write_log("WARN", f"识别结果：{matched_cmd}")
            return
        self.log_panel.write_log("INFO", f"🎯 匹配指令：{matched_cmd}")
        self._execute_gui_cmd(matched_cmd)

    # ---------------------- 内部执行逻辑 ----------------------
    def _execute_gui_cmd(self, cmd_text: str):
        success, msg = self.cmd_parser.parse_and_execute(cmd_text)
        if success:
            if "无需重复操作" in msg:
                self.log_panel.write_log("WARN", msg)
            else:
                self.log_panel.write_log("INFO", msg)
            self._sync_all_gui()
        else:
            self.log_panel.write_log("ERROR", msg)

    def _sync_all_gui(self):
        success, light_state = self.state_machine.get_device_state("light")
        if success:
            self.device_panel.sync_light_status(
                is_on=(light_state["status"] == "on"),
                brightness=light_state["brightness"]
            )

        success, air_state = self.state_machine.get_device_state("air")
        if success:
            self.device_panel.sync_air_status(
                is_on=(air_state["status"] == "on"),
                temp=air_state["temp"]
            )
            if air_state["status"] == "on":
                self.btn_temp_up.config(state=tk.NORMAL)
                self.btn_temp_down.config(state=tk.NORMAL)
            else:
                self.btn_temp_up.config(state=tk.DISABLED)
                self.btn_temp_down.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()