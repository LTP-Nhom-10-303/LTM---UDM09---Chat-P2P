import uuid


class Message:
    def __init__(self, message_id, sender, content):
        self.message_id = message_id
        self.sender = sender
        self.content = content


class Reply:
    def __init__(self, original_message, sender, content):
        self.type = "REPLY"
        self.sender = sender
        self.content = content
        self.reply_to = original_message.message_id
        self.original_content = original_message.content


# =========================
# Người dùng nhập Message
# =========================

sender = input("Nhập tên người gửi: ").strip()
content = input("Nhập nội dung tin nhắn: ").strip()

# Hệ thống tự tạo Message ID
message_id = str(uuid.uuid4())

# Tạo Message gốc
original_message = Message(
    message_id,
    sender,
    content
)

print("\n===== MESSAGE GỐC =====")
print("ID:", original_message.message_id)
print("Người gửi:", original_message.sender)
print("Nội dung:", original_message.content)


# =========================
# Người dùng nhập Reply
# =========================

reply_sender = input("\nNhập tên người Reply: ").strip()
reply_content = input("Nhập nội dung Reply: ").strip()

# Tạo Reply
reply_message = Reply(
    original_message,
    reply_sender,
    reply_content
)

print("\n===== REPLY =====")
print("Type:", reply_message.type)
print("Reply tới:", reply_message.reply_to)
print("Người Reply:", reply_message.sender)
print("Nội dung Reply:", reply_message.content)