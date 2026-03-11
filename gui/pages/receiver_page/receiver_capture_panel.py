from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QHBoxLayout, QMenu
)
from PySide6.QtCore import Signal, Qt, QPoint
from gui.pages.frame_page.hexdump_window import HexDumpWindow


class DummyFrame:
    def __init__(self, pkt_id, hex_string):
        self.id = pkt_id
        self.scapy = bytes.fromhex(hex_string)


class ReceiverCapturePanel(QWidget):
    clearRequested = Signal()
    saveRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opened_windows = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_layout = QHBoxLayout()

        top_layout.addStretch()

        btn_clear = QPushButton("Clear Table")
        btn_clear.setProperty("styleClass", "common_button")
        btn_clear.clicked.connect(self.clear_table)
        btn_clear.clicked.connect(self.clearRequested.emit)
        top_layout.addWidget(btn_clear)

        layout.addLayout(top_layout)

        self.packet_list = QTreeWidget()
        self.packet_list.setObjectName("packet_list")
        self.packet_list.setColumnCount(3)
        self.packet_list.setHeaderLabels(["#", "Length", "Summary"])

        self.packet_list.setRootIsDecorated(False)
        self.packet_list.setIndentation(0)
        self.packet_list.setAlternatingRowColors(True)
        self.packet_list.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.packet_list.setUniformRowHeights(True)

        header = self.packet_list.header()
        header.resizeSection(0, 50)
        header.resizeSection(1, 80)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.packet_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.packet_list.customContextMenuRequested.connect(self._open_context_menu)
        self.packet_list.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.packet_list)

    def add_packet(self, packet_data):
        row_count = self.packet_list.topLevelItemCount() + 1
        length_val = str(packet_data.get("len", 0))
        summary_val = packet_data.get("summary", "No summary")
        hex_val = packet_data.get("hex_data", "")

        item = QTreeWidgetItem()
        item.setText(0, str(row_count))
        item.setText(1, length_val)
        item.setText(2, summary_val)

        item.setTextAlignment(0, Qt.AlignmentFlag.AlignCenter)
        item.setTextAlignment(1, Qt.AlignmentFlag.AlignCenter)

        item.setData(0, Qt.ItemDataRole.UserRole, hex_val)

        self.packet_list.addTopLevelItem(item)

    def clear_table(self):
        self.packet_list.clear()

    def _open_context_menu(self, position: QPoint):
        selected_items = self.packet_list.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        menu.addAction("Show Hexdump", lambda: self._show_hexdump(selected_items[0]))
        menu.exec(self.packet_list.mapToGlobal(position))

    def _on_item_double_clicked(self, item, column):
        self._show_hexdump(item)

    def _show_hexdump(self, item):
        hex_data = item.data(0, Qt.ItemDataRole.UserRole)
        pkt_id = item.text(0)

        if hex_data:
            dummy_frame = DummyFrame(pkt_id, hex_data)
            window = HexDumpWindow(dummy_frame)
            self._opened_windows.append(window)
            window.destroyed.connect(lambda: self._cleanup_window(window))
            window.show()

    def _cleanup_window(self, window):
        if window in self._opened_windows:
            self._opened_windows.remove(window)