import tkinter as tk
from gui.main_window import MainWindow
import traceback
import sys

def report_callback_exception(exc_type, exc_value, exc_traceback):
    """捕获tkinter回调异常并打印"""
    print("Exception in Tkinter callback")
    traceback.print_exception(exc_type, exc_value, exc_traceback)

if __name__ == "__main__":
    # 设置tkinter异常报告
    tk.Tk.report_callback_exception = report_callback_exception

    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()