import tkinter as tk
from tkinter import scrolledtext


class P2PChatGUI:
    def __init__(self, root):
        self.root = root
        root.title("Chat P2P")
        root.geometry("420x520")

        # ---- Nút kết nối / ngắt kết nối ----
        top = tk.Frame(root, pady=10)
        top.pack(fill=tk.X)

        self.connect_btn = tk.Button(top, text="Kết nối", width=14, command=self.on_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        self.disconnect_btn = tk.Button(top, text="Ngắt kết nối", width=14,
                                         command=self.on_disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT)

        self.status = tk.Label(root, text="Chưa kết nối", fg="red")
        self.status.pack()

        # ---- Khung hiển thị tin nhắn ----
        self.chat_area = scrolledtext.ScrolledText(root, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ---- Ô nhập tin nhắn + nút Gửi ----
        bottom = tk.Frame(root, pady=10)
        bottom.pack(fill=tk.X, padx=10)

        self.msg_entry = tk.Entry(bottom, state=tk.DISABLED)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", lambda e: self.on_send())

        self.send_btn = tk.Button(bottom, text="Gửi", width=8, command=self.on_send, state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=(5, 0))

    # ---- Tiện ích ----
    def _print(self, text):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, text + "\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _set_connected(self, connected):
        state = tk.NORMAL if connected else tk.DISABLED
        self.msg_entry.config(state=state)
        self.send_btn.config(state=state)
        self.disconnect_btn.config(state=state)
        self.connect_btn.config(state=tk.DISABLED if connected else tk.NORMAL)
        self.status.config(text="Đã kết nối" if connected else "Chưa kết nối",
                            fg="green" if connected else "red")

    # ---- Xử lý sự kiện (chưa gắn socket thật) ----
    def on_connect(self):
        self._print("Đang kết nối tới peer ...")
        self._set_connected(True)

    def on_disconnect(self):
        self._print("Đã ngắt kết nối.")
        self._set_connected(False)

    def on_send(self):
        text = self.msg_entry.get().strip()
        if text:
            self._print(f"Bạn: {text}")
            self.msg_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    P2PChatGUI(root)
    root.mainloop()
