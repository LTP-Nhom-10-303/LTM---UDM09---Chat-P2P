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

Ứng dụng theo mô hình **P2P thuần túy (peer-to-peer)**, không có server trung tâm đóng vai trò trung chuyển tin nhắn:

- Mỗi client vừa đóng vai trò **server** (mở một port để lắng nghe kết nối đến từ các peer khác) vừa đóng vai trò **client** (chủ động kết nối tới peer khác khi cần).
- Kết nối sử dụng **TCP socket**, đảm bảo dữ liệu truyền đi không bị mất hoặc sai thứ tự.
- Mỗi client có thể duy trì **nhiều kết nối P2P cùng lúc** với nhiều peer khác nhau, phục vụ cho danh sách peer và chức năng forward.
- Dữ liệu trao đổi giữa các peer được định dạng theo **JSON**, phân tách bằng ký tự xuống dòng (`\n`) để xác định ranh giới từng message qua socket.
- IP và port đều được **cấu hình khi chạy ứng dụng**, không hard-code cho bất kỳ máy cụ thể nào.

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
| `forwarded_from` | Tên người gửi gốc nếu đây là tin nhắn forward, ngược lại là `null` |
| `timestamp` | Thời gian gửi, theo chuẩn UTC ISO 8601 |

## Cấu trúc thư mục

```
LTM---UDM09---Chat-P2P/
├── Code/               # Toàn bộ mã nguồn ứng dụng
│   ├── network/
│   │   ├── __init__.py
│   │   ├── message_protocol.py   # Định dạng và tạo message
│   │   └── p2p_connection.py     # Xử lý kết nối P2P qua socket
│   ├── peer_list.py    # Giao diện danh sách peer
│   └── main_gui.py     # Giao diện chính, điểm khởi chạy ứng dụng
├── DOCX/               # Báo cáo dự án (Word)
├── PPTX/               # Slide thuyết trình
├── Extra/              # Ảnh minh chứng demo, log, kết quả kiểm thử, dữ liệu phụ
├── README.md
└── .gitignore
```

## Yêu cầu môi trường

- Python 3.10 trở lên
- Thư viện GUI: Tkinter
- Không yêu cầu cài đặt thêm gì khác ngoài Python chuẩn (module `socket`, `threading`, `json`, `uuid`, `datetime` đều có sẵn)

## Cài đặt

```bash
git clone https://github.com/LTP-Nhom-10-303/LTM---UDM09---Chat-P2P.git
cd LTM---UDM09---Chat-P2P

```

## Cấu hình

Khi khởi động ứng dụng, người dùng cần nhập:

- **Port cá nhân**: port mà máy hiện tại sẽ lắng nghe kết nối đến (ví dụ `8000`)
- **IP và port của peer** muốn kết nối tới (ví dụ `127.0.0.1` và `8001`)

Không có giá trị nào bị hard-code sẵn trong code — mọi thông số mạng đều nhập được qua giao diện.

## Cách chạy project

```bash
cd Code
python main_gui.py
```

Để test giữa 2 client trên cùng máy: mở 2 cửa sổ terminal, chạy lệnh trên ở mỗi cửa sổ, đặt port khác nhau cho mỗi bên (ví dụ `8000` và `8001`), sau đó nhập IP `127.0.0.1` và port của bên kia để kết nối.

Để test giữa 2 máy khác nhau trong cùng mạng LAN: dùng IP LAN thật của từng máy (xem bằng lệnh `ipconfig` trên Windows hoặc `ifconfig`/`ip a` trên Linux/Mac) thay cho `127.0.0.1`.

## Công nghệ sử dụng

- Ngôn ngữ: Python 3.x
- GUI: Tkinter
- Networking: `socket` (TCP), `threading`
- Định dạng dữ liệu: JSON

## Kiểm thử

Các kịch bản kiểm thử được thực hiện, kết quả lưu tại thư mục `Extra/`:

- Test chức năng: kết nối, gửi/nhận tin nhắn, reply, forward, emoji, hiển thị avatar
- Test dữ liệu không hợp lệ: gửi message sai định dạng, thiếu trường bắt buộc
- Test mất kết nối đột ngột: tắt một client giữa phiên chat
- Stress test / performance test: so sánh hiệu năng ở ít nhất 2 mức tải khác nhau (số lượng peer / tần suất gửi tin nhắn)

## Giới hạn của sản phẩm

- Ứng dụng hoạt động trong phạm vi **mạng LAN** (các máy biết IP của nhau), chưa hỗ trợ kết nối P2P qua Internet (chưa xử lý NAT traversal).
- *(Cập nhật thêm các giới hạn khác khi phát hiện trong quá trình phát triển/kiểm thử)*

## Video demo

*(Dán link YouTube/Google Drive — chế độ Public hoặc Unlisted — sau khi quay xong)*

## Tiến độ

- [x] Kết nối P2P giữa 2 client
- [x] Định dạng message chung (protocol)
- [ ] Giao diện chính (danh sách peer, khung chat)
- [ ] Hiển thị avatar
- [x] Chức năng Reply
- [x] Chức năng Forward
- [ ] Emoji picker + hiển thị emoji
