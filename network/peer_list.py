from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem
)


class PeerList(QWidget):

    def __init__(self):
        super().__init__()

        # Ô tìm kiếm peer
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍Tìm bạn bè...")

        # Danh sách peer
        self.list_widget = QListWidget()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.search_box)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

        # Khi nhập vào ô tìm kiếm
        self.search_box.textChanged.connect(self.search_peer)

    def add_peer(self, peer):
        """Thêm peer vào danh sách."""

        item = QListWidgetItem(
            f"👤{peer} - Online"
        )

        item.setData(Qt.UserRole, peer)
        item.setData(Qt.UserRole + 1, True)

        self.list_widget.addItem(item)

    def update_peer_status(self, peer, online):
        """Cập nhật trạng thái Online / Offline."""

        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)

            if item.data(Qt.UserRole) == peer:

                status = "Online" if online else "Offline"

                item.setText(
                    f"{peer} - {status}"
                )

                item.setData(
                    Qt.UserRole + 1,
                    online
                )

                break

    def search_peer(self, text):
        """Tìm kiếm peer theo tên."""

        text = text.lower()

        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)

            peer = item.data(Qt.UserRole)

            if text in peer.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def get_selected_peer(self):
        """Lấy peer đang được chọn."""

        item = self.list_widget.currentItem()

        if item and not item.isHidden():
            return item.data(Qt.UserRole)

        return None