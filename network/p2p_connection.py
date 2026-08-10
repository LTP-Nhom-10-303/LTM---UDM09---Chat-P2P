"""
test_p2p_cli.py
Demo P2P bằng dòng lệnh (chưa cần GUI của Cặp 2).
Chạy file này ở 2 máy (hoặc 2 terminal trong cùng máy để test nhanh).
 
Cách test trên cùng 1 máy:
  Terminal 1: python test_p2p_cli.py  -> nhập port 5001, chọn "n" (không chủ động connect)
  Terminal 2: python test_p2p_cli.py  -> nhập port 5002, chọn "y", connect tới 127.0.0.1:5001
"""
 
import sys
from network.p2p_connection import P2PConnection
from network.message_protocol import new_message
 
 
def main():
    my_name = input("Tên của bạn: ").strip()
    my_port = int(input("Port để lắng nghe (VD: 5001): ").strip())
 
    def on_message(msg):
        print(f"\n[{msg['sender']}] {msg['content']}")
 
    def on_status(text):
        print(f"\n>> {text}")
 
    conn = P2PConnection(my_port, on_message=on_message, on_status=on_status)
    conn.start_listening()
 
    choice = input("Bạn muốn chủ động kết nối tới peer? (y/n): ").strip().lower()
    if choice == "y":
        ip = input("IP của peer (LAN, VD 192.168.1.5): ").strip()
        port = int(input("Port của peer: ").strip())
        conn.connect_to_peer(ip, port)
 
    print("Gõ tin nhắn rồi Enter để gửi. Ctrl+C để thoát.\n")
    try:
        while True:
            text = input()
            if not text:
                continue
            msg = new_message(my_name, text)
            conn.send(msg)
    except KeyboardInterrupt:
        conn.close()
        sys.exit(0)
 
 
if __name__ == "__main__":
    main()
 
