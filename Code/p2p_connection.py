""Peer-to-peer TCP networking layer for UDM_09.

Each running application is both a TCP server and a TCP client.
There is no central relay/server.
"""

from __future__ import annotations

import socket
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from protocol.message_protocol import MessageProtocol


@dataclass
class PeerConnection:
    sock: socket.socket
    address: Tuple[str, int]
    peer_id: Optional[str] = None
    peer_name: str = "Unknown"
    avatar_base64: str = ""
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    alive: bool = True

    
class P2PConnection:
    def __init__(
        self,
        peer_id: str,
        peer_name: str,
        port: int = 5000,
        avatar_base64: str = "",
        on_message: Optional[Callable[[str, dict], None]] = None,
        on_peer_status: Optional[Callable[[dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.peer_id = peer_id
        self.peer_name = peer_name
        self.port = port
        self.avatar_base64 = avatar_base64
        self.on_message = on_message
        self.on_peer_status = on_peer_status
        self.on_error = on_error

        self._server: Optional[socket.socket] = None
        self._accept_thread: Optional[threading.Thread] = None
        self._running = False
        self._connections: Dict[str, PeerConnection] = {}
        self._connections_lock = threading.RLock()
        self._unnamed_connections: set[PeerConnection] = set()
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
