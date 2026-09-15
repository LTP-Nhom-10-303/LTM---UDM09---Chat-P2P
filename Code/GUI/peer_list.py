
from __future__ import annotations

import base64
import io
import tkinter as tk
from PIL import Image, ImageTk


class PeerList(tk.Frame):
    def __init__(self, master=None, on_select=None):
        super().__init__(master)
        self.on_select = on_select
        self.peers: dict[str, dict] = {}
        self.selected_peer_id: str | None = None
        self.default_avatar = "👤"
        self.avatar_images: dict[str, tuple] = {}  # peer_id -> (signature, PhotoImage)
        self.rows: dict[str, dict] = {}
        self._search_after = None

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=5, pady=5)
        tk.Label(search_frame, text="🔍", font=("Arial", 13)).pack(side="left", padx=(5, 3))
        self.search_box = tk.Entry(search_frame)
        self.search_box.pack(side="left", fill="x", expand=True)
        self.search_box.bind("<KeyRelease>", self.search_peer)

        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def upsert_peer(self, peer_id, name, online, address=""):
        current = self.peers.get(peer_id, {})
        current.update({"name": name, "online": online, "address": address})
        current.setdefault("avatar_b64", None)
        self.peers[peer_id] = current
        self.show_peers()

    def update_peer_status(self, peer_id, online):
        if peer_id in self.peers and self.peers[peer_id].get("online") != online:
            self.peers[peer_id]["online"] = online
            self.show_peers()

    def remove_peer(self, peer_id):
        self.peers.pop(peer_id, None)
        self.avatar_images.pop(peer_id, None)
        row = self.rows.pop(peer_id, None)
        if row:
            row["frame"].destroy()

    def sync_from_peer_manager(self, peers: dict):
        new = {}
        for peer_id, info in peers.items():
            new[peer_id] = {
                "name": info.get("name", "Unknown"),
                "online": info.get("status") == "online",
                "address": f"{info['address'][0]}:{info['address'][1]}" if info.get("address") else "",
                # Ảnh mà chính peer_id này gửi qua mạng — luôn lấy từ dữ liệu mới nhất của đúng peer đó.
                "avatar_b64": info.get("avatar_base64") or None,
            }
        self.peers = new
        for peer_id in list(self.rows):
            if peer_id not in new:
                self.rows[peer_id]["frame"].destroy()
                self.rows.pop(peer_id, None)
                self.avatar_images.pop(peer_id, None)
        self.show_peers()

    def get_avatar(self, peer_id):
        item = self.peers.get(peer_id, {})
        b64 = item.get("avatar_b64")
        signature = ("b64", b64) if b64 else None

        cached = self.avatar_images.get(peer_id)
        if cached and cached[0] == signature:
            return cached[1]

        if signature is None:
            self.avatar_images.pop(peer_id, None)
            return self.default_avatar

        try:
            image = Image.open(io.BytesIO(base64.b64decode(b64)))
            with image:
                image = image.convert("RGB").resize((50, 50), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.avatar_images[peer_id] = (signature, photo)
            return photo
        except Exception:
            self.avatar_images.pop(peer_id, None)
            return self.default_avatar

    def search_peer(self, _event=None):
        # Debounce typing so a long list is not refreshed for every keystroke.
        if self._search_after:
            self.after_cancel(self._search_after)
        self._search_after = self.after(100, self.show_peers)

    def _create_row(self, peer_id):
        frame = tk.Frame(self.list_frame, bd=1, relief="solid", padx=5, pady=5, cursor="hand2")
        avatar_label = tk.Label(frame, font=("Arial", 25))
        avatar_label.pack(side="left")
        name_label = tk.Label(frame, font=("Arial", 11, "bold"))
        name_label.pack(side="left", padx=10)
        status_label = tk.Label(frame, font=("Arial", 10))
        status_label.pack(side="left", padx=10)
        address_label = tk.Label(frame, fg="#6b7280", font=("Arial", 8))
        address_label.pack(side="left", padx=6)
        for widget in (frame, avatar_label, name_label, status_label, address_label):
            widget.bind("<Button-1>", lambda _e, p=peer_id: self.select_peer(p))
        row = {"frame": frame, "avatar": avatar_label, "name": name_label,
               "status": status_label, "address": address_label}
        self.rows[peer_id] = row
        return row

    def _update_row(self, peer_id, item):
        row = self.rows.get(peer_id) or self._create_row(peer_id)
        avatar = self.get_avatar(peer_id)
        if avatar == self.default_avatar:
            row["avatar"].configure(text="👤", image="")
        else:
            row["avatar"].configure(text="", image=avatar)
            row["avatar"].image = avatar
        row["name"].configure(text=item["name"])
        row["status"].configure(text="● Online" if item["online"] else "● Offline",
                                fg="green" if item["online"] else "gray")
        row["address"].configure(text=item.get("address", ""))
        row["frame"].configure(bg="#dbeafe" if peer_id == self.selected_peer_id else self.list_frame.cget("bg"))
        for key in ("avatar", "name", "status", "address"):
            row[key].configure(bg=row["frame"].cget("bg"))
        return row

    def show_peers(self):
        self._search_after = None
        search = self.search_box.get().strip().lower()
        visible = set()
        ordered = sorted(self.peers.items(), key=lambda kv: kv[1]["name"].lower())
        for peer_id, item in ordered:
            if search and search not in item["name"].lower():
                continue
            visible.add(peer_id)
            row = self._update_row(peer_id, item)
            row["frame"].pack(fill="x", pady=2)
        for peer_id, row in self.rows.items():
            if peer_id not in visible:
                row["frame"].pack_forget()

    def select_peer(self, peer_id):
        self.selected_peer_id = peer_id
        self.show_peers()
        if self.on_select:
            self.on_select(peer_id)

    def get_selected_peer(self):
        return self.selected_peer_id
