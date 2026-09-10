
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os


class PeerList(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)

        search_frame = tk.Frame(self)
        search_frame.pack(fill="x", padx=5, pady=5)

        search_icon = tk.Label(
            search_frame,
            text="🔍",
            font=("Arial", 13)
        )
        search_icon.pack(side="left", padx=(5, 3))

        self.search_box = tk.Entry(search_frame)
        self.search_box.pack(side="left", fill="x", expand=True)
        self.search_box.bind("<KeyRelease>", self.search_peer)

        self.list_frame = tk.Frame(self)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.peers = []
        self.selected_peer = None
        self.default_avatar = self.create_default_avatar()
        self.avatar_images = {}

    def create_default_avatar(self):
        image = Image.new("RGB", (50, 50), "lightgray")
        return ImageTk.PhotoImage(image)

    def add_peer(self, peer, avatar_path=None):
        for item in self.peers:
            if item["name"] == peer:
                return

        self.peers.append({
            "name": peer,
            "online": True,
            "avatar": avatar_path
        })

        self.show_peers()

    def update_peer_status(self, peer, online):
        for item in self.peers:
            if item["name"] == peer:
                item["online"] = online
                break

        self.show_peers()

    def choose_avatar(self, peer):
        file_path = filedialog.askopenfilename(
            title="Chọn avatar",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif"),
                ("PNG files", "*.png"),
                ("JPG files", "*.jpg *.jpeg"),
                ("GIF files", "*.gif"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        for item in self.peers:
            if item["name"] == peer:
                item["avatar"] = file_path
                break

        if peer in self.avatar_images:
            del self.avatar_images[peer]

        self.show_peers()

    def get_avatar(self, peer):
        if peer in self.avatar_images:
            return self.avatar_images[peer]

        avatar_path = None

        for item in self.peers:
            if item["name"] == peer:
                avatar_path = item["avatar"]
                break

        if not avatar_path:
            return self.default_avatar

        if not os.path.exists(avatar_path):
            return self.default_avatar

        try:
            image = Image.open(avatar_path)
            image = image.resize((50, 50), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.avatar_images[peer] = photo
            return photo
        except Exception:
            return self.default_avatar

    def search_peer(self, event=None):
        self.show_peers()

    def show_peers(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        search_text = self.search_box.get().strip().lower()

        for item in self.peers:
            name = item["name"]

            if search_text and not name.lower().startswith(search_text):
                continue

            peer_frame = tk.Frame(
                self.list_frame,
                bd=1,
                relief="solid",
                padx=5,
                pady=5,
                cursor="hand2"
            )
            peer_frame.pack(fill="x", pady=2)

            avatar = self.get_avatar(name)

            avatar_label = tk.Label(
                peer_frame,
                image=avatar
            )
            avatar_label.pack(side="left")

            name_label = tk.Label(
                peer_frame,
                text=name,
                font=("Arial", 11, "bold")
            )
            name_label.pack(side="left", padx=10)

            if item["online"]:
                status_text = "● Online"
                status_color = "green"
            else:
                status_text = "● Offline"
                status_color = "gray"

            status_label = tk.Label(
                peer_frame,
                text=status_text,
                fg=status_color,
                font=("Arial", 10)
            )
            status_label.pack(side="left", padx=10)

            avatar_button = tk.Button(
                peer_frame,
                text="Đổi avatar",
                command=lambda p=name: self.choose_avatar(p)
            )
            avatar_button.pack(side="right", padx=5)

            widgets = [
                peer_frame,
                avatar_label,
                name_label,
                status_label
            ]

            for widget in widgets:
                widget.bind(
                    "<Button-1>",
                    lambda event, p=name: self.select_peer(p)
                )

    def select_peer(self, peer):
        self.selected_peer = peer

    def get_selected_peer(self):
        return self.selected_peer

