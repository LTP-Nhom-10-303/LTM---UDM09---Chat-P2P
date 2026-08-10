"""
p2p_connection.py
Kết nối P2P trực tiếp giữa 2 client qua TCP socket, không dùng server trung gian.

Cơ chế:
- Mỗi peer mở 1 socket "listener" để chờ peer kia kết nối tới (giống server).
- Đồng thời có thể chủ động connect tới peer kia (giống client).
- Bên nào kết nối được trước thì dùng luôn kết nối đó, bên còn lại
  không cần chủ động connect nữa.
- Chỉ hỗ trợ 1 peer tại 1 thời điểm (đúng yêu cầu "chat P2P giữa 2 client").
"""

import socket
import threading
import json


class P2PConnection:
    def __init__(self, my_port, on_message=None, on_status=None):
        """
        my_port: port mà client này sẽ lắng nghe kết nối đến.
        on_message(dict): callback khi nhận được 1 message hoàn chỉnh.
        on_status(str): callback khi có thay đổi trạng thái (để GUI hiển thị log).
        """
        self.my_port = my_port
        self.on_message = on_message
        self.on_status = on_status

        self.peer_socket = None
        self.listener_socket = None
        self.connected = False
        self._lock = threading.Lock()

    # ---------- Lắng nghe kết nối đến ----------
    def start_listening(self):
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.bind(("0.0.0.0", self.my_port))
        self.listener_socket.listen(1)
        self._notify_status(f"Đang lắng nghe ở port {self.my_port}...")

        while True:
            try:
                conn, addr = self.listener_socket.accept()
            except OSError:
                break  # socket đã bị đóng (close())

            with self._lock:
                if self.connected:
                    conn.close()  # đã có peer rồi, từ chối kết nối thêm
                    continue
                self.peer_socket = conn
                self.connected = True

            self._notify_status(f"Peer {addr[0]}:{addr[1]} đã kết nối tới bạn.")
            threading.Thread(target=self._receive_loop, daemon=True).start()

    # ---------- Chủ động kết nối tới peer ----------
    def connect_to_peer(self, peer_ip, peer_port, timeout=5):
        with self._lock:
            if self.connected:
                self._notify_status("Đã có kết nối, bỏ qua yêu cầu connect mới.")
                return False

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((peer_ip, peer_port))
            s.settimeout(None)
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._notify_status(f"Không kết nối được tới {peer_ip}:{peer_port} ({e})")
            return False

        with self._lock:
            if self.connected:
                s.close()
                return False
            self.peer_socket = s
            self.connected = True

        self._notify_status(f"Đã kết nối tới peer {peer_ip}:{peer_port}.")
        threading.Thread(target=self._receive_loop, daemon=True).start()
        return True

    # ---------- Nhận dữ liệu ----------
    def _receive_loop(self):
        sock = self.peer_socket
        buffer = ""
        while True:
            try:
                data = sock.recv(4096)
            except OSError:
                break
            if not data:
                break  # peer đóng kết nối

            buffer += data.decode("utf-8")
            # Mỗi message là 1 dòng JSON, phân cách bằng "\n"
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

    # ---------- Gửi dữ liệu ----------
    def send(self, message: dict) -> bool:
        if not self.connected or not self.peer_socket:
            self._notify_status("Chưa có kết nối, không gửi được.")
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
            self.connected = False
            if self.peer_socket:
                try:
                    self.peer_socket.close()
                except OSError:
                    pass
                self.peer_socket = None
        self._notify_status("Peer đã ngắt kết nối.")

    def close(self):
        with self._lock:
            self.connected = False
            if self.peer_socket:
                self.peer_socket.close()
            if self.listener_socket:
                self.listener_socket.close()

    def _notify_status(self, text):
        if self.on_status:
            self.on_status(text)
        else:
            print(f"[STATUS] {text}")
