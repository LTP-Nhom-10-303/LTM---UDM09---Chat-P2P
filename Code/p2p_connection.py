"""
p2p_connection.py
Hỗ trợ Multi-Peer, Validation gói tin và Ghi Log ra file.
"""

import json
import logging
import os
import socket
import threading

# --- 1. Cấu hình Logging (Ghi log vào thư mục Extra/logs) ---
LOG_DIR = os.path.join("Extra", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


class P2PConnection:

    def __init__(self, my_port, on_message=None, on_status=None):
        self.my_port = int(my_port)
        self.on_message = on_message
        self.on_status = on_status

        # Quản lý MULTI-PEER: Dùng dict để lưu nhiều kết nối {address_str: socket}
        self.peers = {}
        self.listener_socket = None
        self._lock = threading.Lock()

    def start_listening(self):
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        try:
            self.listener_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM
            )
            self.listener_socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
            self.listener_socket.bind(("0.0.0.0", self.my_port))
            self.listener_socket.listen(5)  # Hỗ trợ hàng chờ nhiều kết nối
            self._log_and_notify(
                f"Đang lắng nghe kết nối ở port {self.my_port}..."
            )
        except Exception as e:
            self._log_and_notify(
                f"Lỗi mở port {self.my_port}: {e}", level="error"
            )
            return

        while True:
            try:
                conn, addr = self.listener_socket.accept()
            except OSError:
                break

            peer_addr = f"{addr[0]}:{addr[1]}"
            with self._lock:
                self.peers[peer_addr] = conn

            self._log_and_notify(f"Peer mới đã kết nối tới: {peer_addr}")
            threading.Thread(
                target=self._receive_loop,
                args=(conn, peer_addr),
                daemon=True,
            ).start()

    def connect_to_peer(self, peer_ip, peer_port, timeout=5):
        peer_addr = f"{peer_ip}:{peer_port}"
        with self._lock:
            if peer_addr in self.peers:
                self._log_and_notify(f"Đã kết nối với {peer_addr} rồi!")
                return False

        self._log_and_notify(f"Đang kết nối tới {peer_addr}...")

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((peer_ip, int(peer_port)))
            s.settimeout(None)
        except Exception as e:
            self._log_and_notify(
                f"Lỗi kết nối tới {peer_addr}: {e}", level="error"
            )
            return False

        with self._lock:
            self.peers[peer_addr] = s

        self._log_and_notify(f"Kết nối thành công tới peer {peer_addr}!")
        threading.Thread(
            target=self._receive_loop, args=(s, peer_addr), daemon=True
        ).start()
        return True

    # --- 2. Kiểm tra dữ liệu hợp lệ (Validation) ---
    def _validate_message(self, msg: dict) -> bool:
        """Bắt buộc gói tin phải có đủ các trường: type, sender, content"""
        required_fields = ["type", "sender", "content"]
        for field in required_fields:
            if field not in msg:
                return False
        return True

    def _receive_loop(self, sock, peer_addr):
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
                    # Thực hiện validate gói tin
                    if not self._validate_message(msg):
                        self._log_and_notify(
                            f"Gói tin không hợp lệ từ {peer_addr}: Thiếu trường dữ liệu!",
                            level="warning",
                        )
                        continue
                except json.JSONDecodeError:
                    self._log_and_notify(
                        f"Lỗi định dạng JSON từ {peer_addr}", level="warning"
                    )
                    continue

                if self.on_message:
                    self.on_message(msg)

        self._remove_peer(peer_addr)

    # --- 3. Gửi tin nhắn Broadcast cho tất cả các Peer ---
    def send_broadcast(self, content: str, msg_type: str = "chat") -> bool:
        message = {
            "type": msg_type,
            "sender": f"Port_{self.my_port}",
            "content": content,
        }

        data = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
        success = False

        with self._lock:
            disconnected_peers = []
            for peer_addr, sock in self.peers.items():
                try:
                    sock.sendall(data)
                    success = True
                except OSError:
                    disconnected_peers.append(peer_addr)

            for peer_addr in disconnected_peers:
                self._remove_peer(peer_addr)

        return success

    def _remove_peer(self, peer_addr):
        if peer_addr in self.peers:
            try:
                self.peers[peer_addr].close()
            except OSError:
                pass
            del self.peers[peer_addr]
            self._log_and_notify(f"Peer {peer_addr} đã ngắt kết nối.")

    def close(self):
        with self._lock:
            for peer_addr, sock in list(self.peers.items()):
                try:
                    sock.close()
                except OSError:
                    pass
            self.peers.clear()

            if self.listener_socket:
                self.listener_socket.close()
        self._log_and_notify("Đã đóng tất cả kết nối P2P.")

    # --- 4. Hàm hỗ trợ ghi Log và hiển thị Status ---
    def _log_and_notify(self, text, level="info"):
        if level == "error":
            logging.error(text)
        elif level == "warning":
            logging.warning(text)
        else:
            logging.info(text)

        if self.on_status:
            self.on_status(text)
