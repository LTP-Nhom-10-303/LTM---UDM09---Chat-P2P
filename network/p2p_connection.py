import json
import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

# ==============================================================================
# 1. LỚP XỬ LÝ KẾT NỐI P2P (SOCKET TCP)
# ==============================================================================
class P2PConnection:
    def __init__(self, my_port, on_message=None, on_status=None):
        self.my_port = int(my_port)
        self.on_message = on_message
        self.on_status = on_status

        self.peer_socket = None
        self.listener_socket = None
        self.connected = False
        self._lock = threading.Lock()

    def start_listening(self):
        """Khởi chạy luồng lắng nghe ở background"""
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        try:
            self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener_socket.bind(("0.0.0.0", self.my_port))
            self.listener_socket.listen(1)
            self._notify_status(f"Đang lắng nghe kết nối ở Port {self.my_port}...")
        except Exception as e:
            self._notify_status(f"Lỗi không mở được port {self.my_port}: {e}")
            return

        while True:
            try:
                conn, addr = self.listener_socket.accept()
            except OSError:
                break  # Socket đã đóng

            with self._lock:
                if self.connected:
                    conn.close()  # Đã kết nối với 1 peer rồi thì từ chối peer khác
                    continue
                self.peer_socket = conn
                self.connected = True

            self._notify_status(f"Peer {addr[0]}:{addr[1]} đã kết nối tới bạn!")
            threading.Thread(target=self._receive_loop, daemon=True).start()

    def connect_to_peer(self, peer_ip, peer_port, timeout=5):
        """Chủ động kết nối tới IP/Port của bạn chat"""
        with self._lock:
            if self.connected:
                self._notify_status("Đã có kết nối, không thể tạo thêm!")
                return False

        self._notify_status(f"Đang kết nối tới {peer_ip}:{peer_port}...")

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((peer_ip, int(peer_port)))
            s.settimeout(None)
        except socket.timeout:
            self._notify_status("Thất bại: Hết thời gian chờ (Timeout).")
            return False
        except ConnectionRefusedError:
            self._notify_status(f"Thất bại: Port {peer_port} đối phương chưa mở.")
            return False
        except Exception as e:
            self._notify_status(f"Không kết nối được: {e}")
            return False

        with self._lock:
            if self.connected:
                s.close()
                return False
            self.peer_socket = s
            self.connected = True

        self._notify_status(f"Kết nối thành công tới peer {peer_ip}:{peer_port}!")
        threading.Thread(target=self._receive_loop, daemon=True).start()
        return True

    def _receive_loop(self):
        sock = self.peer_socket
        buffer = ""
        while True:
            try:
                data = sock.recv(4096)
            except OSError:
                break
            if not data:
                break

            buffer += data.decode("utf-8", errors="ignore")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if self.on_message:
                    self.on_message(msg)

        self._handle_disconnect()

    def send(self, message: dict) -> bool:
        if not self.connected or not self.peer_socket:
            self._notify_status("Chưa kết nối, không thể gửi tin!")
            return False
        try:
            data = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
            self.peer_socket.sendall(data)
            return True
        except OSError as e:
            self._notify_status(f"Gửi thất bại: {e}")
            self._handle_disconnect()
            return False

    def _handle_disconnect(self):
        with self._lock:
            if self.connected:
                self.connected = False
                if self.peer_socket:
                    try:
                        self.peer_socket.close()
                    except OSError:
                        pass
                    self.peer_socket = None
                self._notify_status("Đối phương đã ngắt kết nối.")

    def close(self):
        with self._lock:
            self.connected = False
            if self.peer_socket:
                try:
                    self.peer_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.peer_socket.close()
            if self.listener_socket:
                self.listener_socket.close()

    def _notify_status(self, text):
        if self.on_status:
            self.on_status(text)


