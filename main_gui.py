import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading

# Import class P2PConnection từ file p2p_connection.py ở trên
from p2p_connection import P2PConnection


class P2PChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Chat P2P (Python Tkinter)")
        self.root.geometry("520x580")

        self.p2p = None

        # --- 1. Cấu hình Port ---
        frame_top = tk.LabelFrame(root, text=" 1. Cấu hình Port cá nhân ", padx=10, pady=5)
        frame_top.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_top, text="Port của bạn:").pack(side="left")
        self.ent_my_port = tk.Entry(frame_top, width=10)
        self.ent_my_port.insert(0, "8000")
        self.ent_my_port.pack(side="left", padx=5)

        self.btn_listen = tk.Button(frame_top, text="Mở Lắng Nghe", command=self.start_listen, bg="#4CAF50", fg="white")
        self.btn_listen.pack(side="left", padx=5)

        # --- 2. Kết nối tới Peer ---
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

        # --- 3. Cửa sổ hiển thị tin nhắn ---
        frame_chat = tk.Frame(root)
        frame_chat.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_chat = scrolledtext.ScrolledText(frame_chat, state="disabled", wrap="word")
        self.txt_chat.pack(fill="both", expand=True)

        # --- 4. Soạn tin nhắn ---
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
