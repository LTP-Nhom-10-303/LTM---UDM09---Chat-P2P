from __future__ import annotations

import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime

class Theme:
    BG          = "#f4f5fa"
    PANEL       = "#ffffff"
    CARD        = "#f7f7fc"
    BORDER      = "#e4e5ef"
    TEXT        = "#1f2233"
    TEXT_DIM    = "#8a8d9e"
    ACCENT      = "#5b53f0"
    ACCENT_SOFT = "#eeecfd"
    ACCENT_HOV  = "#4a42dd"
    BUBBLE_OUT  = "#5b53f0"
    BUBBLE_IN   = "#eef0f6"
    AVATAR_BG   = "#1e9e79"

    IDLE        = "#9599a8"
    CONNECTING  = "#e0a527"
    SUCCESS     = "#1e9e79"
    FAILED      = "#e5566c"

    FONT = "Segoe UI"


STATUS_TEXT = {
    "idle": "Chưa kết nối", "connecting": "Đang kết nối...",
    "success": "Kết nối thành công", "failed": "Kết nối thất bại",
}
STATUS_COLOR = {
    "idle": Theme.IDLE, "connecting": Theme.CONNECTING,
    "success": Theme.SUCCESS, "failed": Theme.FAILED,
}

CONNECT_TIMEOUT = 5
ACCEPT_TIMEOUT = 10
MAX_MSG_LEN = 500


def avatar_text(name: str) -> str:
    return (name.strip()[:1] or "?").upper()


class Badge(tk.Frame):
    """Huy hiệu trạng thái: chấm tròn màu + chữ, nền pill bo góc."""

    def __init__(self, parent, bg_parent=Theme.PANEL):
        super().__init__(parent, bg=bg_parent)
        self.dot = tk.Canvas(self, width=8, height=8, bg=bg_parent, highlightthickness=0)
        self.dot.pack(side=tk.LEFT)
        self.dot_id = self.dot.create_oval(1, 1, 7, 7, fill=Theme.IDLE, outline="")
        self.label = tk.Label(self, text=STATUS_TEXT["idle"], bg=bg_parent,
                               fg=Theme.IDLE, font=(Theme.FONT, 9, "bold"))
        self.label.pack(side=tk.LEFT, padx=(5, 0))

    def set_state(self, state: str):
        color = STATUS_COLOR[state]
        self.dot.itemconfig(self.dot_id, fill=color)
        self.label.config(text=STATUS_TEXT[state], fg=color)


class Avatar(tk.Canvas):

    def __init__(self, parent, letter: str, size=44, bg_parent=Theme.PANEL, color=Theme.AVATAR_BG):
        super().__init__(parent, width=size, height=size, bg=bg_parent, highlightthickness=0)
        self.create_oval(2, 2, size - 2, size - 2, fill=color, outline="")
        self.create_text(size / 2, size / 2, text=letter, fill="white",
                          font=(Theme.FONT, int(size * 0.36), "bold"))


