import uuid
from Message_protocol import MessageProtocol


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

    def to_json(self):
        reply_data = {
            "msg_id": self.reply_to,
            "content": self.original_content
        }

        return MessageProtocol.create_json_message(
            sender_name=self.sender,
            content=self.content,
            reply_to=reply_data
        )


# =========================
# Tạo danh sách Message
# =========================

messages = []

print("===== NHẬP MESSAGE =====")

for i in range(3):
    print(f"\nMessage {i + 1}")

    sender = input("Nhập tên người gửi: ").strip()
    content = input("Nhập nội dung tin nhắn: ").strip()

    message_id = str(uuid.uuid4())

    message = Message(
        message_id,
        sender,
        content
    )

    messages.append(message)


# =========================
# Hiển thị danh sách Message
# =========================

print("\n===== DANH SÁCH MESSAGE =====")

for i, message in enumerate(messages, 1):
    print(f"{i}. {message.sender}: {message.content}")


# =========================
# Chọn Message để Reply
# =========================

choice = input("\nChọn Message để Reply: ").strip()

if choice.isdigit():

    index = int(choice) - 1

    if 0 <= index < len(messages):

        original_message = messages[index]

        print("\n===== MESSAGE ĐƯỢC CHỌN =====")
        print("ID:", original_message.message_id)
        print("Người gửi:", original_message.sender)
        print("Nội dung:", original_message.content)


        # =========================
        # Nhập nội dung Reply
        # =========================

        reply_sender = input(
            "\nNhập tên người Reply: "
        ).strip()

        reply_content = input(
            "Nhập nội dung Reply: "
        ).strip()


        # =========================
        # Tạo Reply
        # =========================

        reply_message = Reply(
            original_message,
            reply_sender,
            reply_content
        )


        # =========================
        # Hiển thị Reply
        # =========================

        print("\n===== REPLY =====")
        print("Type:", reply_message.type)
        print("Reply tới:", reply_message.reply_to)
        print("Message gốc:", reply_message.original_content)
        print("Người Reply:", reply_message.sender)
        print("Nội dung Reply:", reply_message.content)


        # =========================
        # Chuyển Reply thành JSON
        # =========================

        json_reply = reply_message.to_json()

        print("\n===== REPLY JSON =====")
        print(json_reply)

    else:
        print("Lựa chọn không hợp lệ.")

else:
    print("Vui lòng nhập số.")