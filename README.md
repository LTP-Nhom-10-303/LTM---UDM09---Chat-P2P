# UDM_09 — Chat P2P

Ứng dụng chat P2P không dùng server trung tâm, toàn bộ thao tác thực hiện bằng GUI.

## Mô tả

- Toàn bộ chức năng của ứng dụng được thực hiện qua GUI.
- Các client giao tiếp trực tiếp theo mô hình P2P, không dùng server trung tâm để chuyển tiếp tin nhắn.
- Hỗ trợ reply một tin nhắn cụ thể và hiển thị nội dung tin nhắn được reply.
- Hỗ trợ forward tin nhắn cho peer hoặc cuộc trò chuyện khác.
- Hiển thị avatar của người dùng trong danh sách peer và khu vực tin nhắn.
- Hỗ trợ chọn, gửi và hiển thị emoji trong nội dung tin nhắn.

## Thành viên nhóm

| Cặp | Thành viên | Phụ trách |
|---|---|---|
| Cặp 1 | Võ Anh Duy, Trương Quang Hòa | Networking & Protocol |
| Cặp 2 | Lê Gia Huy, Nguyễn Đông Nam | GUI chính & Peer list / Avatar |
| Cặp 3 | Trần Thị Đài Trang, Nguyễn Duy Nhất | Reply, Forward, Emoji |

## Kiến trúc

Ứng dụng theo mô hình P2P thuần túy (peer-to-peer), không có server trung tâm đóng vai trò trung chuyển tin nhắn:

- Mỗi client vừa đóng vai trò server (mở một port để lắng nghe kết nối đến từ các peer khác) vừa đóng vai trò client (chủ động kết nối tới peer khác khi cần).
- Kết nối sử dụng TCP socket, đảm bảo dữ liệu truyền đi không bị mất hoặc sai thứ tự.
- Mỗi client có thể duy trì nhiều kết nối P2P cùng lúc với nhiều peer khác nhau, phục vụ cho danh sách peer và chức năng forward.
- Dữ liệu trao đổi giữa các client được định dạng theo JSON, phân tách bằng ký tự xuống dòng (`\n`) để xác định ranh giới từng message qua socket.
- IP và port đều được cấu hình khi chạy ứng dụng, không hard-code cho bất kỳ máy cụ thể nào.

## Định dạng message (Protocol)

Mỗi tin nhắn trao đổi giữa các client có cấu trúc JSON như sau:

```json
{
  "type": "message",
  "id": "uuid-string",
  "sender": "tên người gửi",
  "content": "nội dung tin nhắn",
  "reply_to": "id của message được reply, hoặc null",
  "forwarded_from": "tên người gửi gốc nếu là tin forward, hoặc null",
  "timestamp": "2026-01-01T12:00:00+00:00"
}
```

| Trường | Ý nghĩa |
|---|---|
| `type` | Loại message: `"message"` (chat bình thường) hoặc `"system"` (thông báo hệ thống) |
| `id` | Mã định danh duy nhất của message (UUID) |
| `sender` | Tên/định danh người gửi |
| `content` | Nội dung tin nhắn (hỗ trợ Unicode, bao gồm emoji) |
| `reply_to` | `id` của message gốc nếu đây là tin nhắn reply, ngược lại là `null` |
| `forwarded_from` | Tên người gửi gốc nếu đây là tin forward, ngược lại là `null` |
| `timestamp` | Thời gian gửi, theo chuẩn UTC ISO 8601 |

## Cấu trúc thư mục

```
LTM---UDM09---Chat-P2P/
│
├── Code/            # Toàn bộ mã nguồn ứng dụng
│   ├── GUI/
│   │   ├── __init__.py
│   │   ├── chat_gui.py
│   │   ├── forward.py
│   │   ├── peer_list.py  # Giao diện danh sách peer
│   │   ├── peer_manager.py
│   │   └── reply_emoji.py
│   │
│   ├── assets/
│   │   └── avatars/
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   └── p2p_connection.py  # Xử lý kết nối P2P qua socket
│   │
│   ├── protocol/
│   │   ├── __init__.py
│   │   └── message_protocol.py  # Định dạng và tạo message
│   │
│   ├── .gitignore
│   ├── Reply.py
│   ├── main.py    # Giao diện chính, điểm khởi chạy ứng dụng
│   ├── requirements.txt
│   └── run.bat
│
├── DOCX/  # Báo cáo dự án (Word)
│
├── Extra/ # Ảnh minh chứng demo, log, kết quả kiểm thử, dữ liệu phụ
│
├── PPTX/  # Slide thuyết trình
│
└── README.md
```

