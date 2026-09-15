"""UDM_09 — Chat P2P application entry point."""

from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog, messagebox
import sys

from GUI.chat_gui import ChatGUI


def main():
    root = tk.Tk()
    root.withdraw()

    username = simpledialog.askstring(
        "UDM_09 — P2P Chat",
        "Nhập tên hiển thị của bạn:",
        parent=root,
    )
    if not username or not username.strip():
        root.destroy()
        return
    username = username.strip()

    port_text = simpledialog.askstring(
        "Port",
        "Nhập TCP Port (mặc định 5000):",
        initialvalue="5000",
        parent=root,
    )
    try:
        port = int(port_text or "5000")
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        messagebox.showerror("Port", "Port không hợp lệ.", parent=root)
        root.destroy()
        return

    root.deiconify()
    ChatGUI(root, username, port)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
