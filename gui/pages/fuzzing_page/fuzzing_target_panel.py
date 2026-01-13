from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QHeaderView
)
from PySide6.QtCore import Signal, Qt


class FuzzingTargetPanel(QWidget):
    """
    Panel displaying the packet structure tree.
    User selects a specific field to fuzz here.
    """

    fieldSelected = Signal(str, str) # layer_name, field_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fuzz_target_panel")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("1. Select Target Field")
        layout.addWidget(lbl)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Layer / Field", "Current Value"])
        self.tree.setColumnWidth(0, 180)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.tree)

        self.tree.itemClicked.connect(self._on_item_clicked)

    def load_packet_structure(self, scapy_pkt):
        self.tree.clear()

        current_layer = scapy_pkt
        while current_layer:
            layer_name = current_layer.name
            layer_item = QTreeWidgetItem(self.tree)
            layer_item.setText(0, layer_name)
            layer_item.setExpanded(True)

            # tag as layer
            layer_item.setData(0, Qt.ItemDataRole.UserRole, "LAYER")
            layer_item.setData(1, Qt.ItemDataRole.UserRole, layer_name)

            try:
                for field_name, value in current_layer.fields.items():
                    field_item = QTreeWidgetItem(layer_item)
                    field_item.setText(0, field_name)
                    field_item.setText(1, str(value))

                    # tag as field
                    field_item.setData(0, Qt.ItemDataRole.UserRole, "FIELD")
                    field_item.setData(1, Qt.ItemDataRole.UserRole, field_name)
            except:
                pass

            current_layer = current_layer.payload
            if current_layer.name == "NoPayload":
                break

    def _on_item_clicked(self, item, col):
        """
        Handles clicking on a specific field.
        :param item: item its clicked on
        :param col: column
        """

        tag = item.data(0, Qt.ItemDataRole.UserRole)

        if tag == "FIELD":
            field_name = item.data(1, Qt.ItemDataRole.UserRole)
            layer_name = item.parent().data(1, Qt.ItemDataRole.UserRole)
            self.fieldSelected.emit(layer_name, field_name)