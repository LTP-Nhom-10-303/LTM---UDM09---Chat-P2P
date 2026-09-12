import json
import uuid
from datetime import datetime


class MessageProtocol:

    @staticmethod
    def create_json_message(
        sender_name,
        content,
        reply_to=None,
        is_forwarded=False
    ):
        message = {
            "type": "CHAT",
            "msg_id": f"msg_{uuid.uuid4().hex[:6]}",
            "sender_name": sender_name,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "content": content,
            "reply_to": reply_to,
            "is_forwarded": is_forwarded,
            "avatar_base64": ""
        }

        return json.dumps(message, ensure_ascii=False)

    @staticmethod
    def parse_json_message(raw_str):
        try:
            return json.loads(raw_str)
        except json.JSONDecodeError:
            return None