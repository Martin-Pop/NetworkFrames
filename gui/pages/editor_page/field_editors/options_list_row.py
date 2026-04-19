from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit
)
from .base_row import BaseFieldRow
import ast
import logging


log = logging.getLogger(__name__)


class OptionsListRow(BaseFieldRow):
    """
    Editor specifically designed for Scapy options fields (like DHCPOptions)
    which are represented as lists of tuples: [('message-type', 5), ('end')]
    """

    def setup_editor(self):
        self.hex_display.hide()
        self.bin_display.hide()

        self.editor_widget = QWidget()
        self.list_layout = QVBoxLayout(self.editor_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(5)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)
        self.list_layout.addWidget(self.items_container)

        self.add_btn = QPushButton("+ Add Option")
        self.add_btn.setObjectName("packetListAddBtn")
        self.add_btn.clicked.connect(lambda: self._add_item_ui("", ""))
        self.list_layout.addWidget(self.add_btn)

        self.mid_layout.insertWidget(0, self.editor_widget)

        self.item_editors = []

        if isinstance(self.current_val, list):
            for item in self.current_val:
                if isinstance(item, tuple) and len(item) == 2:
                    self._add_item_ui(str(item[0]), str(item[1]))
                elif isinstance(item, tuple) and len(item) > 0:
                    self._add_item_ui(str(item[0]), "")
                else:
                    self._add_item_ui(str(item), "")

    def _add_item_ui(self, key_text, val_text):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        key_edit = QLineEdit(key_text)
        key_edit.setPlaceholderText("Option (e.g. message-type)")

        val_edit = QLineEdit(val_text)
        val_edit.setPlaceholderText("Value (leave empty if none)")

        del_btn = QPushButton("X")
        del_btn.setObjectName("btn_remove_layer")
        del_btn.setFixedWidth(30)
        del_btn.clicked.connect(lambda: self._remove_item(row_widget))

        row_layout.addWidget(key_edit)
        row_layout.addWidget(val_edit)
        row_layout.addWidget(del_btn)

        self.items_layout.addWidget(row_widget)
        self.item_editors.append((row_widget, key_edit, val_edit))

    def _remove_item(self, row_widget):
        row_widget.deleteLater()
        self.item_editors = [item for item in self.item_editors if item[0] != row_widget]

    def get_value(self):
        """
        Reconstructs the list of tuples for Scapy when saving.
        """
        result = []
        for _, key_edit, val_edit in self.item_editors:
            k = key_edit.text().strip()
            v = val_edit.text().strip()

            if not k:
                continue

            if not v:
                result.append(k)
                continue

            try:
                parsed_v = ast.literal_eval(v)
            except (ValueError, SyntaxError):
                parsed_v = v

            result.append((k, parsed_v))

        return result