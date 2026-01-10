from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QHeaderView, QMenu, QFrame
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal, QPoint

from gui.utils import get_file


class FrameListPanel(QTreeWidget):
    """
    This gui class represents a list of all frames.
    """

    frameSelected = Signal(int)  # when frame gets selected
    framesDeleted = Signal(list) # when frames get deleted
    addNewFrame = Signal(str)  # when new frame is added
    sendRequest = Signal(int) # when to sender option is selected

    def __init__(self, parent=None):
        super().__init__(parent)

        columns = ["Number", "Source", "Destination", "Protocol", "Length", "Info"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        self.setObjectName("packet_list")

        for i in range(len(columns)):
            self.headerItem().setTextAlignment(i, Qt.AlignmentFlag.AlignCenter)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setUniformRowHeights(True)

        header = self.header()
        header.resizeSection(0, 100)
        header.resizeSection(1, 160)
        header.resizeSection(2, 160)
        header.resizeSection(3, 100)
        header.resizeSection(4, 100)

        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)
        self.itemDoubleClicked.connect(self._on_item_clicked)

    def add_frame(self, frame):

        item = QTreeWidgetItem(self)

        for i in range(self.columnCount()):
            if i == 5:
               item.setTextAlignment(i, Qt.AlignmentFlag.AlignLeft)
            else:
                item.setTextAlignment(i, Qt.AlignmentFlag.AlignCenter)

        def on_info_updated():
            info = frame.get_info()
            item.setText(0, info["id"])
            item.setText(1, info["src_ip"])
            item.setText(2, info["dst_ip"])
            item.setText(3, info["protocol"])
            item.setData(0, Qt.ItemDataRole.UserRole, frame.id)

        frame.infoUpdated.connect(on_info_updated)
        on_info_updated()

    def _on_item_clicked(self, item, _):
        """
        When item is double-clicked sends signal with its id.
        :param item: clicked item
        """
        pkt_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.frameSelected.emit(pkt_id)

    def _open_context_menu(self, position: QPoint):
        """
        Opens context menu
        :param position: mouse position
        """

        selected_items = self.selectedItems()
        menu = QMenu()
        if not selected_items:
            add_new = QAction('Add new packet')
            add_new.triggered.connect(lambda: self.addNewFrame.emit(''))

            load_from_pcap = QAction('Load from pcap')
            load_from_pcap.triggered.connect(lambda: self._get_pcap_file())

            menu.addAction(add_new)
            menu.addAction(load_from_pcap)

        else:
            count = len(selected_items)
            delete_action = QAction(f"Delete Packet(s) ({count})")
            delete_action.triggered.connect(self._delete_selected_frames)
            if count == 1:
                to_sender_action = QAction("To Sender")
                to_sender_action.triggered.connect(self._to_sender_action)
                menu.addAction(to_sender_action)

            menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(position))

    def _to_sender_action(self):
        item = self.selectedItems()[0]
        pkt_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.sendRequest.emit(pkt_id)

    def _delete_selected_frames(self):
        """
        Delete selected frames and emits signal with ids.
        """
        items = self.selectedItems()
        if not items:
            return

        deleted_ids = []

        for item in items:
            pkt_id = item.data(0, Qt.ItemDataRole.UserRole)
            deleted_ids.append(pkt_id)

            index = self.indexOfTopLevelItem(item)
            self.takeTopLevelItem(index)

        self.framesDeleted.emit(deleted_ids)

    def _get_pcap_file(self):
        """
        Gets pcap file and emits signal with its path.
        :return:
        """
        file_filter = "Packet Capture (*.pcap)"
        file_path = get_file(self, file_filter)
        if file_path:
            self.addNewFrame.emit(file_path)
