import socket, threading, tkinter as tk
from datetime import datetime

TIMEOUT_CONNECT, TIMEOUT_ACCEPT, MAX_LEN = 5, 10, 500

class P2PChat:
    def __init__(self, root):
        self.root = root
        root.title("P2PChat"); root.geometry("600x500")
        self.sock = self.srv = None

        top = tk.Frame(root); top.pack(fill="x", pady=4)
        tk.Label(top, text="IP:").pack(side="left")
        self.ip = tk.Entry(top, width=12); self.ip.insert(0, "127.0.0.1"); self.ip.pack(side="left")
        tk.Label(top, text="Port:").pack(side="left")
        self.port = tk.Entry(top, width=6); self.port.insert(0, "5000"); self.port.pack(side="left")
        self.btn_conn = tk.Button(top, text="Kết nối", command=self.connect); self.btn_conn.pack(side="left", padx=4)
        self.btn_disc = tk.Button(top, text="Ngắt", command=self.disconnect, state="disabled"); self.btn_disc.pack(side="left")
        self.status = tk.Label(top, text="Chưa kết nối", fg="gray"); self.status.pack(side="left", padx=8)

        self.chat = tk.Text(root, state="disabled", wrap="word"); self.chat.pack(fill="both", expand=True, padx=4)

        bottom = tk.Frame(root); bottom.pack(fill="x", pady=4)
        self.entry = tk.Entry(bottom, state="disabled"); self.entry.pack(side="left", fill="x", expand=True, padx=4)
        self.entry.bind("<Return>", lambda e: self.send())
        self.btn_send = tk.Button(bottom, text="Gửi", command=self.send, state="disabled"); self.btn_send.pack(side="left", padx=4)

        root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------- UI helpers ----------
    def log(self, text, tag=""):
        self.chat.config(state="normal")
        prefix = f"[{datetime.now():%H:%M}] " if tag != "sys" else ""
        self.chat.insert("end", f"{prefix}{text}\n")
        self.chat.see("end")
        self.chat.config(state="disabled")

    def set_status(self, text, color):
        self.status.config(text=text, fg=color)

    # ---------- Kết nối ----------
    def connect(self):
        ip, port_s = self.ip.get().strip(), self.port.get().strip()
        if not ip or not port_s.isdigit():
            self.log("⚠ IP/Port không hợp lệ.", "sys"); return
        port = int(port_s)
        self.btn_conn.config(state="disabled")
        self.set_status("Đang kết nối...", "orange")
        self.log(f"Đang kết nối tới {ip}:{port} ...", "sys")
        threading.Thread(target=self._connect_worker, args=(ip, port), daemon=True).start()

    def _connect_worker(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(TIMEOUT_CONNECT)
            s.connect((ip, port))
            s.settimeout(None)
            self.sock = s
        except OSError:
            s.close()
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                srv.bind(("0.0.0.0", port)); srv.listen(1); srv.settimeout(TIMEOUT_ACCEPT)
                self.srv = srv
                self.root.after(0, self.log, f"Đang chờ peer tới cổng {port} ...", "sys")
                conn, _ = srv.accept()
                self.sock = conn
            except OSError as e:
                srv.close(); self.srv = None
                self.root.after(0, self._connect_failed, str(e)); return
        self.root.after(0, self._connect_ok)
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _connect_ok(self):
        self.set_status("Đã kết nối", "green")
        self.log("Kết nối thành công.", "sys")
        for w in (self.entry, self.btn_send): w.config(state="normal")
        self.btn_disc.config(state="normal")

    def _connect_failed(self, err):
        self.set_status("Thất bại", "red")
        self.log(f"Kết nối thất bại: {err}", "sys")
        self.btn_conn.config(state="normal")

    def _recv_loop(self):
        while self.sock:
            try:
                data = self.sock.recv(4096)
            except OSError:
                break
            if not data: break
            text = data.decode("utf-8", errors="replace")
            self.root.after(0, self.log, f"Peer: {text}")
        if self.sock:
            self.root.after(0, self.log, "Peer đã ngắt kết nối.", "sys")
            self.root.after(0, self.disconnect)

    # ---------- Gửi ----------
    def send(self):
        text = self.entry.get()
        if not text.strip(): return
        if len(text) > MAX_LEN or not text.isprintable():
            self.log("⚠ Tin nhắn không hợp lệ.", "sys"); return
        if not self.sock:
            self.log("⚠ Chưa kết nối.", "sys"); return
        try:
            self.sock.sendall(text.encode("utf-8"))
        except OSError:
            self.log("⚠ Gửi thất bại.", "sys"); self.disconnect(); return
        self.entry.delete(0, "end")
        self.log(f"Tôi: {text}")

    # ---------- Ngắt kết nối ----------
    def disconnect(self):
        for s in (self.sock, self.srv):
            if s:
                try: s.close()
                except OSError: pass
        self.sock = self.srv = None
        self.set_status("Chưa kết nối", "gray")
        self.log("Đã ngắt kết nối.", "sys")
        for w in (self.entry, self.btn_send): w.config(state="disabled")
        self.btn_disc.config(state="disabled")
        self.btn_conn.config(state="normal")

    def close(self):
        self.disconnect(); self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    P2PChat(root)
    root.mainloop()