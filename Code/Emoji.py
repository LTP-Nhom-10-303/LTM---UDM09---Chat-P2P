"""Reply and emoji helpers for the Chat GUI."""

EMOJIS = [
    "😀",
    "😂",
    "😍",
    "😊",
    "😢",
    "😡",
    "👍",
    "👎",
    "❤️",
    "🎉",
    "💯",
    "👏",
    "🔥",
    "🙏"
]

def reply_preview(message: dict) -> dict:
    return {
        "msg_id": message.get("msg_id"),
        "sender_name": message.get("sender_name", "Unknown"),
        "content": message.get("content", ""),
    }


