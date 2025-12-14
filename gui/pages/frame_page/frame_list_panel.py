from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QHeaderView, QMenu
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QPoint

from gui.utils import get_file


class FrameListPanel(QTreeWidget):

    frameSelected = Signal(int)
    framesDeleted = Signal(list)
    addNewFrame = Signal(str) #file path or empty string

    def __init__(self, parent=None):
        super().__init__(parent)

        columns = ["No.", "Time", "Source", "Destination", "Protocol", "Length", "Info"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.setUniformRowHeights(True)

        header = self.header()
        header.resizeSection(0, 60)
        header.resizeSection(1, 100)
        header.resizeSection(4, 80)
        header.resizeSection(5, 70)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        self.itemClicked.connect(self._on_item_clicked)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)

    def add_packet(self, packet_id, time, src, dst, proto, length, info):
        item = QTreeWidgetItem(self)
        item.setText(0, str(packet_id))
        item.setText(1, str(time))
        item.setText(2, src)
        item.setText(3, dst)
        item.setText(4, proto)
        item.setText(5, str(length))
        item.setText(6, info)
        item.setData(0, Qt.ItemDataRole.UserRole, packet_id)

    def _on_item_clicked(self, item, _):
        pkt_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.frameSelected.emit(pkt_id)


    def _open_context_menu(self, position: QPoint):

        # item = self.itemAt(position)

        selected_items = self.selectedItems()
        menu = QMenu()
        if not selected_items:
            add_new = QAction('Add new packet')
            add_new.triggered.connect(lambda : self.addNewFrame.emit(''))

            load_from_pcap = QAction('Load from pcap')
            load_from_pcap.triggered.connect(lambda : self._get_pcap_file())

            menu.addAction(add_new)
            menu.addAction(load_from_pcap)

        else:
            count = len(selected_items)
            delete_action = QAction(f"Delete Packet(s) ({count})")
            delete_action.triggered.connect(self._delete_selected_packets)

            menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(position))

    def _delete_selected_packets(self):
        items = self.selectedItems()
        if not items:
            return

        deleted_ids = []

        for item in items:
            pkt_id = item.data(0, Qt.ItemDataRole.UserRole)
            deleted_ids.append(pkt_id)

            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)

        print(f"Deleted {len(items)} of packets: {deleted_ids}")

        self.framesDeleted.emit(deleted_ids)

    def _get_pcap_file(self):
        file_filter = "Packet Capture (*.pcap)"
        file_name = get_file(self, file_filter)
        if file_name:
            self.addNewFrame.emit(file_name)