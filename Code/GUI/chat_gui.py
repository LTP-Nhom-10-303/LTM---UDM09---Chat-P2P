"""Main GUI for UDM_09 P2P Chat."""

from __future__ import annotations

import base64
import io
import socket
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Dict, List, Optional

from PIL import Image, ImageTk

from GUI.forward import build_forward_message
from GUI.peer_list import PeerList
from GUI.peer_manager import PeerManager
from GUI.reply_emoji import EMOJIS, reply_preview
from network.p2p_connection import P2PConnection
from protocol.message_protocol import MessageProtocol


class ChatGUI:
    BG = "#f4f6f8"
    PANEL = "#ffffff"
    TEXT = "#17202a"
    MUTED = "#6b7280"
    ACCENT = "#2563eb"
    GREEN = "#16a34a"
    RED = "#dc2626"

    def __init__(self, root: tk.Tk, username: str, port: int = 5000):
        self.root = root
        self.username = username
        self.peer_id = f"peer_{uuid.uuid4().hex[:8]}"
        self.port = port
        self.avatar_base64 = ""
        self._own_avatar_photo = None  # giữ tham chiếu PhotoImage để không bị garbage-collect
        self.local_ip = self._get_local_ip()

        self.peer_manager = PeerManager(self._on_peer_list_changed)
        self.selected_peer_id: Optional[str] = None
        self.selected_message: Optional[dict] = None
        self.histories: Dict[str, List[dict]] = {}
        self.message_index: Dict[str, Dict[str, dict]] = {}
        self.emoji_visible = False
        self._peer_render_pending = False

        self.network = P2PConnection(
            peer_id=self.peer_id,
            peer_name=self.username,
            port=self.port,
            avatar_base64=self.avatar_base64,
            on_message=self._network_message,
            on_peer_status=self._network_peer_status,
            on_error=self._network_error,
        )

        self._build_style()
        self._build_ui()
        self._show_local_identity()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        try:
            self.network.start()
        except OSError as exc:
            messagebox.showerror(
                "Không thể mở Port",
                f"Không thể mở port {self.port}.\n\n{exc}\n\nHãy thử port khác, ví dụ 5001.",
            )

    # ---------- UI ----------
    def _build_style(self):
        self.root.configure(bg=self.BG)
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.PANEL)
        style.configure(
            "Header.TLabel",
            background=self.BG,
            foreground=self.TEXT,
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 9, "bold"),
            padding=(10, 7),
        )
        style.configure("Accent.TButton", background=self.ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])
        style.configure("Connect.TButton", background="#0f766e", foreground="white")
        style.configure("Danger.TButton", background="#b91c1c", foreground="white")
        style.configure("TEntry", padding=7)
        style.configure(
            "Treeview",
            rowheight=30,
            font=("Segoe UI", 9),
            background="white",
            fieldbackground="white",
            foreground=self.TEXT,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#e8edf3",
            foreground=self.TEXT,
        )
        style.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", self.TEXT)],
        )

    def _build_ui(self):
        self.root.title(f"UDM_09 — P2P Chat | {self.username}")
        self.root.geometry("1180x720")
        self.root.minsize(980, 620)

        outer = ttk.Frame(self.root)
        outer.pack(fill="both", expand=True, padx=18, pady=14)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="UDM_09 — P2P Chat", style="Header.TLabel").pack(side="left")
        self.connection_label = ttk.Label(header, text="● Đang khởi động...", style="Sub.TLabel")
        self.connection_label.pack(side="right", pady=7)

        content = ttk.Frame(outer)
        content.pack(fill="both", expand=True)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # LEFT PANEL
        left = ttk.Frame(content, style="Card.TFrame", padding=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.configure(width=300)

        ttk.Label(left, text="Peer List", style="CardTitle.TLabel").pack(anchor="w")

        identity_row = ttk.Frame(left, style="Card.TFrame")
        identity_row.pack(fill="x", pady=(3, 10))
        self.own_avatar_label = tk.Label(identity_row, text="👤", font=("Arial", 20), bg=self.PANEL)
        self.own_avatar_label.pack(side="left", padx=(0, 8))
        identity_col = ttk.Frame(identity_row, style="Card.TFrame")
        identity_col.pack(side="left", fill="x", expand=True)
        self.identity_label = ttk.Label(identity_col, text="", style="Sub.TLabel", justify="left")
        self.identity_label.pack(anchor="w")
        ttk.Button(identity_col, text="Đổi avatar của tôi", command=self._choose_own_avatar).pack(anchor="w", pady=(5, 0))

        self.peer_list_widget = PeerList(left, on_select=self._on_peer_selected)
        self.peer_list_widget.pack(fill="both", expand=True)

        ttk.Separator(left).pack(fill="x", pady=10)
        ttk.Label(left, text="Kết nối Peer", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        conn_row = ttk.Frame(left, style="Card.TFrame")
        conn_row.pack(fill="x")
        self.ip_var = tk.StringVar(value="192.168.1.10")
        self.port_var = tk.StringVar(value=str(self.port))
        ttk.Entry(conn_row, textvariable=self.ip_var, width=18).pack(side="left", fill="x", expand=True)
        ttk.Entry(conn_row, textvariable=self.port_var, width=7).pack(side="left", padx=(6, 0))
        ttk.Button(left, text="Connect", style="Connect.TButton", command=self._connect_clicked).pack(fill="x", pady=(7, 4))
        ttk.Button(left, text="Disconnect Peer", style="Danger.TButton", command=self._disconnect_clicked).pack(fill="x")

        # RIGHT PANEL
        right = ttk.Frame(content, style="Card.TFrame", padding=12)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        topbar = ttk.Frame(right, style="Card.TFrame")
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        topbar.columnconfigure(0, weight=1)
        self.chat_title = ttk.Label(topbar, text="Chọn một Peer để bắt đầu", style="CardTitle.TLabel")
        self.chat_title.grid(row=0, column=0, sticky="w")
        self.peer_status_label = ttk.Label(topbar, text="", style="Sub.TLabel")
        self.peer_status_label.grid(row=1, column=0, sticky="w")

        self.chat_tree = ttk.Treeview(
            right,
            columns=("time", "sender", "message", "kind"),
            show="headings",
            selectmode="browse",
        )
        self.chat_tree.heading("time", text="Time")
        self.chat_tree.heading("sender", text="Người gửi")
        self.chat_tree.heading("message", text="Nội dung")
        self.chat_tree.heading("kind", text="Type")
        self.chat_tree.column("time", width=72, stretch=False)
        self.chat_tree.column("sender", width=120, stretch=False)
        self.chat_tree.column("message", width=450)
        self.chat_tree.column("kind", width=90, stretch=False)
        self.chat_tree.grid(row=1, column=0, sticky="nsew")
        self.chat_tree.bind("<<TreeviewSelect>>", self._on_message_selected)

        action = ttk.Frame(right, style="Card.TFrame")
        action.grid(row=2, column=0, sticky="ew", pady=(8, 7))
        ttk.Button(action, text="↩ Reply", command=self._reply_clicked).pack(side="left")
        ttk.Button(action, text="↗ Forward", command=self._forward_clicked).pack(side="left", padx=6)
        ttk.Button(action, text="😊 Emoji", command=self._toggle_emoji).pack(side="left")
        self.selected_label = ttk.Label(action, text="Chưa chọn message", style="Sub.TLabel")
        self.selected_label.pack(side="right")

        self.emoji_frame = ttk.Frame(right, style="Card.TFrame")
        # Created now, packed only when toggled.
        for emoji in EMOJIS:
            ttk.Button(
                self.emoji_frame,
                text=emoji,
                width=3,
                command=lambda e=emoji: self._insert_emoji(e),
            ).pack(side="left", padx=1)

        input_row = ttk.Frame(right, style="Card.TFrame")
        input_row.grid(row=4, column=0, sticky="ew", pady=(7, 0))
        input_row.columnconfigure(0, weight=1)

        self.reply_banner = ttk.Label(input_row, text="", style="Sub.TLabel")
        self.reply_banner.grid(row=0, column=0, sticky="w", pady=(0, 4))

        compose = ttk.Frame(input_row, style="Card.TFrame")
        compose.grid(row=1, column=0, sticky="ew")
        compose.columnconfigure(0, weight=1)

        self.message_var = tk.StringVar()
        entry = ttk.Entry(compose, textvariable=self.message_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        entry.bind("<Return>", lambda _e: self._send_clicked())
        self.message_entry = entry

        ttk.Button(compose, text="Send", style="Accent.TButton", command=self._send_clicked).grid(row=0, column=1)

        self._set_chat_enabled(False)

    def _show_local_identity(self):
        self.identity_label.configure(
            text=f"🟢 {self.username}\nID: {self.peer_id}\nIP: {self.local_ip}\nPort: {self.port}"
        )
        self.connection_label.configure(text=f"● Listening {self.local_ip}:{self.port}", foreground=self.GREEN)

    def _choose_own_avatar(self):
        """Đổi avatar của CHÍNH máy này (ví dụ: A đổi avatar của A).
        Ảnh này sẽ được gửi kèm khi kết nối/nhắn tin, nên phía peer bên kia sẽ
        thấy đúng avatar của mình dưới tên peer_id của mình — không lẫn sang
        avatar của peer khác."""
        path = filedialog.askopenfilename(
            title="Chọn avatar của bạn",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                send_img = img.resize((64, 64), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                send_img.save(buf, format="JPEG", quality=82)
                preview_img = img.resize((40, 40), Image.Resampling.LANCZOS)
                preview_photo = ImageTk.PhotoImage(preview_img)
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể đọc ảnh: {exc}")
            return

        self.avatar_base64 = base64.b64encode(buf.getvalue()).decode("ascii")
        # Gửi ngay avatar mới cho TẤT CẢ peer đang kết nối (không cần ngắt/kết nối lại).
        # Đồng thời cập nhật avatar dùng cho các kết nối mới sau này.
        self.network.broadcast_avatar_update(self.avatar_base64)

        self._own_avatar_photo = preview_photo
        self.own_avatar_label.configure(text="", image=preview_photo)

    def _set_chat_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        try:
            self.message_entry.configure(state=state)
        except Exception:
            pass

    # ---------- Peer handling ----------
    def _connect_clicked(self):
        host = self.ip_var.get().strip()
        try:
            port = int(self.port_var.get().strip())
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Port không hợp lệ", "Port phải là số từ 1 đến 65535.")
            return
        if not host:
            messagebox.showwarning("Thiếu IP", "Nhập IP của máy Peer cần kết nối.")
            return
        self.connection_label.configure(text=f"● Đang kết nối {host}:{port}...", foreground="#ca8a04")
        threading_call = lambda: self.network.connect_to_peer(host, port)
        import threading
        threading.Thread(target=threading_call, daemon=True).start()

    def _disconnect_clicked(self):
        if not self.selected_peer_id:
            messagebox.showinfo("Disconnect", "Chọn một Peer trước.")
            return
        self.network.disconnect_peer(self.selected_peer_id)

    def _on_peer_selected(self, peer_id: str):
        self.selected_peer_id = peer_id
        peer = self.peer_manager.get(peer_id) or {}
        addr = peer.get("address")
        address = f"{addr[0]}:{addr[1]}" if addr else "-"
        status = peer.get("status")
        dot = "●" if status == "online" else "○"
        self.chat_title.configure(text=f"Chat với {peer.get('name', 'Unknown')}")
        self.peer_status_label.configure(text=f"{dot} {address}")
        self._set_chat_enabled(status == "online")
        self._render_history(peer_id)

    def _on_peer_list_changed(self, _peers):
        # Many network events can arrive together. Render once per UI cycle.
        if self._peer_render_pending:
            return
        self._peer_render_pending = True
        self.root.after_idle(self._render_peer_list)

    def _render_peer_list(self):
        self._peer_render_pending = False
        self.peer_list_widget.sync_from_peer_manager(self.peer_manager.peers)

    # ---------- Messages ----------
    def _network_message(self, peer_id: str, message: dict):
        self.root.after(0, lambda: self._receive_message_ui(peer_id, message))

    def _receive_message_ui(self, peer_id: str, message: dict):
        msg_type = message.get("type")
        if msg_type not in ("CHAT", "FORWARD"):
            return
        message = dict(message)
        message["direction"] = "in"
        self._store_message(peer_id, message)
        # Do not call set_status here: every message used to trigger a complete
        # peer-list refresh, causing visible lag.
        if self.selected_peer_id == peer_id:
            self._append_message_to_tree(message)

    def _send_clicked(self):
        if not self.selected_peer_id:
            messagebox.showinfo("Chưa chọn Peer", "Chọn một Peer trước khi gửi.")
            return
        content = self.message_var.get().strip()
        if not content:
            return

        peer = self.peer_manager.get(self.selected_peer_id)
        if not peer or peer.get("status") != "online":
            messagebox.showwarning("Peer Offline", "Peer đang offline hoặc chưa kết nối.")
            return

        reply_to = reply_preview(self.selected_message) if self.selected_message and self.reply_banner.cget("text") else None
        raw = MessageProtocol.create_chat_message(
            self.peer_id,
            self.username,
            content,
            reply_to=reply_to,
            avatar_base64=self.avatar_base64,
        )
        if not self.network.send_to_peer(self.selected_peer_id, raw):
            messagebox.showerror("Send lỗi", "Không gửi được message. Peer có thể đã ngắt kết nối.")
            return

        msg = MessageProtocol.parse_message(raw)
        assert msg is not None
        msg["direction"] = "out"
        self._store_message(self.selected_peer_id, msg)
        self.message_var.set("")
        self.selected_message = None
        self.reply_banner.configure(text="")
        self.selected_label.configure(text="Đã gửi")
        self._append_message_to_tree(msg)
        self.message_entry.focus_set()

    def _store_message(self, peer_id: str, msg: dict):
        self.histories.setdefault(peer_id, []).append(msg)
        msg_id = msg.get("msg_id")
        if msg_id:
            self.message_index.setdefault(peer_id, {})[msg_id] = msg

    def _message_values(self, msg: dict):
        sender = "Bạn" if msg.get("direction") == "out" else msg.get("sender_name", "Unknown")
        content = msg.get("content", "")
        kind = msg.get("type", "CHAT")
        if msg.get("reply_to"):
            reply = msg["reply_to"]
            content = f"↩ {reply.get('sender_name', '')}: {reply.get('content', '')} | {content}"
            kind = "REPLY"
        if msg.get("is_forwarded"):
            content = f"↗ {msg.get('original_sender', 'Unknown')}: {content}"
            kind = "FORWARD"
        return (msg.get("timestamp", ""), sender, content, kind)

    def _append_message_to_tree(self, msg: dict):
        msg_id = msg.get("msg_id") or f"row_{uuid.uuid4().hex}"
        values = self._message_values(msg)
        if self.chat_tree.exists(msg_id):
            self.chat_tree.item(msg_id, values=values)
        else:
            self.chat_tree.insert("", "end", iid=msg_id, values=values)
        self.chat_tree.see(msg_id)

    def _render_history(self, peer_id: str):
        # Full render only when changing peer, not for every new message.
        children = self.chat_tree.get_children()
        if children:
            self.chat_tree.delete(*children)
        for msg in self.histories.get(peer_id, []):
            self._append_message_to_tree(msg)

    def _on_message_selected(self, _event=None):
        if not self.selected_peer_id:
            return
        selection = self.chat_tree.selection()
        if not selection:
            return
        msg_id = selection[0]
        msg = self.message_index.get(self.selected_peer_id, {}).get(msg_id)
        if msg:
            self.selected_message = msg
            self.selected_label.configure(text=f"Selected: {msg_id}")

    def _reply_clicked(self):
        if not self.selected_message:
            messagebox.showinfo("Reply", "Chọn một message trước.")
            return
        preview = reply_preview(self.selected_message)
        self.reply_banner.configure(
            text=f"↩ Reply {preview['sender_name']}: {preview['content'][:90]}"
        )
        self.message_entry.focus_set()

    def _forward_clicked(self):
        if not self.selected_message:
            messagebox.showinfo("Forward", "Chọn một message trước.")
            return
        online = self.peer_manager.online_peers()
        if not online:
            messagebox.showinfo("Forward", "Không có Peer online để Forward.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Forward message")
        dialog.geometry("330x270")
        dialog.transient(self.root)
        ttk.Label(dialog, text="Chọn Peer nhận Forward", font=("Segoe UI", 11, "bold")).pack(pady=12)
        lb = tk.Listbox(dialog, height=8, font=("Segoe UI", 10))
        lb.pack(fill="both", expand=True, padx=14)
        lookup = {}
        for idx, peer in enumerate(online):
            text = f"{peer.get('name', 'Unknown')} — {peer.get('address', ('?', '?'))[0]}"
            lb.insert(idx, text)
            lookup[idx] = peer

        def do_forward():
            sel = lb.curselection()
            if not sel:
                return
            peer = lookup[sel[0]]
            raw = build_forward_message(
                self.peer_id, self.username, self.selected_message, self.avatar_base64
            )
            if not self.network.send_to_peer(peer["peer_id"], raw):
                messagebox.showerror("Forward lỗi", "Không gửi được Forward.")
                return
            msg = MessageProtocol.parse_message(raw)
            if msg:
                msg["direction"] = "out"
                self._store_message(peer["peer_id"], msg)
            dialog.destroy()
            if self.selected_peer_id == peer["peer_id"]:
                self._append_message_to_tree(msg)

        ttk.Button(dialog, text="Forward", style="Accent.TButton", command=do_forward).pack(pady=12)

    def _toggle_emoji(self):
        if self.emoji_visible:
            self.emoji_frame.grid_forget()
            self.emoji_visible = False
            return
        self.emoji_frame.grid(row=3, column=0, sticky="w", pady=(2, 2))
        self.emoji_visible = True

    def _insert_emoji(self, emoji: str):
        self.message_var.set(self.message_var.get() + emoji)
        self.message_entry.focus_set()

    # ---------- Networking callbacks ----------
    def _network_peer_status(self, info: dict):
        self.root.after(0, lambda: self._apply_peer_status(info))

    def _apply_peer_status(self, info: dict):
        self.peer_manager.upsert(info)
        status = info.get("status")
        name = info.get("name", "Peer")
        if status == "online":
            self.connection_label.configure(text=f"● Connected: {name}", foreground=self.GREEN)
            if self.selected_peer_id == info.get("peer_id"):
                addr = info.get("address")
                address = f"{addr[0]}:{addr[1]}" if addr else "-"
                self.peer_status_label.configure(text=f"● {address}")
                self._set_chat_enabled(True)
        elif status == "offline":
            if self.selected_peer_id == info.get("peer_id"):
                self.peer_status_label.configure(text="○ Offline")
                self._set_chat_enabled(False)
            # Cập nhật lại chữ góc trên phải: nếu vẫn còn peer khác đang online thì
            # hiển thị peer đó, nếu không còn ai online thì quay về trạng thái Listening.
            still_online = self.peer_manager.online_peers()
            if still_online:
                other = still_online[0]
                self.connection_label.configure(
                    text=f"● Connected: {other.get('name', 'Peer')}", foreground=self.GREEN
                )
            else:
                self.connection_label.configure(
                    text=f"● Listening {self.local_ip}:{self.port}", foreground=self.GREEN
                )

    def _network_error(self, message: str):
        self.root.after(0, lambda: self._show_error(message))

    def _show_error(self, message: str):
        self.connection_label.configure(text="● Network error", foreground=self.RED)
        messagebox.showwarning("Network", message)

    # ---------- Misc ----------
    @staticmethod
    def _get_local_ip() -> str:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            sock.close()
            return ip
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "127.0.0.1"

    def _on_close(self):
        if messagebox.askyesno("Thoát", "Bạn có muốn đóng ứng dụng không?"):
            self.network.stop()
            self.root.destroy()
