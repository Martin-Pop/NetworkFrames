import logging
import uuid

from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QHeaderView, QMenu, QFrame, QInputDialog
)
from PySide6.QtGui import QColor, QBrush
from PySide6.QtCore import Qt, Signal, QPoint

from utils.files import get_file, save_file
from gui.pages.frame_page.hexdump_window import HexDumpWindow

# ROLES
ROLE_ID = Qt.ItemDataRole.UserRole + 1
ROLE_IS_GROUP = Qt.ItemDataRole.UserRole + 2
ROLE_FRAME = Qt.ItemDataRole.UserRole + 3

log = logging.getLogger(__name__)


class FrameListPanel(QTreeWidget):
    """
    This gui class represents a list of all frames.
    """

    frameSelected = Signal(int)
    framesDeleted = Signal(list)
    framesSaved = Signal(str, list)  # path and list of ids
    addNewFrame = Signal(str, str)  # path or empty string, uuid (group id) or empty string
    sendRequest = Signal(list, str)
    openFuzzingRequest = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._opened_windows = []

        self.item_map = {}  # frame_id : QTreeWidgetItem
        self.group_map = {}

        columns = ["ID/GROUP", "Source", "Destination", "Protocol", "Length", "Info"]
        self.setColumnCount(len(columns))
        self.setHeaderLabels(columns)
        self.setObjectName("packet_list")

        self.setRootIsDecorated(False)
        self.setIndentation(15)

        self.setAlternatingRowColors(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setUniformRowHeights(True)

        for i in range(len(columns)):
            self.headerItem().setTextAlignment(i, Qt.AlignmentFlag.AlignCenter)

        # header sizes
        header = self.header()
        header.resizeSection(0, 120)
        header.resizeSection(1, 140)
        header.resizeSection(2, 140)
        header.resizeSection(3, 80)
        header.resizeSection(4, 80)

        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._open_context_menu)
        self.itemDoubleClicked.connect(self._on_item_clicked)

    def add_frame(self, frame, group_id):
        """
        Adds new frame to top
        :param frame: fram to add
        :param group_id: group id to add new frame to, empty string for no group
        """
        item = QTreeWidgetItem()
        self._setup_item_appearance(item)
        self._bind_frame_data(item, frame)
        self.item_map[frame.id] = item

        if group_id and group_id in self.group_map:
            target_group = self.group_map[group_id]
            target_group.addChild(item)
            target_group.setExpanded(True)
        else:
            self.addTopLevelItem(item)

        self._update_decoration_state()

    def add_frames(self, frame_list, group_id):
        """
        Optimized method to add multiple frames at once.
        Prevents UI flickering and freezing.
        :param frame_list: list of frame objects
        :param group_id: group id to add frames to
        """
        self.setUpdatesEnabled(False)

        target_parent = self
        if group_id and group_id in self.group_map:
            target_parent = self.group_map[group_id]

        items = []
        for frame in frame_list:
            item = QTreeWidgetItem()
            self._setup_item_appearance(item)
            self._bind_frame_data(item, frame)
            self.item_map[frame.id] = item
            items.append(item)

        if target_parent == self:
            self.addTopLevelItems(items)
        else:
            target_parent.addChildren(items)
            target_parent.setExpanded(True)

        self._update_decoration_state()
        self.setUpdatesEnabled(True)

    def _create_group(self):
        name, ok = QInputDialog.getText(self, "Create Group", "Group Name:")
        if not ok or not name:
            return None
        return self.create_named_group(name)

    def create_named_group(self, name):
        group_item = QTreeWidgetItem(self)
        group_item.setText(0, name.strip())

        font = group_item.font(5)
        font.setBold(True)
        group_item.setFont(5, font)
        group_item.setForeground(5, QBrush(QColor("#E8834A")))

        group_item.setData(0, ROLE_IS_GROUP, True)

        virtual_id = str(uuid.uuid4())
        group_item.setData(0, ROLE_ID, virtual_id)

        self.group_map[virtual_id] = group_item
        self.addTopLevelItem(group_item)

        return group_item

    def _setup_item_appearance(self, item):
        for i in range(self.columnCount()):
            align = Qt.AlignmentFlag.AlignLeft if i == 5 else Qt.AlignmentFlag.AlignCenter
            item.setTextAlignment(i, align)

    def _bind_frame_data(self, item, frame):
        """
        Binds info to frame
        :param item: item to bind
        :param frame: frame with info
        """

        item.setData(0, ROLE_FRAME, frame)

        def on_info_updated():
            info = frame.get_info()
            item.setText(0, str(info["id"]))
            item.setText(1, info["src_ip"])
            item.setText(2, info["dst_ip"])
            item.setText(3, info["protocol"])
            item.setText(4, str(info["len"]))
            item.setText(5, info["info"])
            item.setData(0, ROLE_ID, frame.id)
            item.setData(0, ROLE_IS_GROUP, False)

        frame.infoUpdated.connect(on_info_updated)
        on_info_updated()

    def _update_decoration_state(self):
        """
        Checks if there are any groups (items with children).
        if yes -> enable tree (arrows)
        if no -> disable tree (no arrows).
        """
        has_groups = False
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.childCount() > 0 or item.data(0, ROLE_IS_GROUP) is True:
                has_groups = True
                break

        # this fixes flickering
        if self.rootIsDecorated() != has_groups:
            self.setRootIsDecorated(has_groups)

    def _open_context_menu(self, position: QPoint):
        """
        Opens context menu
        :param position: mouse position
        """
        selected_items = self.selectedItems()
        menu = QMenu()

        if not selected_items:
            menu.addAction('Add New', lambda: self.addNewFrame.emit('', ''))
            menu.addAction('Load from PCAP', self._load_pcap)
            menu.addAction('Load from PCAP as new group', self._load_pcap_as_group)
            menu.addAction('Create Group', self._create_empty_group)
            menu.exec(self.mapToGlobal(position))
            return

        count = len(selected_items)
        contains_group = any(item.data(0, ROLE_IS_GROUP) for item in selected_items)
        all_groups = all(item.data(0, ROLE_IS_GROUP) for item in selected_items)

        single_group = (count == 1 and all_groups)
        single_frame = (count == 1 and not contains_group)

        # menu for single group
        if single_group:
            current_id = selected_items[0].data(0, ROLE_ID)
            menu.addAction('Add New Packet Here', lambda: self.addNewFrame.emit('', current_id))
            menu.addAction('Load PCAP to group', lambda: self._load_pcap(current_id))
            menu.addSeparator()

        # menu for everything
        menu.addAction("To Sender", lambda: self._send_selection(selected_items))
        menu.addAction("Save as PCAP...", lambda: self._save_selection(selected_items))

        # menu for single frame
        if single_frame:
            menu.addSeparator()
            item = selected_items[0]
            current_id = item.data(0, ROLE_ID)
            menu.addAction("Fuzz", lambda: self.openFuzzingRequest.emit(current_id))
            menu.addAction("Show Hexdump", lambda: self._open_hexdump_window(item))

        # grouping
        menu.addSeparator()
        if count > 1 and not contains_group:
            menu.addAction(f"Group ({count}) items", lambda: self._create_group_from_selection(selected_items))

        if single_group:
            menu.addAction("Ungroup", lambda: self._ungroup(selected_items[0]))

        # deleting
        menu.addSeparator()
        del_text = "Delete" if count == 1 else f"Delete Selected ({count})"
        menu.addAction(del_text, self._delete_selection)

        menu.exec(self.mapToGlobal(position))

    def _save_selection(self, selected_items):
        """
        Saves selection as PCAP
        :param selected_items: selected items
        """
        path = save_file(self, "Packet Capture (*.pcap)")
        if not path:
            return

        ids = self._get_unique_ids_from_selection(selected_items)
        self.framesSaved.emit(path, ids)

    def _send_selection(self, selected_items):
        """
        Sends selection to sender
        :param selected_items: selected items
        """
        ids = self._get_unique_ids_from_selection(selected_items)

        group_name = ''
        if len(selected_items) == 1 and selected_items[0].data(0, ROLE_IS_GROUP):
            group_name = selected_items[0].text(0)

        self.sendRequest.emit(ids, group_name)

    def _get_unique_ids_from_selection(self, selected_items):
        """
        Helper function for getting unique ids from selection
        :param selected_items: selected items
        :return: list of unique ids
        """
        ids = []
        for item in selected_items:
            if item.data(0, ROLE_IS_GROUP):
                for i in range(item.childCount()):
                    ids.append(item.child(i).data(0, ROLE_ID))
            else:
                ids.append(item.data(0, ROLE_ID))

        seen = set()
        unique_ids = [x for x in ids if not (x in seen or seen.add(x))]
        return unique_ids

    def _create_empty_group(self):
        """
        Creates empty group
        """
        group_item = self._create_group()
        if group_item:
            self._update_decoration_state()

    def _create_group_from_selection(self, selected_items):
        """
        Creates group from selection
        :param selected_items: selected items
        """
        if any(item.data(0, ROLE_IS_GROUP) for item in selected_items):
            return

        group_item = self._create_group()
        if not group_item:
            return

        for item in selected_items:
            parent = item.parent()
            # gets removed from old group
            if parent:
                parent.removeChild(item)
            else:
                idx = self.indexOfTopLevelItem(item)
                if idx != -1:
                    self.takeTopLevelItem(idx)

            group_item.addChild(item)

        group_item.setExpanded(True)
        self._update_decoration_state()

    def _ungroup(self, group_item):
        """
        Ungroups items, first saves its children then readds them to root.
        :param group_item: group item (widget)
        :return:
        """
        children = [group_item.child(i) for i in range(group_item.childCount())]
        group_index = self.indexOfTopLevelItem(group_item)

        for i, child in enumerate(children):
            group_item.removeChild(child)
            self.insertTopLevelItem(group_index + i, child)

        virtual_id = group_item.data(0, ROLE_ID)
        if virtual_id in self.group_map:
            del self.group_map[virtual_id]

        self.takeTopLevelItem(self.indexOfTopLevelItem(group_item))
        self._update_decoration_state()

    def _delete_selection(self):
        """
        Deletes selection
        """
        items = self.selectedItems()
        if not items: return

        ids_to_delete = set()

        for item in items:
            if item.data(0, ROLE_IS_GROUP):
                virtual_id = item.data(0, ROLE_ID)
                if virtual_id in self.group_map:
                    del self.group_map[virtual_id]

                for i in range(item.childCount()):
                    child = item.child(i)
                    pkt_id = child.data(0, ROLE_ID)
                    ids_to_delete.add(pkt_id)
                    if pkt_id in self.item_map:
                        del self.item_map[pkt_id]

                idx = self.indexOfTopLevelItem(item)
                if idx != -1:
                    self.takeTopLevelItem(idx)

            else:
                pkt_id = item.data(0, ROLE_ID)
                ids_to_delete.add(pkt_id)
                if pkt_id in self.item_map:
                    del self.item_map[pkt_id]

                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    idx = self.indexOfTopLevelItem(item)
                    if idx != -1:
                        self.takeTopLevelItem(idx)

        self._update_decoration_state()
        self.framesDeleted.emit(list(ids_to_delete))

    def _on_item_clicked(self, item, _):
        """
        Double click frame to use editor
        :param item: item clicked on
        :param _:
        :return: early if its group header
        """
        if item.data(0, ROLE_IS_GROUP):
            return

        pkt_id = item.data(0, ROLE_ID)
        self.frameSelected.emit(pkt_id)

    def _load_pcap(self, parent_id=None):
        """
        Gets pcap file and emits signal to create new frames from this file
        :param parent_id: parent is group id if pcap is loaded into already existing group
        """
        file_filter = "Packet Capture (*.pcap)"
        file_path = get_file(self, file_filter)
        if file_path:
            self.addNewFrame.emit(file_path, parent_id if parent_id else '')

    def _load_pcap_as_group(self):
        """
        Loads frames from pcap file as a new group
        """
        group_item = self._create_group()
        if not group_item:
            return

        group_id = group_item.data(0, ROLE_ID)
        file_filter = "Packet Capture (*.pcap)"
        file_path = get_file(self, file_filter)

        if file_path:
            self.addNewFrame.emit(file_path, group_id)
        else:
            if group_id in self.group_map:
                del self.group_map[group_id]

            idx = self.indexOfTopLevelItem(group_item)
            self.takeTopLevelItem(idx)

    def _open_hexdump_window(self, item):
        frame = item.data(0, ROLE_FRAME)
        if frame:
            window = HexDumpWindow(frame)

            self._opened_windows.append(window)
            window.destroyed.connect(lambda: self._cleanup_window(window))
            window.show()

    def _cleanup_window(self, window):
        if window in self._opened_windows:
            self._opened_windows.remove(window)