# ==============================================================================
# 2. GIAO DIỆN NGUỜI DÙNG (GUI TKINTER)
# ==============================================================================
class P2PChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Chat P2P (Python TKinter)")
        self.root.geometry("520x580")

        self.p2p = None

        # --- Khung 1: Cấu hình Port cá nhân ---
        frame_top = tk.LabelFrame(root, text=" 1. Cấu hình Port cá nhân ", padx=10, pady=5)
        frame_top.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_top, text="Port của bạn:").pack(side="left")
        self.ent_my_port = tk.Entry(frame_top, width=10)
        self.ent_my_port.insert(0, "8000")
        self.ent_my_port.pack(side="left", padx=5)

        self.btn_listen = tk.Button(frame_top, text="Mở Lắng Nghe", command=self.start_listen, bg="#4CAF50", fg="white")
        self.btn_listen.pack(side="left", padx=5)

        # --- Khung 2: Kết nối đến Peer ---
        frame_conn = tk.LabelFrame(root, text=" 2. Kết nối tới Peer (Bạn Chat) ", padx=10, pady=5)
        frame_conn.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_conn, text="IP Peer:").pack(side="left")
        self.ent_peer_ip = tk.Entry(frame_conn, width=15)
        self.ent_peer_ip.insert(0, "127.0.0.1")
        self.ent_peer_ip.pack(side="left", padx=2)

        tk.Label(frame_conn, text="Port Peer:").pack(side="left")
        self.ent_peer_port = tk.Entry(frame_conn, width=8)
        self.ent_peer_port.insert(0, "8001")
        self.ent_peer_port.pack(side="left", padx=2)

        self.btn_connect = tk.Button(frame_conn, text="Kết Nối", command=self.connect_peer, bg="#2196F3", fg="white")
        self.btn_connect.pack(side="left", padx=5)

        # --- Khung 3: Cửa sổ Chat ---
        frame_chat = tk.Frame(root)
        frame_chat.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_chat = scrolledtext.ScrolledText(frame_chat, state="disabled", wrap="word")
        self.txt_chat.pack(fill="both", expand=True)

        # --- Khung 4: Soạn tin nhắn ---
        frame_bottom = tk.Frame(root, pady=10)
        frame_bottom.pack(fill="x", padx=10)

        self.ent_msg = tk.Entry(frame_bottom)
        self.ent_msg.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ent_msg.bind("<Return>", lambda event: self.send_message())

        self.btn_send = tk.Button(frame_bottom, text="Gửi", command=self.send_message, width=10, bg="#FF9800", fg="white")
        self.btn_send.pack(side="right")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, text):
        self.txt_chat.config(state="normal")
        self.txt_chat.insert(tk.END, text + "\n")
        self.txt_chat.see(tk.END)
        self.txt_chat.config(state="disabled")

    def start_listen(self):
        my_port = self.ent_my_port.get().strip()
        if not my_port.isdigit():
            messagebox.showerror("Lỗi", "Port phải là chuỗi số!")
            return

        self.p2p = P2PConnection(
            my_port=int(my_port),
            on_message=self.on_message_received,
            on_status=lambda stt: self.root.after(0, self.log, f"[HỆ THỐNG]: {stt}")
        )
        self.p2p.start_listening()
        self.btn_listen.config(state="disabled")

    def connect_peer(self):
        if not self.p2p:
            messagebox.showwarning("Cảnh báo", "Bạn phải bấm 'Mở Lắng Nghe' trước!")
            return

        peer_ip = self.ent_peer_ip.get().strip()
        peer_port = self.ent_peer_port.get().strip()

        if not peer_ip or not peer_port.isdigit():
            messagebox.showerror("Lỗi", "IP/Port của peer không hợp lệ!")
            return

        threading.Thread(
            target=self.p2p.connect_to_peer,
            args=(peer_ip, int(peer_port)),
            daemon=True
        ).start()

    def send_message(self):
        msg_text = self.ent_msg.get().strip()
        if not msg_text or not self.p2p:
            return

        msg_data = {"sender": f"Port_{self.p2p.my_port}", "content": msg_text}
        if self.p2p.send(msg_data):
            self.log(f"Tôi: {msg_text}")
            self.ent_msg.delete(0, tk.END)

    def on_message_received(self, msg):
        sender = msg.get("sender", "Bạn chat")
        content = msg.get("content", "")
        self.root.after(0, self.log, f"[{sender}]: {content}")

    def on_close(self):
        if self.p2p:
            self.p2p.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = P2PChatGUI(root)
    root.mainloop()
