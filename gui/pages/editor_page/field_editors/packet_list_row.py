from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QGroupBox
)
from .base_row import BaseFieldRow
import logging
import scapy.all as scapy_all

log = logging.getLogger(__name__)

class PacketListRow(BaseFieldRow):
    def setup_editor(self):
        self.hex_display.hide()
        self.bin_display.hide()

        self.item_class = getattr(self.field_desc, "cls", None)

        # scapy uses an internal class (starts with '_'),
        # map it to the public class so it can be instantiated without the 's' parameter.
        if self.item_class and self.item_class.__name__.startswith("_"):
            public_cls_name = self.item_class.__name__.lstrip("_")
            public_cls = getattr(scapy_all, public_cls_name, None)
            if public_cls:
                self.item_class = public_cls

        self.editor_widget = QWidget()
        self.list_layout = QVBoxLayout(self.editor_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(5)

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.addWidget(self.items_container)

        btn_name = self.item_class.__name__ if self.item_class else "Item"
        self.add_btn = QPushButton(f"+ Add {btn_name}")
        self.add_btn.setObjectName("packetListAddBtn")
        self.add_btn.clicked.connect(lambda: self._add_item_ui(None))
        self.list_layout.addWidget(self.add_btn)

        self.mid_layout.insertWidget(0, self.editor_widget)

        self.item_editors = []

        if isinstance(self.current_val, list):
            for item in self.current_val:
                self._add_item_ui(item)

    def _add_item_ui(self, packet_instance):
        if not self.item_class:
            log.warning(f"Cannot add item: Unknown class for {self.field_desc.name}")
            return

        if packet_instance is None:
            packet_instance = self.item_class()

        box = QGroupBox(self.item_class.__name__)
        box.setObjectName("packetListGroupBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(5, 15, 5, 5)

        row_widgets = {}

        # prevent circular dependency
        from .factory import FieldRowFactory

        for f in packet_instance.fields_desc:
            val = packet_instance.getfieldval(f.name)

            row = FieldRowFactory.create_row(f.name, self.item_class.__name__, f, val)

            row.infoRequested.connect(self.infoRequested)

            box_layout.addWidget(row)
            row_widgets[f.name] = row

        del_btn = QPushButton("Remove")
        del_btn.setObjectName("packetListRemoveBtn")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(del_btn)
        box_layout.addLayout(btn_layout)

        self.items_layout.addWidget(box)

        item_entry = {"box": box, "rows": row_widgets, "cls": self.item_class}
        self.item_editors.append(item_entry)

        del_btn.clicked.connect(lambda: self._remove_item(item_entry))

    def _remove_item(self, item_entry):
        item_entry["box"].deleteLater()
        self.item_editors.remove(item_entry)

    def get_value(self):
        """
        Reconstructs the list of packets based on the UI states,
        applying type-casting safety checks.
        """
        result = []
        for item in self.item_editors:
            kwargs = {}

            field_map = {f.name: f for f in item["cls"].fields_desc}

            for fname, row_widget in item["rows"].items():
                val = row_widget.get_value()
                field_desc = field_map.get(fname)

                if hasattr(field_desc, 'fld'):
                    field_desc = field_desc.fld

                if isinstance(val, str) and field_desc:
                    cls_name = field_desc.__class__.__name__
                    if "Str" not in cls_name and "IP" not in cls_name and "MAC" not in cls_name:
                        try:
                            val = int(val, 0)
                        except ValueError:
                            pass

                kwargs[fname] = val

            try:
                pkt = item["cls"](**kwargs)
                result.append(pkt)
            except Exception as e:
                log.error(f"Failed to build list item {item['cls'].__name__}: {e}")

        return result