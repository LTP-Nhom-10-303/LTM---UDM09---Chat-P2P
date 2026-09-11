import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

from Message_protocol import MessageProtocol


class P2PChatGUI:

    def __init__(self, root):
        self.root = root

        self.sock = None
        self.server_sock = None

        self.my_name = "User"

        root.title("Chat P2P - UDM_09")
        root.geometry("500x600")

        # =========================
        # KHU VỰC KẾT NỐI
        # =========================

        top = tk.Frame(root, pady=10)
        top.pack(fill=tk.X)

        self.connect_btn = tk.Button(
            top,
            text="Kết nối",
            width=14,
            command=self.on_connect
        )
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        self.disconnect_btn = tk.Button(
            top,
            text="Ngắt kết nối",
            width=14,
            command=self.on_disconnect,
            state=tk.DISABLED
        )
        self.disconnect_btn.pack(side=tk.LEFT)

        # =========================
        # TRẠNG THÁI
        # =========================

        self.status = tk.Label(
            root,
            text="Chưa kết nối",
            fg="red"
        )
        self.status.pack()

        # =========================
        # KHUNG CHAT
        # =========================

        self.chat_area = scrolledtext.ScrolledText(
            root,
            state=tk.DISABLED,
            wrap=tk.WORD
        )

        self.chat_area.pack(
            fill=tk.BOTH,
            expand=True,
            padx=10,
            pady=5
        )

        # =========================
        # KHU VỰC NHẬP
        # =========================

        bottom = tk.Frame(root, pady=10)
        bottom.pack(fill=tk.X, padx=10)

        self.msg_entry = tk.Entry(
            bottom,
            state=tk.DISABLED
        )

        self.msg_entry.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        self.msg_entry.bind(
            "<Return>",
            lambda event: self.on_send()
        )

        # =========================
        # NÚT GỬI
        # =========================

        self.send_btn = tk.Button(
            bottom,
            text="Gửi",
            width=8,
            command=self.on_send,
            state=tk.DISABLED
        )

        self.send_btn.pack(
            side=tk.LEFT,
            padx=(5, 0)
        )

        # =========================
        # NÚT EMOJI
        # =========================

        self.emoji_btn = tk.Button(
            bottom,
            text="😊",
            width=5,
            command=self.show_emoji,
            state=tk.DISABLED
        )

        self.emoji_btn.pack(
            side=tk.LEFT,
            padx=(5, 0)
        )

    # =====================================================
    # HIỂN THỊ TIN NHẮN
    # =====================================================

    def _print_message(self, sender, content, timestamp=None):

        if timestamp is None:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        self.chat_area.config(state=tk.NORMAL)

        self.chat_area.insert(
            tk.END,
            f"[{timestamp}] {sender}: {content}\n"
        )

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    # =====================================================
    # CẬP NHẬT TRẠNG THÁI
    # =====================================================

    def _set_connected(self, connected):

        state = tk.NORMAL if connected else tk.DISABLED

        self.msg_entry.config(state=state)
        self.send_btn.config(state=state)
        self.emoji_btn.config(state=state)
        self.disconnect_btn.config(state=state)

        if connected:

            self.connect_btn.config(state=tk.DISABLED)

            self.status.config(
                text="Đã kết nối",
                fg="green"
            )

        else:

            self.connect_btn.config(state=tk.NORMAL)

            self.status.config(
                text="Chưa kết nối",
                fg="red"
            )

    # =====================================================
    # KẾT NỐI
    # =====================================================

    def on_connect(self):

        ip = simpledialog.askstring(
            "Kết nối",
            "Nhập IP peer:",
            initialvalue="127.0.0.1"
        )

        if not ip:
            return

        port = simpledialog.askinteger(
            "Kết nối",
            "Nhập port:",
            initialvalue=5000
        )

        if not port:
            return

        self.my_name = simpledialog.askstring(
            "Tên người dùng",
            "Nhập tên của bạn:",
            initialvalue="User"
        )

        if not self.my_name:
            self.my_name = "User"

        self.connect_btn.config(state=tk.DISABLED)

        threading.Thread(
            target=self._connect_thread,
            args=(ip, port),
            daemon=True
        ).start()

    # =====================================================
    # THREAD KẾT NỐI
    # =====================================================

    def _connect_thread(self, ip, port):

        try:

            # Thử làm CLIENT

            s = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            s.settimeout(3)

            s.connect((ip, port))

            s.settimeout(None)

            self.sock = s

        except OSError:

            # Nếu không kết nối được
            # thì chuyển sang SERVER

            try:

                self.server_sock = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM
                )

                self.server_sock.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_REUSEADDR,
                    1
                )

                self.server_sock.bind(
                    ("0.0.0.0", port)
                )

                self.server_sock.listen(1)

                self.root.after(
                    0,
                    self._print_message,
                    "Hệ thống",
                    f"Đang chờ peer kết nối tới cổng {port}..."
                )

                self.sock, address = self.server_sock.accept()

            except OSError as e:

                self.root.after(
                    0,
                    messagebox.showerror,
                    "Lỗi kết nối",
                    str(e)
                )

                self.root.after(
                    0,
                    lambda: self.connect_btn.config(
                        state=tk.NORMAL
                    )
                )

                return

        # Kết nối thành công

        self.root.after(
            0,
            self._print_message,
            "Hệ thống",
            "Đã kết nối với peer."
        )

        self.root.after(
            0,
            self._set_connected,
            True
        )

        threading.Thread(
            target=self._receive_loop,
            daemon=True
        ).start()

    # =====================================================
    # NHẬN DỮ LIỆU
    # =====================================================

    def _receive_loop(self):

        while self.sock:

            try:

                data = self.sock.recv(4096)

            except OSError:

                break

            if not data:
                break

            raw_data = data.decode(
                "utf-8",
                errors="replace"
            )

            # Giải mã JSON

            message = MessageProtocol.parse_json_message(
                raw_data
            )

            if message:

                sender = message.get(
                    "sender_name",
                    "Peer"
                )

                content = message.get(
                    "content",
                    ""
                )

                timestamp = message.get(
                    "timestamp"
                )

                # Kiểm tra Reply

                reply_to = message.get(
                    "reply_to"
                )

                if reply_to:

                    original_content = reply_to.get(
                        "content",
                        ""
                    )

                    display_text = (
                        f"↩ Reply: \"{original_content}\"\n"
                        f"   {content}"
                    )

                else:

                    display_text = content

                # Kiểm tra Forward

                if message.get(
                    "is_forwarded",
                    False
                ):

                    display_text = (
                        f"↪ Forward: {display_text}"
                    )

                self.root.after(
                    0,
                    self._print_message,
                    sender,
                    display_text,
                    timestamp
                )

            else:

                self.root.after(
                    0,
                    self._print_message,
                    "Peer",
                    raw_data
                )

        # Peer ngắt kết nối

        if self.sock:

            self.root.after(
                0,
                self._print_message,
                "Hệ thống",
                "Peer đã ngắt kết nối."
            )

            self.root.after(
                0,
                self.on_disconnect
            )

    # =====================================================
    # NGẮT KẾT NỐI
    # =====================================================

    def on_disconnect(self):

        for s in (
            self.sock,
            self.server_sock
        ):

            if s:

                try:
                    s.close()

                except OSError:
                    pass

        self.sock = None
        self.server_sock = None

        self._print_message(
            "Hệ thống",
            "Đã ngắt kết nối."
        )

        self._set_connected(False)

    # =====================================================
    # GỬI TIN NHẮN
    # =====================================================

    def on_send(self):

        text = self.msg_entry.get().strip()

        if not text:
            return

        if not self.sock:
            return

        try:

            # Đóng gói thành JSON

            json_message = MessageProtocol.create_json_message(
                sender_name=self.my_name,
                content=text
            )

            # Gửi JSON

            self.sock.sendall(
                json_message.encode("utf-8")
            )

            # Hiển thị bên mình

            self._print_message(
                "Bạn",
                text
            )

            self.msg_entry.delete(
                0,
                tk.END
            )

        except OSError as e:

            messagebox.showerror(
                "Lỗi gửi tin nhắn",
                str(e)
            )

            self.on_disconnect()

    # =====================================================
    # HIỂN THỊ EMOJI
    # =====================================================

    def show_emoji(self):

        emoji_window = tk.Toplevel(
            self.root
        )

        emoji_window.title(
            "Chọn Emoji"
        )

        emoji_window.geometry(
            "300x300"
        )

        emojis = [
            "😀",
            "😂",
            "😍",
            "😊",
            "😢",
            "😡",
            "👍",
            "👎",
            "❤️",
            "🎉"
        ]

        tk.Label(
            emoji_window,
            text="Chọn Emoji",
            font=("Arial", 14)
        ).pack(pady=10)

        frame = tk.Frame(
            emoji_window
        )

        frame.pack()

        for index, emoji in enumerate(emojis):

            button = tk.Button(
                frame,
                text=emoji,
                font=("Arial", 18),
                width=4,
                command=lambda e=emoji:
                self.select_emoji(e, emoji_window)
            )

            button.grid(
                row=index // 2,
                column=index % 2,
                padx=5,
                pady=5
            )

    # =====================================================
    # CHỌN EMOJI
    # =====================================================

    def select_emoji(self, emoji, window):

        if not self.sock:

            messagebox.showwarning(
                "Chưa kết nối",
                "Bạn cần kết nối với peer trước."
            )

            window.destroy()
            return

        try:

            json_message = MessageProtocol.create_json_message(
                sender_name=self.my_name,
                content=emoji
            )

            self.sock.sendall(
                json_message.encode("utf-8")
            )

            self._print_message(
                "Bạn",
                emoji
            )

        except OSError as e:

            messagebox.showerror(
                "Lỗi gửi Emoji",
                str(e)
            )

            self.on_disconnect()

        window.destroy()


# =========================================================
# CHẠY CHƯƠNG TRÌNH
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = P2PChatGUI(root)

    root.mainloop()