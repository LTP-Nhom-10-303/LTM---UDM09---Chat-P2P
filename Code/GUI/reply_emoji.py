"""
emoji_picker.py
Danh sách emoji + popup chọn emoji để chèn vào ô nhập tin nhắn.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

EMOJIS = [
    "😀", "😂", "😍", "😊", "😢", "😡", "👍", "👎",
    "❤️", "🎉", "💯", "👏", "🔥", "🙏", "😎", "🤔",
    "😴", "🥳", "😱", "🤝",
]


def show_emoji_picker(anchor_widget: tk.Widget, on_pick: Callable[[str], None]) -> None:
    popup = tk.Toplevel(anchor_widget)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)

    x = anchor_widget.winfo_rootx()
    y = anchor_widget.winfo_rooty() - 170
    popup.geometry(f"+{x}+{y}")

    frame = tk.Frame(popup, bd=1, relief="solid", bg="white")
    frame.pack()

    cols = 5
    for i, emo in enumerate(EMOJIS):
        r, c = divmod(i, cols)
        btn = tk.Button(
            frame,
            text=emo,
            font=("Segoe UI Emoji", 14),
            relief="flat",
            bg="white",
            command=lambda e=emo: (on_pick(e), popup.destroy()),
        )
        btn.grid(row=r, column=c, padx=2, pady=2)

    def _close_on_focus_out(_event: object) -> None:
        popup.destroy()

    popup.bind("<FocusOut>", _close_on_focus_out)
    popup.focus_set()


def reply_preview(message: dict) -> dict:
    """Tạo dữ liệu preview cho message được Reply."""
    return {
        "sender_name": message.get("sender_name", "Unknown"),
        "content": message.get("content", ""),
        "msg_id": message.get("msg_id", ""),
    }
