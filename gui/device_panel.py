# gui/device_panel.py — 现代暗色主题 · 精致设备可视化
import tkinter as tk

# 主题色（与 main_window 保持一致）
THEME = {
    "bg_deep":      "#0d1117",
    "bg_card":      "#161b22",
    "bg_surface":   "#1c2333",
    "border":       "#30363d",
    "accent":       "#00d4aa",
    "accent_warm":  "#ffa940",
    "text_primary": "#e6edf3",
    "text_secondary":"#8b949e",
    "shadow":       "#00000044",
}


class DevicePanel:
    def __init__(self, parent, root):
        self.root = root

        # 外层框架，暗色背景
        self.frame = tk.Frame(parent, width=780, height=340, bg=THEME["bg_deep"])
        self.frame.pack(side=tk.LEFT, fill=tk.BOTH)
        self.frame.pack_propagate(False)

        # 面板标题
        tk.Label(
            self.frame, text="📟  设备仿真面板",
            font=("微软雅黑", 13, "bold"),
            bg=THEME["bg_deep"], fg=THEME["text_primary"]
        ).pack(pady=(10, 6))

        # 设备容器（水平排列）
        dev_container = tk.Frame(self.frame, bg=THEME["bg_deep"])
        dev_container.pack(expand=True)

        # ═══════════ 灯光卡片 ═══════════
        self._create_light_card(dev_container)

        # ═══════════ 空调卡片 ═══════════
        self._create_air_card(dev_container)

    # ---------- 灯光卡片 ----------
    def _create_light_card(self, parent):
        card = tk.Frame(parent, bg=THEME["bg_card"],
                         highlightbackground=THEME["border"],
                         highlightthickness=1, padx=16, pady=12)
        card.pack(side=tk.LEFT, padx=30, pady=8)

        tk.Label(card, text="💡 灯光", font=("微软雅黑", 11, "bold"),
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(pady=(0, 8))

        self.light_canvas = tk.Canvas(
            card, width=160, height=210, bg=THEME["bg_card"],
            highlightthickness=0
        )
        self.light_canvas.pack()

        # 发光光晕（外层大圆）
        self.light_glow = self.light_canvas.create_oval(10, 5, 150, 145, fill="#1a2a1e", outline="")
        # 灯泡玻璃主体
        self.light_glass = self.light_canvas.create_oval(30, 25, 130, 125, fill="#2a3a2a", outline="#3a5a3a", width=2)
        # 灯头金属底座
        self.light_base = self.light_canvas.create_rectangle(55, 122, 105, 150, fill="#3a3a3a", outline="#4a4a4a", width=2)
        # 灯头螺纹
        self.light_canvas.create_line(57, 130, 103, 130, fill="#4a4a4a", width=1)
        self.light_canvas.create_line(57, 138, 103, 138, fill="#4a4a4a", width=1)

        # 状态文字
        self.light_text = self.light_canvas.create_text(
            80, 180, text="已关闭", font=("微软雅黑", 11, "bold"), fill=THEME["text_secondary"]
        )

    # ---------- 空调卡片 ----------
    def _create_air_card(self, parent):
        card = tk.Frame(parent, bg=THEME["bg_card"],
                         highlightbackground=THEME["border"],
                         highlightthickness=1, padx=16, pady=12)
        card.pack(side=tk.LEFT, padx=30, pady=8)

        tk.Label(card, text="❄️ 空调", font=("微软雅黑", 11, "bold"),
                 bg=THEME["bg_card"], fg=THEME["text_primary"]).pack(pady=(0, 8))

        self.air_canvas = tk.Canvas(
            card, width=200, height=210, bg=THEME["bg_card"],
            highlightthickness=0
        )
        self.air_canvas.pack()

        # 机身阴影
        self.air_shadow = self.air_canvas.create_rectangle(18, 20, 182, 180, fill="#1a2a1e", outline="")
        # 机身主体
        self.air_body = self.air_canvas.create_rectangle(25, 25, 175, 175, fill="#2a3a2a", outline="#3a5a3a", width=2)
        # 出风口格栅
        for i in range(4):
            y = 55 + i * 22
            self.air_canvas.create_line(35, y, 165, y, fill="#3a5a3a", width=1.5)
        # 显示屏区域
        self.air_screen = self.air_canvas.create_rectangle(55, 25, 145, 52, fill="#0d1a0d", outline="#3a5a3a", width=1)
        # 温度数字
        self.air_temp_display = self.air_canvas.create_text(
            100, 38, text="24°C", font=("微软雅黑", 18, "bold"), fill="#4a8a4a"
        )
        # 开关状态灯
        self.air_led = self.air_canvas.create_oval(150, 30, 160, 40, fill="#333333", outline="")

        # 底部状态文字
        self.air_text = self.air_canvas.create_text(
            100, 192, text="已关闭", font=("微软雅黑", 11, "bold"), fill=THEME["text_secondary"]
        )

    # ═══════════════════════════════════════════════
    #  状态同步方法 — 功能 100% 不变
    # ═══════════════════════════════════════════════
    def sync_light_status(self, is_on: bool, brightness: int = 50):
        def _update():
            if is_on:
                self.light_canvas.itemconfig(self.light_glow, fill="#2d3a1a")
                self.light_canvas.itemconfig(self.light_glass, fill="#f0c040", outline="#f5d060")
                self.light_canvas.itemconfig(self.light_text, text=f"已开启", fill="#f0c040")
            else:
                self.light_canvas.itemconfig(self.light_glow, fill="#1a2a1e")
                self.light_canvas.itemconfig(self.light_glass, fill="#2a3a2a", outline="#3a5a3a")
                self.light_canvas.itemconfig(self.light_text, text="已关闭", fill=THEME["text_secondary"])
        self.root.after(0, _update)

    def sync_air_status(self, is_on: bool, temp: int = 24):
        def _update():
            if is_on:
                self.air_canvas.itemconfig(self.air_shadow, fill="#1a2a2e")
                self.air_canvas.itemconfig(self.air_body, fill="#1e3a4a", outline="#3a7aba")
                self.air_canvas.itemconfig(self.air_screen, fill="#0a1a2a")
                self.air_canvas.itemconfig(self.air_temp_display, text=f"{temp}°C", fill="#58a6ff")
                self.air_canvas.itemconfig(self.air_led, fill="#00d4aa")
                self.air_canvas.itemconfig(self.air_text, text="运行中", fill="#58a6ff")
            else:
                self.air_canvas.itemconfig(self.air_shadow, fill="#1a2a1e")
                self.air_canvas.itemconfig(self.air_body, fill="#2a3a2a", outline="#3a5a3a")
                self.air_canvas.itemconfig(self.air_screen, fill="#0d1a0d")
                self.air_canvas.itemconfig(self.air_temp_display, text=f"{temp}°C", fill="#4a8a4a")
                self.air_canvas.itemconfig(self.air_led, fill="#333333")
                self.air_canvas.itemconfig(self.air_text, text="已关闭", fill=THEME["text_secondary"])
        self.root.after(0, _update)