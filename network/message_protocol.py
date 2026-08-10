"""
message_protocol.py
Định dạng chuẩn cho 1 tin nhắn trao đổi giữa 2 client.
Các trường reply_to / forwarded_from để sẵn cho phần Reply & Forward (Cặp 3).
"""

import uuid
from datetime import datetime, timezone


def new_message(sender, content, msg_type="message", reply_to=None, forwarded_from=None):
    """
    sender: tên người gửi
    content: nội dung tin nhắn (có thể chứa emoji dạng unicode luôn)
    msg_type: "message" (chat bình thường) | "system" (thông báo hệ thống)
    reply_to: id của message được reply, hoặc None
    forwarded_from: tên người gửi gốc nếu đây là tin forward, hoặc None
    """
    return {
        "type": msg_type,
        "id": str(uuid.uuid4()),
        "sender": sender,
        "content": content,
        "reply_to": reply_to,
        "forwarded_from": forwarded_from,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
