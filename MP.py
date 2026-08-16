import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

class ChatWindowGUI:
    def __init__(self, root, send_callback=None):
        self.root = root
        self.root.title("UDM_09 - Peer Chat")
        self.root.geometry("450x550")
        self.send_callback = send_callback  # Hàm kết nối với Message Protocol/Network

        # 1. Thiết kế cửa sổ Chat chính & 2. Khu vực hiển thị tin nhắn
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', font=("Arial", 10))
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Cấu hình Tag hiển thị tin nhắn gửi/nhận (Nhiệm vụ 5)
        self.chat_display.tag_config('SENT', foreground='blue', justify='right')
        self.chat_display.tag_config('RECEIVED', foreground='green', justify='left')

        # Khung chứa ô nhập và nút bấm
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        # 3. Ô nhập Message
        self.msg_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 7. Xử lý sự kiện nhấn phím Enter để gửi
        self.msg_entry.bind("<Return>", lambda event: self.on_send_click())

        # 4. Nút Send
        self.send_button = tk.Button(input_frame, text="Send", width=8, bg="#0084ff", fg="white", command=self.on_send_click)
        self.send_button.pack(side=tk.RIGHT)

    # 7. Xử lý sự kiện gửi Message
    def on_send_click(self):
        content = self.msg_entry.get().strip()
        if content:
            # Displays message locally
            self.display_message("Bạn", content, is_sent=True)
            self.msg_entry.delete(0, tk.END)
            
            # 8. Kết nối GUI với Networking / Protocol Layer
            if self.send_callback:
                self.send_callback(content)

    # 5. Hiển thị tin nhắn gửi/nhận & 6. Hiển thị thời gian
    def display_message(self, sender_name: str, text: str, is_sent: bool = False):
        self.chat_display.config(state='normal')
        
        # 6. Hiển thị thời gian (Format HH:MM)
        current_time = datetime.now().strftime("%H:%M")
        
        tag = 'SENT' if is_sent else 'RECEIVED'
        formatted_msg = f"[{current_time}] {sender_name}:\n{text}\n\n"
        
        self.chat_display.insert(tk.END, formatted_msg, tag)
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END) # Tự động cuộn xuống tin nhắn mới nhất

# --- DEMO CHẠY THỬ GUI ---
if __name__ == "__main__":
    def dummy_network_send(message):
        print(f"[GUI Event] Đã chuyển tin nhắn sang Socket: {message}")

    root = tk.Tk()
    app = ChatWindowGUI(root, send_callback=dummy_network_send)
    
    # Giả lập nhận 1 tin nhắn từ Peer khác
    app.display_message("Peer_02", "Chào Hòa, tớ kết nối thành công rồi!", is_sent=False)
    
    root.mainloop()
