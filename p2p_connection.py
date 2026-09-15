"""Optimized peer-to-peer TCP networking layer for UDM_09."""
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
    hello_sent: bool = False
    hello_received: bool = False
    online_notified: bool = False


class P2PConnection:
    def __init__(self, peer_id: str, peer_name: str, port: int = 5000,
                 avatar_base64: str = "", on_message: Optional[Callable[[str, dict], None]] = None,
                 on_peer_status: Optional[Callable[[dict], None]] = None,
                 on_error: Optional[Callable[[str], None]] = None) -> None:
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

    def start(self) -> None:
        if self._running:
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(20)
        server.settimeout(1.0)
        self._server = server
        self._running = True
        self._accept_thread = threading.Thread(target=self._accept_loop, name="accept-loop", daemon=True)
        self._accept_thread.start()

    def stop(self) -> None:
        self._running = False
        server, self._server = self._server, None
        if server:
            try: server.close()
            except OSError: pass

        with self._connections_lock:
            connections = list(set(map(id, self._connections.values())))
            # Keep actual objects while removing duplicate dictionary entries.
            peers = []
            seen = set()
            for conn in self._connections.values():
                if id(conn) not in seen:
                    peers.append(conn); seen.add(id(conn))
            self._connections.clear()

        goodbye = MessageProtocol.create_goodbye(self.peer_id, self.peer_name).encode("utf-8")
        for conn in peers:
            try:
                with conn.send_lock:
                    conn.sock.sendall(goodbye)
            except OSError:
                pass
            self._close_connection(conn, notify=False)

    def _accept_loop(self) -> None:
        while self._running:
            server = self._server
            if not server:
                break
            try:
                sock, address = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._setup_connection(sock, address)

    def _setup_connection(self, sock: socket.socket, address: Tuple[str, int]) -> PeerConnection:
        sock.settimeout(1.0)
        conn = PeerConnection(sock=sock, address=address)
        threading.Thread(target=self._receive_loop, args=(conn,),
                         name=f"recv-{address[0]}:{address[1]}", daemon=True).start()
        return conn

    def _send_hello(self, conn: PeerConnection) -> bool:
        if not conn.alive or conn.hello_sent:
            return conn.alive
        hello = MessageProtocol.create_hello(self.peer_id, self.peer_name, self.port, self.avatar_base64)
        try:
            with conn.send_lock:
                if not conn.alive or conn.hello_sent:
                    return conn.alive
                conn.sock.sendall(hello.encode("utf-8"))
                conn.hello_sent = True
            return True
        except OSError:
            self._close_connection(conn, notify=True)
            return False

    def connect_to_peer(self, host: str, port: Optional[int] = None) -> None:
        port = port or self.port
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((host, port))
            conn = self._setup_connection(sock, (host, port))
            self._send_hello(conn)
        except OSError as exc:
            self._report_error(f"Không thể kết nối {host}:{port} - {exc}")
            if sock is not None:
                try: sock.close()
                except OSError: pass

    def send_to_peer(self, peer_id: str, message: str) -> bool:
        with self._connections_lock:
            conn = self._connections.get(peer_id)
        if not conn or not conn.alive:
            return False
        try:
            with conn.send_lock:
                conn.sock.sendall(message.encode("utf-8"))
            return True
        except OSError:
            self._close_connection(conn, notify=True)
            return False

    def broadcast(self, message: str) -> None:
        with self._connections_lock:
            peer_ids = list(self._connections)
        for peer_id in peer_ids:
            self.send_to_peer(peer_id, message)

    def broadcast_avatar_update(self, avatar_base64: str) -> None:
        """Gửi avatar MỚI của chính mình cho tất cả peer đang kết nối, để họ
        thấy ngay mà không cần ngắt/kết nối lại. Đồng thời cập nhật avatar mặc
        định dùng cho các lần HELLO tiếp theo (kết nối mới sau này)."""
        self.avatar_base64 = avatar_base64
        message = MessageProtocol.create_avatar_update(self.peer_id, self.peer_name, avatar_base64)
        with self._connections_lock:
            connections = list(self._connections.values())
        for conn in connections:
            if not conn.alive:
                continue
            try:
                with conn.send_lock:
                    conn.sock.sendall(message.encode("utf-8"))
                conn.avatar_base64 = avatar_base64
            except OSError:
                self._close_connection(conn, notify=True)

    def disconnect_peer(self, peer_id: str) -> None:
        with self._connections_lock:
            conn = self._connections.get(peer_id)
        if not conn:
            return
        try:
            goodbye = MessageProtocol.create_goodbye(self.peer_id, self.peer_name).encode("utf-8")
            with conn.send_lock:
                conn.sock.sendall(goodbye)
        except OSError:
            pass
        self._close_connection(conn, notify=True)

    def get_peers(self) -> Dict[str, PeerConnection]:
        with self._connections_lock:
            return dict(self._connections)

    def _receive_loop(self, conn: PeerConnection) -> None:
        buffer = ""
        try:
            while self._running and conn.alive:
                try:
                    data = conn.sock.recv(8192)
                    if not data:
                        break
                    buffer += data.decode("utf-8", errors="replace")
                    messages, buffer = MessageProtocol.extract_frames(buffer)
                    for message in messages:
                        self._handle_message(conn, message)
                        if not conn.alive:
                            break
                except socket.timeout:
                    continue
                except (ConnectionResetError, BrokenPipeError, OSError):
                    break
        finally:
            self._close_connection(conn, notify=True)

    def _handle_message(self, conn: PeerConnection, message: dict) -> None:
        msg_type = message.get("type")

        if msg_type == "HELLO":
            remote_id = message.get("sender_id")
            if not remote_id or remote_id == self.peer_id:
                self._close_connection(conn, notify=False)
                return

            first_hello = not conn.hello_received
            conn.hello_received = True
            conn.peer_id = remote_id
            conn.peer_name = message.get("sender_name", "Unknown")
            conn.avatar_base64 = message.get("avatar_base64", "")

            with self._connections_lock:
                old = self._connections.get(remote_id)
                self._connections[remote_id] = conn

            if old and old is not conn:
                # Keep one connection only. Closing the old socket prevents duplicate
                # receive threads and duplicate UI updates.
                self._close_connection(old, notify=False)

            # IMPORTANT: answer at most once. This prevents HELLO <-> HELLO loops.
            if not conn.hello_sent and not self._send_hello(conn):
                return

            if first_hello and not conn.online_notified:
                conn.online_notified = True
                self._notify_status("online", conn)
            return

        if msg_type == "GOODBYE":
            self._close_connection(conn, notify=True)
            return

        if msg_type == "AVATAR_UPDATE":
            if conn.peer_id:
                conn.avatar_base64 = message.get("avatar_base64", "")
                # Peer chỉ gửi cập nhật avatar khi đang online, nên trạng thái giữ nguyên "online".
                self._notify_status("online", conn)
            return

        if conn.peer_id and self.on_message:
            self.on_message(conn.peer_id, message)

    def _close_connection(self, conn: PeerConnection, notify: bool) -> None:
        if not conn.alive:
            return
        conn.alive = False
        try: conn.sock.shutdown(socket.SHUT_RDWR)
        except OSError: pass
        try: conn.sock.close()
        except OSError: pass

        peer_id = conn.peer_id
        if peer_id:
            removed = False
            with self._connections_lock:
                if self._connections.get(peer_id) is conn:
                    self._connections.pop(peer_id, None)
                    removed = True
            if notify and removed and conn.online_notified:
                self._notify_status("offline", conn)

    def _notify_status(self, status: str, conn: PeerConnection) -> None:
        if self.on_peer_status and conn.peer_id:
            self.on_peer_status({
                "peer_id": conn.peer_id, "name": conn.peer_name,
                "address": conn.address, "status": status,
                "avatar_base64": conn.avatar_base64,
            })

    def _report_error(self, message: str) -> None:
        if self.on_error:
            self.on_error(message)