class P2PChatApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("P2PChat — UDM_09")
        root.geometry("980x600")
        root.minsize(820, 480)
        root.configure(bg=Theme.BG)

        self.sock: socket.socket | None = None
        self.server_sock: socket.socket | None = None
        self.peer_name = "Peer"
        self.peer_addr = "—"
        self.peer_ip = ""
        self.peer_port = None
        self.sent_count = 0
        self.recv_count = 0
        self.connected_since = None

        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._tick()

    # ------------------------------------------------------------------
    def _build(self):
        wrap = tk.Frame(self.root, bg=Theme.BG)
        wrap.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        self._build_left(wrap)
        self._build_center(wrap)
        self._build_right(wrap)

    # ---- CỘT TRÁI: thẻ Peer + cấu hình địa chỉ ----
    def _build_left(self, parent):
        col = tk.Frame(parent, bg=Theme.PANEL, width=260, highlightbackground=Theme.BORDER,
                        highlightthickness=1)
        col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        col.pack_propagate(False)

        tk.Label(col, text="P2P Chat", bg=Theme.PANEL, fg=Theme.TEXT,
                 font=(Theme.FONT, 13, "bold")).pack(anchor="w", padx=18, pady=(18, 0))
        tk.Label(col, text="Kết nối trực tiếp, không qua server", bg=Theme.PANEL,
                 fg=Theme.TEXT_DIM, font=(Theme.FONT, 8)).pack(anchor="w", padx=18, pady=(0, 14))

        tk.Frame(col, bg=Theme.BORDER, height=1).pack(fill=tk.X, padx=18)

        # ---- Card peer (1 peer duy nhất - đúng mô hình P2P 2 máy) ----
        card = tk.Frame(col, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        card.pack(fill=tk.X, padx=18, pady=18)

        row = tk.Frame(card, bg=Theme.CARD)
        row.pack(fill=tk.X, padx=12, pady=12)
        Avatar(row, avatar_text(self.peer_name), bg_parent=Theme.CARD).pack(side=tk.LEFT)
        info = tk.Frame(row, bg=Theme.CARD)
        info.pack(side=tk.LEFT, padx=10)
        self.peer_name_lbl = tk.Label(info, text=self.peer_name, bg=Theme.CARD, fg=Theme.TEXT,
                                       font=(Theme.FONT, 11, "bold"))
        self.peer_name_lbl.pack(anchor="w")
        self.peer_addr_lbl = tk.Label(info, text="Chưa cấu hình", bg=Theme.CARD, fg=Theme.TEXT_DIM,
                                       font=(Theme.FONT, 8))
        self.peer_addr_lbl.pack(anchor="w")

        tk.Label(card, text="IP peer", bg=Theme.CARD, fg=Theme.TEXT_DIM,
                 font=(Theme.FONT, 8)).pack(anchor="w", padx=12)
        self.ip_entry = tk.Entry(card, relief="flat", bg="white", fg=Theme.TEXT,
                                  font=(Theme.FONT, 10), highlightthickness=1,
                                  highlightbackground=Theme.BORDER, highlightcolor=Theme.ACCENT)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(fill=tk.X, padx=12, pady=(2, 8), ipady=5)

        tk.Label(card, text="Port", bg=Theme.CARD, fg=Theme.TEXT_DIM,
                 font=(Theme.FONT, 8)).pack(anchor="w", padx=12)
        self.port_entry = tk.Entry(card, relief="flat", bg="white", fg=Theme.TEXT,
                                    font=(Theme.FONT, 10), highlightthickness=1,
                                    highlightbackground=Theme.BORDER, highlightcolor=Theme.ACCENT)
        self.port_entry.insert(0, "5000")
        self.port_entry.pack(fill=tk.X, padx=12, pady=(2, 10), ipady=5)

        self.connect_btn = tk.Button(card, text="Kết nối", command=self.on_connect,
                                      bg=Theme.ACCENT, fg="white", relief="flat",
                                      activebackground=Theme.ACCENT_HOV, activeforeground="white",
                                      font=(Theme.FONT, 10, "bold"), cursor="hand2")
        self.connect_btn.pack(fill=tk.X, padx=12, pady=(0, 8), ipady=6)

        self.disconnect_btn = tk.Button(card, text="Ngắt kết nối", command=self.on_disconnect,
                                         bg="white", fg=Theme.FAILED, relief="flat",
                                         highlightthickness=1, highlightbackground=Theme.BORDER,
                                         activebackground="#fdecee", activeforeground=Theme.FAILED,
                                         font=(Theme.FONT, 10), cursor="hand2", state=tk.DISABLED)
        self.disconnect_btn.pack(fill=tk.X, padx=12, pady=(0, 12), ipady=6)

        tk.Label(col, text="TRẠNG THÁI", bg=Theme.PANEL, fg=Theme.TEXT_DIM,
                 font=(Theme.FONT, 8, "bold")).pack(anchor="w", padx=18)
        self.badge_left = Badge(col)
        self.badge_left.pack(anchor="w", padx=18, pady=(4, 18))

    # ---- CỘT GIỮA: khung chat ----
    def _build_center(self, parent):
        col = tk.Frame(parent, bg=Theme.PANEL, highlightbackground=Theme.BORDER, highlightthickness=1)
        col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 14))

        header = tk.Frame(col, bg=Theme.PANEL, height=64)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        hrow = tk.Frame(header, bg=Theme.PANEL)
        hrow.pack(side=tk.LEFT, padx=16, pady=10)
        self.avatar_center = Avatar(hrow, avatar_text(self.peer_name))
        self.avatar_center.pack(side=tk.LEFT)
        htext = tk.Frame(hrow, bg=Theme.PANEL)
        htext.pack(side=tk.LEFT, padx=10)
        self.chat_title = tk.Label(htext, text=self.peer_name, bg=Theme.PANEL, fg=Theme.TEXT,
                                    font=(Theme.FONT, 12, "bold"))
        self.chat_title.pack(anchor="w")
        self.badge_header = Badge(htext)
        self.badge_header.pack(anchor="w")

        tk.Frame(col, bg=Theme.BORDER, height=1).pack(fill=tk.X)

        # ---- khung tin nhắn (canvas cuộn) ----
        chat_wrap = tk.Frame(col, bg=Theme.BG)
        chat_wrap.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(chat_wrap, bg=Theme.BG, highlightthickness=0)
        vsb = ttk.Scrollbar(chat_wrap, orient="vertical", command=self.canvas.yview)
        self.msg_frame = tk.Frame(self.canvas, bg=Theme.BG)
        self.msg_frame.bind("<Configure>",
                             lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_win = self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_win, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-e.delta / 120), "units"))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.placeholder = tk.Label(self.msg_frame, text="Bấm Kết nối để bắt đầu trò chuyện",
                                     bg=Theme.BG, fg=Theme.TEXT_DIM, font=(Theme.FONT, 10))
        self.placeholder.pack(pady=40)

        # ---- ô nhập ----
        bottom = tk.Frame(col, bg=Theme.PANEL)
        bottom.pack(fill=tk.X)
        tk.Frame(bottom, bg=Theme.BORDER, height=1).pack(fill=tk.X)
        row = tk.Frame(bottom, bg=Theme.PANEL)
        row.pack(fill=tk.X, padx=14, pady=12)

        entry_card = tk.Frame(row, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
        entry_card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.msg_entry = tk.Entry(entry_card, bg=Theme.CARD, fg=Theme.TEXT, relief="flat",
                                   font=(Theme.FONT, 10), state=tk.DISABLED)
        self.msg_entry.pack(fill=tk.X, padx=10, pady=8)
        self.msg_entry.bind("<Return>", lambda e: self.on_send())

        self.send_btn = tk.Button(row, text="Gửi", command=self.on_send,
                                   bg=Theme.ACCENT, fg="white", relief="flat",
                                   activebackground=Theme.ACCENT_HOV, activeforeground="white",
                                   font=(Theme.FONT, 10, "bold"), cursor="hand2", state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, ipadx=16, ipady=7)

        self.warn_label = tk.Label(bottom, text="", bg=Theme.PANEL, fg=Theme.CONNECTING,
                                    font=(Theme.FONT, 8), anchor="w")
        self.warn_label.pack(fill=tk.X, padx=14, pady=(0, 8))

    # ---- CỘT PHẢI: chi tiết phiên kết nối ----
    def _build_right(self, parent):
        col = tk.Frame(parent, bg=Theme.PANEL, width=230, highlightbackground=Theme.BORDER,
                        highlightthickness=1)
        col.pack(side=tk.LEFT, fill=tk.Y)
        col.pack_propagate(False)

        tk.Label(col, text="Chi tiết kết nối", bg=Theme.PANEL, fg=Theme.TEXT,
                 font=(Theme.FONT, 11, "bold")).pack(anchor="w", padx=16, pady=(18, 12))

        self.detail_rows = {}
        for key, label in [
            ("local", "Địa chỉ của bạn"),
            ("peer_ip", "IP"), ("peer_port", "Port"),
            ("since", "Kết nối lúc"), ("sent", "Đã gửi"), ("recv", "Đã nhận"),
        ]:
            box = tk.Frame(col, bg=Theme.CARD, highlightbackground=Theme.BORDER, highlightthickness=1)
            box.pack(fill=tk.X, padx=16, pady=4)
            tk.Label(box, text=label, bg=Theme.CARD, fg=Theme.TEXT_DIM,
                     font=(Theme.FONT, 7)).pack(anchor="w", padx=10, pady=(6, 0))
            val = tk.Label(box, text="—", bg=Theme.CARD, fg=Theme.TEXT, font=(Theme.FONT, 9, "bold"))
            val.pack(anchor="w", padx=10, pady=(0, 6))
            self.detail_rows[key] = val

        self.detail_rows["local"].config(text=self._get_local_ip())

    def _refresh_details(self):
        self.detail_rows["peer_ip"].config(text=self.peer_ip or "—")
        self.detail_rows["peer_port"].config(text=str(self.peer_port) if self.peer_port else "—")
        self.detail_rows["sent"].config(text=str(self.sent_count))
        self.detail_rows["recv"].config(text=str(self.recv_count))
        if self.connected_since:
            self.detail_rows["since"].config(text=self.connected_since.strftime("%H:%M:%S"))
        else:
            self.detail_rows["since"].config(text="—")

    def _tick(self):
        self.root.after(1000, self._tick)

    @staticmethod
    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"

    # ------------------------------------------------------------------
    # BONG BÓNG TIN NHẮN (bọc an toàn - lỗi vẽ UI không làm mất dữ liệu)
    # ------------------------------------------------------------------
    def _safe_bubble(self, text: str, is_me: bool, system: bool = False):
        try:
            self._bubble(text, is_me, system)
        except Exception as e:
            print(f"[GUI] Lỗi vẽ bong bóng tin nhắn: {e}")

    def _bubble(self, text: str, is_me: bool, system: bool = False):
        if self.placeholder.winfo_exists():
            self.placeholder.destroy()

        row = tk.Frame(self.msg_frame, bg=Theme.BG)
        row.pack(fill=tk.X, padx=14, pady=4)

        if system:
            tk.Label(row, text=text, bg=Theme.BG, fg=Theme.TEXT_DIM,
                     font=(Theme.FONT, 8, "italic")).pack(anchor="center")
        else:
            side = tk.RIGHT if is_me else tk.LEFT
            bg = Theme.BUBBLE_OUT if is_me else Theme.BUBBLE_IN
            fg = "white" if is_me else Theme.TEXT
            bubble = tk.Frame(row, bg=bg)
            bubble.pack(side=side)
            tk.Label(bubble, text=text, bg=bg, fg=fg, font=(Theme.FONT, 10),
                     wraplength=360, justify="left", padx=12, pady=7).pack()
            tk.Label(row, text=datetime.now().strftime("%H:%M"), bg=Theme.BG, fg=Theme.TEXT_DIM,
                     font=(Theme.FONT, 7)).pack(side=side, padx=3)

        self.msg_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1.0)

    # ------------------------------------------------------------------
    # KẾT NỐI - chạy nền, có timeout, không treo GUI
    # ------------------------------------------------------------------
    def on_connect(self):
        ip = self.ip_entry.get().strip()
        port_text = self.port_entry.get().strip()
        if not ip or not port_text.isdigit():
            self.warn_label.config(text="⚠ IP/Port không hợp lệ.")
            return

        port = int(port_text)
        self.peer_ip = ip
        self.peer_port = port
        self.peer_addr = f"{ip}:{port}"
        self.peer_addr_lbl.config(text=self.peer_addr)
        self.connect_btn.config(state=tk.DISABLED)
        for b in (self.badge_left, self.badge_header):
            b.set_state("connecting")
        self._safe_bubble(f"Đang kết nối tới {self.peer_addr} ...", is_me=False, system=True)

        threading.Thread(target=self._connect_worker, args=(ip, port), daemon=True).start()

    def _connect_worker(self, ip: str, port: int):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(CONNECT_TIMEOUT)
            s.connect((ip, port))
            s.settimeout(None)
            self.sock = s
        except OSError:
            # connect() thất bại -> đóng socket vừa tạo, không để rò rỉ file descriptor
            try:
                s.close()
            except OSError:
                pass

            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                srv.bind(("0.0.0.0", port))
                srv.listen(1)
                srv.settimeout(ACCEPT_TIMEOUT)
                self.server_sock = srv
                self.root.after(0, self._safe_bubble, f"Đang chờ peer kết nối tới cổng {port} ...", False, True)
                conn, _ = srv.accept()
                self.sock = conn
            except OSError as e:
                # QUAN TRỌNG: đóng server_sock ngay khi thất bại/timeout, nếu không
                # cổng vẫn còn ở trạng thái lắng nghe từ lần thử trước -> lần bấm
                # "Kết nối" tiếp theo có thể kết nối "thành công" một cách khó hiểu
                # vào đúng socket cũ đang bỏ dở này (race condition + resource leak).
                try:
                    srv.close()
                except OSError:
                    pass
                self.server_sock = None
                self.root.after(0, self._on_connect_failed, str(e))
                return

        self.root.after(0, self._on_connect_success)
        threading.Thread(target=self._receive_loop, daemon=True).start()

    def _on_connect_success(self):
        self.connected_since = datetime.now()
        for b in (self.badge_left, self.badge_header):
            b.set_state("success")
        self.chat_title.config(text=self.peer_addr)
        self._safe_bubble("Kết nối thành công.", is_me=False, system=True)
        self.msg_entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.NORMAL)
        self._refresh_details()

    def _on_connect_failed(self, err: str):
        for b in (self.badge_left, self.badge_header):
            b.set_state("failed")
        self._safe_bubble(f"Kết nối thất bại: {err}", is_me=False, system=True)
        self.connect_btn.config(state=tk.NORMAL)

    # ------------------------------------------------------------------
    def _receive_loop(self):
        while self.sock:
            try:
                data = self.sock.recv(4096)
            except OSError:
                break
            if not data:
                break
            try:
                text = data.decode("utf-8", errors="replace")
            except Exception:
                text = "[Dữ liệu không hợp lệ]"
            self.recv_count += 1
            self.root.after(0, self._safe_bubble, text, False, False)
            self.root.after(0, self._refresh_details)

        if self.sock:
            self.root.after(0, self._safe_bubble, "Peer đã ngắt kết nối.", False, True)
            self.root.after(0, self.on_disconnect)

    # ------------------------------------------------------------------
    # GỬI TIN NHẮN - validate trước khi gửi, xoá ô nhập ngay khi gửi
    # mạng thành công (không phụ thuộc việc vẽ UI có lỗi hay không)
    # ------------------------------------------------------------------
    def on_send(self):
        self.warn_label.config(text="")
        text = self.msg_entry.get()

        if not text.strip():
            self.warn_label.config(text="⚠ Tin nhắn trống.")
            return
        if len(text) > MAX_MSG_LEN:
            self.warn_label.config(text=f"⚠ Tin nhắn vượt quá {MAX_MSG_LEN} ký tự.")
            return
        if not text.isprintable():
            self.warn_label.config(text="⚠ Tin nhắn chứa ký tự không hợp lệ.")
            return
        if not self.sock:
            self.warn_label.config(text="⚠ Chưa kết nối.")
            return

        try:
            self.sock.sendall(text.encode("utf-8"))
        except OSError:
            self.warn_label.config(text="⚠ Gửi thất bại - kết nối đã mất.")
            self.on_disconnect()
            return

        self.sent_count += 1
        self._refresh_details()
        self.msg_entry.delete(0, tk.END)
        self._safe_bubble(text, is_me=True)

    # ------------------------------------------------------------------
    # NGẮT KẾT NỐI / ĐÓNG APP - luôn giải phóng tài nguyên
    # ------------------------------------------------------------------
    def on_disconnect(self):
        for s in (self.sock, self.server_sock):
            if s:
                try:
                    s.close()
                except OSError:
                    pass
        self.sock = None
        self.server_sock = None
        self.connected_since = None

        for b in (self.badge_left, self.badge_header):
            b.set_state("idle")
        self.chat_title.config(text=self.peer_name)
        self._safe_bubble("Đã ngắt kết nối.", is_me=False, system=True)

        self.msg_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.connect_btn.config(state=tk.NORMAL)
        self._refresh_details()

    def on_close(self):
        self.on_disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    P2PChatApp(root)
    root.mainloop()
