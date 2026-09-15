"""Message protocol for UDM_09 P2P Chat.

All network messages are JSON objects terminated by a newline (\\n).
This gives the TCP stream a simple message boundary (framing) and keeps
UTF-8/emoji intact.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class MessageProtocol:
    PROTOCOL_VERSION = 1

    @staticmethod
    def new_id(prefix: str = "msg") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def now() -> str:
        return datetime.now().strftime("%H:%M:%S")

    @staticmethod
    def _base(
        msg_type: str,
        sender_id: str,
        sender_name: str,
        content: str = "",
        avatar_base64: str = "",
    ) -> Dict[str, Any]:
        return {
            "version": MessageProtocol.PROTOCOL_VERSION,
            "type": msg_type,
            "msg_id": MessageProtocol.new_id(),
            "sender_id": sender_id,
            "sender_name": sender_name,
            "timestamp": MessageProtocol.now(),
            "content": content,
            "avatar_base64": avatar_base64,
        }

    @staticmethod
    def create_hello(
        sender_id: str,
        sender_name: str,
        port: int,
        avatar_base64: str = "",
    ) -> str:
        message = MessageProtocol._base(
            "HELLO", sender_id, sender_name, avatar_base64=avatar_base64
        )
        message.update({"port": port})
        return MessageProtocol.encode(message)

    @staticmethod
    def create_chat_message(
        sender_id: str,
        sender_name: str,
        content: str,
        reply_to: Optional[Dict[str, Any]] = None,
        avatar_base64: str = "",
    ) -> str:
        message = MessageProtocol._base(
            "CHAT", sender_id, sender_name, content, avatar_base64
        )
        message.update({"reply_to": reply_to, "is_forwarded": False})
        return MessageProtocol.encode(message)

    @staticmethod
    def create_forward_message(
        sender_id: str,
        sender_name: str,
        content: str,
        original_sender: str,
        original_msg_id: str,
        avatar_base64: str = "",
    ) -> str:
        message = MessageProtocol._base(
            "FORWARD", sender_id, sender_name, content, avatar_base64
        )
        message.update(
            {
                "reply_to": None,
                "is_forwarded": True,
                "original_sender": original_sender,
                "original_msg_id": original_msg_id,
            }
        )
        return MessageProtocol.encode(message)

    @staticmethod
    def create_goodbye(sender_id: str, sender_name: str) -> str:
        return MessageProtocol.encode(
            MessageProtocol._base("GOODBYE", sender_id, sender_name)
        )

    @staticmethod
    def create_avatar_update(
        sender_id: str,
        sender_name: str,
        avatar_base64: str = "",
    ) -> str:
        """Gửi ngay khi người dùng đổi avatar của chính mình, để các peer đang
        kết nối cập nhật avatar mới mà không cần chờ tới lần bắt tay tiếp theo."""
        return MessageProtocol.encode(
            MessageProtocol._base("AVATAR_UPDATE", sender_id, sender_name, avatar_base64=avatar_base64)
        )

    @staticmethod
    def encode(message: Dict[str, Any]) -> str:
        """Serialize exactly one JSON message + newline frame."""
        if not isinstance(message, dict):
            raise TypeError("message must be a dict")
        return json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n"

    @staticmethod
    def parse_message(raw: str) -> Optional[Dict[str, Any]]:
        try:
            message = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

        if not isinstance(message, dict):
            return None

        required = {"version", "type", "msg_id", "sender_id", "sender_name"}
        if not required.issubset(message.keys()):
            return None

        return message

    @staticmethod
    def extract_frames(buffer: str) -> Tuple[List[Dict[str, Any]], str]:
        """Extract all complete newline-delimited JSON messages from buffer."""
        messages: List[Dict[str, Any]] = []
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            parsed = MessageProtocol.parse_message(line)
            if parsed is not None:
                messages.append(parsed)
        return messages, buffer

    @staticmethod
    def reply_preview(message: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "msg_id": message.get("msg_id"),
            "sender_name": message.get("sender_name", "Unknown"),
            "content": message.get("content", ""),
        }
