import json
from Message_protocol import MessageProtocol


emoji_list = [
    "😀",
    "😂",
    "😍",
    "😊",
    "😢",
    "😡",
    "👍",
    "👎",
    "❤️",
    "🎉"
]


def show_emoji_list():
    print("\n===== DANH SÁCH EMOJI =====")

    for i, emoji in enumerate(emoji_list, 1):
        print(f"{i}. {emoji}")


def choose_emoji():
    show_emoji_list()

    choice = input("\nNhập số Emoji muốn chọn: ").strip()

    if not choice.isdigit():
        print("Vui lòng nhập số.")
        return None

    choice = int(choice)

    if choice < 1 or choice > len(emoji_list):
        print("Số Emoji không hợp lệ.")
        return None

    return emoji_list[choice - 1]


def create_emoji_message(emoji):
    message = MessageProtocol.create_json_message(
        sender_name="User",
        content=emoji
    )

    return message


if __name__ == "__main__":
    selected_emoji = choose_emoji()

    if selected_emoji:
        print("\nEmoji đã chọn:", selected_emoji)

        emoji_message = create_emoji_message(selected_emoji)

        print("\n===== EMOJI JSON =====")
        print(emoji_message)
