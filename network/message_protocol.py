import sys
import json
import socket
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Signal, QObject, Qt

# 1. MESSAGE PROTOCOL LAYER
class MessageProtocol:
    @staticmethod
    def create_chat_message(sender_name, avatar, content, reply_to=None):
        """Tạo gói tin chuẩn JSON theo thiết kế giao thức Message Protocol"""
        return {
            "type": "CHAT_MSG",
            "msg_id": f"msg_{int(datetime.now().timestamp() * 1000)}",
            "sender_name": sender_name,
            "sender_avatar": avatar,
            "content": content,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "reply_to": reply_to
        }

    @staticmethod
    def serialize(msg_dict):
        """Đóng gói dữ liệu Dict -> JSON string -> bytes"""
        return (json.dumps(msg_dict) + "\n").encode('utf-8')

    @staticmethod
    def deserialize(data_str):
        """Giải mã dữ liệu bytes/string -> Dict"""
        try:
            return json.loads(data_str)
        except Exception:
            return None

# 2. NETWORK LAYER & SIGNAL HANDLER
class NetworkSignals(QObject):
    # Định nghĩa các Signal giao tiếp giữa Thread Mạng và Thread GUI trong PySide6
    message_received = Signal(dict)
    connection_status = Signal(str)

class PeerServerThread(threading.Thread):
    def __init__(self, host, port, signals):
        super().__init__()
        self.host = host
        self.port = port
        self.signals = signals
        self.daemon = True
        self.running = True

    def run(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            self.signals.connection_status.emit(f"Server P2P đang lắng nghe tại {self.host}:{self.port}")

            while self.running:
                client, addr = server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client, addr), daemon=True).start()
        except Exception as e:
            self.signals.connection_status.emit(f"Lỗi Socket Server: {e}")

    def handle_client(self, client, addr):
        buffer = ""
        while self.running:
            try:
                data = client.recv(1024).decode('utf-8')
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg_dict = MessageProtocol.deserialize(line)
                    if msg_dict:
                        self.signals.message_received.emit(msg_dict)
            except Exception:
                break
        client.close()

# 3. MAIN GUI WINDOW (PYSIDE6)
class ChatMainWindow(QMainWindow):
    def __init__(self, user_name="Trương Quang Hòa", avatar="😎", port=9000, target_port=9001):
        super().__init__()
        self.user_name = user_name
        self.avatar = avatar
        self.port = port
        self.target_port = target_port
        self.replying_msg = None

        self.init_ui()
        self.init_network()

    def init_ui(self):
        # 1. Thiết kế cửa sổ Chat chính
        self.setWindowTitle(f"P2P Chat - {self.user_name} (Port: {self.port})")
        self.resize(500, 600)

        main_widget = QWidget()
        layout = QVBoxLayout()

        # Hiển thị trạng thái kết nối
        self.lbl_status = QLabel("Trạng thái: Đang kết nối...")
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_status)

        # 2. Khu vực hiển thị tin nhắn (QListWidget)
        self.msg_list = QListWidget()
        layout.addWidget(self.msg_list)

        # Xem trước tin nhắn Reply
        self.lbl_reply_preview = QLabel("")
        self.lbl_reply_preview.setStyleSheet("background-color: #f0f0f0; border-left: 3px solid #007bff; padding: 4px;")
        self.lbl_reply_preview.hide()
        layout.addWidget(self.lbl_reply_preview)

        # 3. Ô nhập Message & 4. Nút Send
        input_layout = QHBoxLayout()
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Nhập nội dung tin nhắn...")
        self.txt_input.returnPressed.connect(self.send_message)  # Gửi khi nhấn Enter

        self.btn_send = QPushButton("Gửi")
        self.btn_send.clicked.connect(self.send_message)  # 7. Xử lý sự kiện gửi Message

        input_layout.addWidget(self.txt_input)
        input_layout.addWidget(self.btn_send)
        layout.addLayout(input_layout)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def init_network(self):
        """8. Kết nối GUI với Protocol/Network Layer"""
        self.signals = NetworkSignals()
        self.signals.message_received.connect(self.on_message_received)
        self.signals.connection_status.connect(self.lbl_status.setText)

        # Chạy Server lắng nghe trên Thread riêng
        self.server_thread = PeerServerThread("127.0.0.1", self.port, self.signals)
        self.server_thread.start()

    def send_message(self):
        content = self.txt_input.text().strip()
        if not content:
            return

        # Tạo gói tin qua MessageProtocol
        msg_dict = MessageProtocol.create_chat_message(
            sender_name=self.user_name,
            avatar=self.avatar,
            content=content,
            reply_to=self.replying_msg
        )

        # 5. Hiển thị tin nhắn gửi lên GUI
        self.display_message(msg_dict, is_mine=True)

        # Gửi dữ liệu qua Socket
        threading.Thread(target=self._socket_send, args=(msg_dict,), daemon=True).start()

        # Reset ô nhập
        self.txt_input.clear()
        self.clear_reply()

    def _socket_send(self, msg_dict):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(("127.0.0.1", self.target_port))
            client.sendall(MessageProtocol.serialize(msg_dict))
            client.close()
        except Exception:
            self.signals.connection_status.emit(f"Không thể kết nối tới Peer port {self.target_port}")

    def on_message_received(self, msg_dict):
        """5. Hiển thị tin nhắn nhận được"""
        self.display_message(msg_dict, is_mine=False)

    def display_message(self, msg_dict, is_mine=False):
        """Hiển thị message kèm Avatar và Timestamp (6)"""
        sender = msg_dict.get("sender_name")
        avatar = msg_dict.get("sender_avatar", "👤")
        content = msg_dict.get("content")
        timestamp = msg_dict.get("timestamp")
        reply_to = msg_dict.get("reply_to")

        text = f"{avatar} <b>{sender}</b> [{timestamp}]:<br>{content}"
        
        if reply_to:
            text = f"<i style='color:gray;'>↩ Trả lời [{reply_to.get('sender_name')}]: \"{reply_to.get('content')}\"</i><br>" + text

        item = QListWidgetItem()
        item_widget = QLabel(text)
        item_widget.setTextFormat(Qt.TextFormat.RichText)
        
        # Căn lề tin nhắn: Phải (Tin gửi đi), Trái (Tin nhận)
        if is_mine:
            item_widget.setStyleSheet("background-color: #dcf8c6; padding: 8px; border-radius: 8px; margin: 4px;")
            item_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            item_widget.setStyleSheet("background-color: #ffffff; padding: 8px; border-radius: 8px; margin: 4px;")
            item_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.msg_list.addItem(item)
        self.msg_list.setItemWidget(item, item_widget)
        self.msg_list.scrollToBottom()

    def clear_reply(self):
        self.replying_msg = None
        self.lbl_reply_preview.hide()

# 4. KHỞI CHẠY ỨNG DỤNG
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Khởi tạo giao diện chính
    window = ChatMainWindow(user_name="Trương Quang Hòa", avatar="👨‍💻", port=9000, target_port=9001)
    window.show()

    sys.exit(app.exec())
