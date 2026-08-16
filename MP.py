import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import json
import uuid

# 1. TẦNG GIAO THỨC JSON (MESSAGE PROTOCOL)
class MessageProtocol:
    @staticmethod
    def create_json_message(sender_name: str, content: str, reply_to: dict = None) -> str:
        """
        [ĐÓNG GÓI JSON] Chuyển thông tin tin nhắn thành chuỗi JSON để gửi đi
        """
        msg_dict = {
            "type": "CHAT",
            "msg_id": f"msg_{uuid.uuid4().hex[:6]}",
            "sender_name": sender_name,
            "timestamp": datetime.now().strftime("%H:%M"),
            "content": content,             # Hỗ trợ UTF-8 / Emoji
            "reply_to": reply_to,           # Thông tin tin nhắn được reply (nếu có)
            "is_forwarded": False
        }
        # json.dumps chuyển Dict -> Chuỗi JSON (ensure_ascii=False để giữ nguyên Emoji / Tiếng Việt)
        return json.dumps(msg_dict, ensure_ascii=False)

    @staticmethod
    def parse_json_message(json_str: str) -> dict:
        """
        [GIẢI MÃ JSON] Chuyển chuỗi JSON nhận từ Socket thành Python Dict
        """
        try:
            # json.loads chuyển Chuỗi JSON -> Dict
            return json.loads(json_str)
        except Exception as e:
            print("[Lỗi Decode JSON]:", e)
            return None

# 2. TẦNG GIAO DIỆN CHAT (GUI)
class ChatWindowGUI:
    def __init__(self, root, my_name="Trương Quang Hòa", send_callback=None):
        self.root = root
        self.my_name = my_name
        self.send_callback = send_callback  # Hàm gửi chuỗi JSON sang Socket của Võ Anh Duy

        self.root.title(f"UDM_09 - Chat P2P ({self.my_name})")
        self.root.geometry("480x580")

        # [Nhiệm vụ 1 & 2]: Cửa sổ Chat chính + Khu vực hiển thị tin nhắn
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Config màu sắc hiển thị [Nhiệm vụ 5]
        self.chat_display.tag_config('SENT', foreground='blue', justify='right')
        self.chat_display.tag_config('RECEIVED', foreground='green', justify='left')

        # Khung nhập liệu
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        # [Nhiệm vụ 3]: Ô nhập Message
        self.msg_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # [Nhiệm vụ 7]: Sự kiện ấn Enter
        self.msg_entry.bind("<Return>", lambda event: self.on_send_click())

        # [Nhiệm vụ 4]: Nút Send
        self.send_button = tk.Button(input_frame, text="Send", width=8, bg="#0084ff", fg="white", command=self.on_send_click)
        self.send_button.pack(side=tk.RIGHT)

    # [Nhiệm vụ 7]: Xử lý sự kiện bấm Send
    def on_send_click(self):
        text_content = self.msg_entry.get().strip()
        if text_content:
            # Step 1: Đóng gói thành chuỗi JSON
            json_packet = MessageProtocol.create_json_message(
                sender_name=self.my_name,
                content=text_content
            )
            
            # Step 2: Hiển thị lên GUI của chính mình
            self.display_incoming_json(json_packet, is_me=True)
            self.msg_entry.delete(0, tk.END)

            # Step 3 [Nhiệm vụ 8]: Gửi chuỗi JSON cho Võ Anh Duy đẩy qua Socket P2P
            if self.send_callback:
                self.send_callback(json_packet)

    # [Nhiệm vụ 5 & 6]: Hiển thị tin nhắn & Thời gian từ chuỗi JSON
    def display_incoming_json(self, json_str: str, is_me: bool = False):
        # Giải mã gói tin JSON
        data = MessageProtocol.parse_json_message(json_str)
        if not data:
            return

        sender = "Bạn" if is_me else data["sender_name"]
        time_str = data["timestamp"]  # Thời gian lấy từ JSON
        content = data["content"]      # Nội dung (chứa chữ / emoji)

        self.chat_display.config(state='normal')
        tag = 'SENT' if is_me else 'RECEIVED'
        
        # Format dòng hiển thị
        formatted_msg = f"[{time_str}] {sender}:\n{content}\n\n"
        
        self.chat_display.insert(tk.END, formatted_msg, tag)
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)

# DEMO CHẠY THỬ
if __name__ == "__main__":
    def dummy_socket_send(json_data_string):
        print("\n--- [DỮ LIỆU ĐƯỢC GỬI SANG SOCKET ANH DUY] ---")
        print(json_data_string)
        print("--------------------------------------------\n")

    root = tk.Tk()
    app = ChatWindowGUI(root, my_name="Trương Quang Hòa", send_callback=dummy_socket_send)

    # Giả lập khi Võ Anh Duy (Socket) nhận được 1 chuỗi JSON từ Peer khác gửi tới:
    sample_incoming_json = '{"type": "CHAT", "sender_name": "Võ Anh Duy", "timestamp": "22:16", "content": "Chào Hòa, tớ nhận được JSON rồi! 👍"}'
    app.display_incoming_json(sample_incoming_json, is_me=False)

    root.mainloop()