## Yêu cầu môi trường

- Python 3.10 trở lên
- Thư viện GUI: Tkinter được sử dụng để xây dựng giao diện người dùng và được tích hợp sẵn trong Python.
- Pillow: dùng để xử lý và hiển thị hình ảnh/avatar.
- Không yêu cầu cài đặt thêm gì khác ngoài Python chuẩn (module `socket`, `threading`, `json`, `uuid`, `datetime` đều có sẵn)

Nếu dùng Tkinter, cài bằng lệnh:
```bash
pip install -r Code/requirements.txt
```
Hoặc cài trực tiếp Pillow:
```bash
pip install Pillow
```

## Cấu hình

Khi khởi chạy ứng dụng, người dùng cần nhập:

- **Tên người dùng**: tên hiển thị trong ứng dụng chat.
- **Port cá nhân**: cổng mà máy mình sẽ lắng nghe kết nối đến từ các peer khác (ví dụ `8000`)
- **IP và port của peer**: địa chỉ IP và cổng của người muốn kết nối tới (ví dụ `192.168.1.5:8001`)

Sau khi ứng dụng khởi động, người dùng có thể thực hiện kết nối với các peer khác thông qua địa chỉ IP và Port của peer.

Các máy cần **cùng chung mạng LAN/Wifi** để có thể kết nối trực tiếp với nhau qua địa chỉ IP nội bộ.

## Cách chạy project

1. Clone repository về máy:
```bash
git clone https://github.com/LTP-Nhom-10-303/LTM---UDM09---Chat-P2P.git
cd LTM---UDM09---Chat-P2P
```
2. Cài thư viện cần thiết:
```bash
pip install -r Code/requirements.txt
```
3. Chạy ứng dụng:
```bash
python Code/main.py
```
4. Khi chương trình khởi động:
- Nhập **tên người dùng**.
- Nhập **port cá nhân**.
- Sau khi vào giao diện chat, nhập **IP** và **port của peer** muốn kết nối.

## Công nghệ sử dụng

- Ngôn ngữ: Python 3.11.x
- GUI: **Tkinter**
- Networking: `socket` (TCP), `threading`
- Định dạng dữ liệu: JSON

## Tiến độ

- [x] Kết nối P2P giữa 2 client
- [x] Định dạng message chung (protocol)
- [x] Giao diện chính (danh sách peer, khung chat)
- [x] Hiển thị avatar
- [x] Chức năng Reply
- [x] Chức năng Forward
- [x] Emoji picker + hiển thị emoji


## Giới hạn

- Ứng dụng hiện chủ yếu được sử dụng trong cùng mạng LAN/Wi-Fi để các client có thể kết nối trực tiếp với nhau.
- Chưa hỗ trợ cơ chế máy chủ trung gian (server) để quản lý và chuyển tiếp kết nối giữa các peer.
- Khi kết nối giữa hai máy khác nhau, người dùng cần biết chính xác địa chỉ IP và port của peer cần kết nối.
- Chưa có cơ chế tự động phát hiện các peer trong mạng.
- Việc kết nối có thể bị ảnh hưởng bởi Firewall hoặc các thiết lập mạng trên máy tính.
- Chưa hỗ trợ đầy đủ kết nối trực tiếp giữa các peer qua Internet khi hai máy nằm ở các mạng khác nhau hoặc phía sau NAT.
- Ứng dụng chưa có cơ chế xác thực và mã hóa đầu cuối (End-to-End Encryption) cho nội dung tin nhắn.
- Khi một peer ngắt kết nối, các peer khác không thể tiếp tục gửi tin nhắn trực tiếp đến peer đó cho đến khi kết nối lại.

## Video demo

*(link video)*
