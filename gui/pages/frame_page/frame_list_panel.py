from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QHeaderView, QMenu
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

    def __init__(self, parent=None):
        super().__init__(parent)

        columns = ["Number", "Source", "Destination", "Protocol", "Length", "Info"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)

        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setUniformRowHeights(True)

        header = self.header()
        header.resizeSection(0, 60)
        header.resizeSection(1, 120)
        header.resizeSection(4, 120)
        header.resizeSection(5, 70)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)
        self.itemDoubleClicked.connect(self._on_item_clicked)

    def add_frame(self, frame):

        item = QTreeWidgetItem(self)

        def on_info_updated():
            # item.setText(0, str(frame.info['id']))
            # item.setText(1, frame.info.get('src', ''))
            # item.setText(2, frame.info.get('dst', ''))
            item.setData(0, Qt.ItemDataRole.UserRole, frame.id)
            pass

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

            menu.addAction(delete_action)

        menu.exec(self.mapToGlobal(position))

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

        print(f"Deleted {len(items)} of packets: {deleted_ids}")

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
