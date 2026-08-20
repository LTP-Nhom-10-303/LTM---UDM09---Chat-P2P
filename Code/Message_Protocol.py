import socket
import threading
import tkinter as tk
import json
import uuid
from datetime import datetime
from tkinter import scrolledtext, simpledialog, messagebox

# LỚP MESSAGE PROTOCOL 
class MessageProtocol:
    @staticmethod
    def create_json_message(sender_name: str, content: str, reply_to: dict = None, is_forwarded: bool = False) -> str:
        """
        [ĐÓNG GÓI] Chuyển thông tin tin nhắn thành chuỗi JSON hỗ trợ UTF-8, Emoji, Reply, Forward
        """
        msg_dict = {
            "type": "CHAT",
            "msg_id": f"msg_{uuid.uuid4().hex[:6]}",
            "sender_name": sender_name,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "content": content,
            "reply_to": reply_to,           # Ví dụ: {"msg_id": "...", "content": "..."}
            "is_forwarded": is_forwarded,
            "avatar_base64": ""             # Dành cho tính năng Avatar
        }
        return json.dumps(msg_dict, ensure_ascii=False)

    @staticmethod
    def parse_json_message(raw_str: str) -> dict:
        """
        [GIẢI MÃ] Chuyển chuỗi JSON nhận từ Socket thành Python Dict
        """
        try:
            return json.loads(raw_str)
        except Exception:
            return None

# LỚP GIAO DIỆN & KẾT NỐI P2P 
class P2PChatGUI:
    def __init__(self, root):
        self.root = root
        self.sock = None          # socket đang dùng để gửi/nhận
        self.server_sock = None   # socket lắng nghe (khi đóng vai server)
        self.my_name = "Trương Quang Hòa" # Tên người gửi

        root.title("Chat P2P - UDM_09")
        root.geometry("420x520")

        #  Nút kết nối / ngắt kết nối 
        top = tk.Frame(root, pady=10)
        top.pack(fill=tk.X)

        self.connect_btn = tk.Button(top, text="Kết nối", width=14, command=self.on_connect)
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        self.disconnect_btn = tk.Button(top, text="Ngắt kết nối", width=14,
                                         command=self.on_disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT)

        self.status = tk.Label(root, text="Chưa kết nối", fg="red")
        self.status.pack()

        #  Khung hiển thị tin nhắn 
        self.chat_area = scrolledtext.ScrolledText(root, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        #  Ô nhập tin nhắn + nút Gửi 
        bottom = tk.Frame(root, pady=10)
        bottom.pack(fill=tk.X, padx=10)

        self.msg_entry = tk.Entry(bottom, state=tk.DISABLED)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.msg_entry.bind("<Return>", lambda e: self.on_send())

        self.send_btn = tk.Button(bottom, text="Gửi", width=8, command=self.on_send, state=tk.DISABLED)
        self.send_btn.pack(side=tk.LEFT, padx=(5, 0))

    #  Tiện ích hiển thị tin nhắn chuẩn định dạng Protocol 
    def _print_message(self, sender_name, text, timestamp=None):
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"[{timestamp}] {sender_name}: {text}\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _set_connected(self, connected):
        state = tk.NORMAL if connected else tk.DISABLED
        self.msg_entry.config(state=state)
        self.send_btn.config(state=state)
        self.disconnect_btn.config(state=state)
        self.connect_btn.config(state=tk.DISABLED if connected else tk.NORMAL)
        self.status.config(text="Đã kết nối" if connected else "Chưa kết nối",
                            fg="green" if connected else "red")

    #  Thao tác kết nối 
    def on_connect(self):
        ip = simpledialog.askstring("Kết nối", "Nhập IP peer:", initialvalue="127.0.0.1")
        if not ip:
            return
        port = simpledialog.askinteger("Kết nối", "Nhập port:", initialvalue=5000)
        if not port:
            return
        self.connect_btn.config(state=tk.DISABLED)
        threading.Thread(target=self._connect_thread, args=(ip, port), daemon=True).start()

    def _connect_thread(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((ip, port))
            s.settimeout(None)
            self.sock = s
        except OSError:
            try:
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_sock.bind(("0.0.0.0", port))
                self.server_sock.listen(1)
                self.root.after(0, self._print_message, "Hệ thống", f"Đang chờ peer kết nối tới cổng {port} ...")
                self.sock, _ = self.server_sock.accept()
            except OSError as e:
                self.root.after(0, messagebox.showerror, "Lỗi kết nối", str(e))
                self.root.after(0, lambda: self.connect_btn.config(state=tk.NORMAL))
                return

        self.root.after(0, self._print_message, "Hệ thống", "Đã kết nối với peer.")
        self.root.after(0, self._set_connected, True)
        threading.Thread(target=self._receive_loop, daemon=True).start()

    #  Nhận tin nhắn: Giải mã JSON từ Socket
    def _receive_loop(self):
        while self.sock:
            try:
                data = self.sock.recv(4096)
            except OSError:
                break
            if not data:
                break
            
            # GIẢI MÃ PROTOCOL JSON TẠI ĐÂY
            raw_str = data.decode('utf-8', errors='replace')
            msg_obj = MessageProtocol.parse_json_message(raw_str)

            if msg_obj:
                sender = msg_obj.get("sender_name", "Peer")
                content = msg_obj.get("content", "")
                time_str = msg_obj.get("timestamp")
                self.root.after(0, self._print_message, sender, content, time_str)
            else:
                # Trường hợp nhận dữ liệu thô cũ không qua JSON
                self.root.after(0, self._print_message, "Peer", raw_str)

        if self.sock:
            self.root.after(0, self._print_message, "Hệ thống", "Peer đã ngắt kết nối.")
            self.root.after(0, self.on_disconnect)

    def on_disconnect(self):
        for s in (self.sock, self.server_sock):
            if s:
                try:
                    s.close()
                except OSError:
                    pass
        self.sock = None
        self.server_sock = None
        self._print_message("Hệ thống", "Đã ngắt kết nối.")
        self._set_connected(False)

    # Gửi tin nhắn: Đóng gói JSON trước khi gửi qua Socket 
    def on_send(self):
        text = self.msg_entry.get().strip()
        if not text or not self.sock:
            return
        try:
            # ĐÓNG GÓI JSON PROTOCOL TẠI ĐÂY
            json_payload = MessageProtocol.create_json_message(
                sender_name=self.my_name,
                content=text
            )
            
            # Gửi chuỗi JSON qua Socket
            self.sock.sendall(json_payload.encode("utf-8"))
            
            # Hiển thị tin nhắn lên khung chat của mình
            self._print_message("Bạn", text)
            self.msg_entry.delete(0, tk.END)
        except OSError as e:
            messagebox.showerror("Lỗi gửi tin nhắn", str(e))
            self.on_disconnect()


if __name__ == "__main__":
    root = tk.Tk()
    P2PChatGUI(root)
    root.mainloop()
