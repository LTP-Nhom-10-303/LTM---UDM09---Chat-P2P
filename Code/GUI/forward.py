"""Forward-message helper."""

from typing import Dict
from protocol.message_protocol import MessageProtocol


def build_forward_message(
    local_id: str,
    local_name: str,
    selected_message: Dict,
    avatar_base64: str = "",
) -> str:
    return MessageProtocol.create_forward_message(
        sender_id=local_id,
        sender_name=local_name,
        content=selected_message.get("content", ""),
        original_sender=selected_message.get("sender_name", "Unknown"),
        original_msg_id=selected_message.get("msg_id", ""),
        avatar_base64=avatar_base64,
    )
