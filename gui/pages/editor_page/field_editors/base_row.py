from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QToolButton, QSizePolicy
)
from PySide6.QtCore import Signal, QEvent, Qt
from scapy.fields import BitField, ByteField, ShortField, IntField, LongField, IPField, MACField, Emph
import logging

log = logging.getLogger(__name__)


class BaseFieldRow(QWidget):
    infoRequested = Signal(str, str, str)

    def __init__(self, field_name_text, cls_name, field_desc, current_val, parent=None):
        super().__init__(parent)
        self.field_name_text = field_name_text
        self.cls_name = cls_name
        self.field_desc = self._remove_emph(field_desc)
        self.current_val = current_val

        self.editor_widget = None
        self.right_editor_container = None

        self._init_base_ui()
        self.setup_editor()
        self._install_event_filters()

    def _init_base_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)
        main_layout.setSpacing(15)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        left_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        left_container.setMinimumWidth(120)

        left_top_layout = QHBoxLayout()
        left_top_layout.setSpacing(5)

        self.name_label = QLabel(self.field_name_text)
        self.name_label.setStyleSheet("font-weight: bold;")

        self.info_btn = QToolButton()
        self.info_btn.setText("?")
        self.info_btn.setFixedSize(20, 20)
        self.info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.info_btn.setToolTip("Show field info")
        self.info_btn.clicked.connect(self._emit_info)

        left_top_layout.addWidget(self.name_label)
        left_top_layout.addWidget(self.info_btn)
        left_top_layout.addStretch()

        self.size_label = QLabel(self._get_size_string(self.field_desc))
        self.size_label.setStyleSheet("color: gray; font-size: 11px;")

        left_layout.addLayout(left_top_layout)
        left_layout.addWidget(self.size_label)
        left_layout.addStretch()

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        self.right_editor_container = QWidget()
        self.mid_layout = QVBoxLayout(self.right_editor_container)
        self.mid_layout.setContentsMargins(0, 0, 0, 0)

        bottom_view_container = QWidget()
        bottom_view_layout = QVBoxLayout(bottom_view_container)
        bottom_view_layout.setContentsMargins(0, 0, 0, 0)
        bottom_view_layout.setSpacing(2)

        self.hex_display = QLineEdit()
        self.hex_display.setObjectName("hexDisplay")
        self.hex_display.setPlaceholderText("HEX")
        self.hex_display.setReadOnly(True)

        self.bin_display = QLineEdit()
        self.bin_display.setObjectName("binDisplay")
        self.bin_display.setPlaceholderText("BIN")
        self.bin_display.setReadOnly(True)

        bottom_view_layout.addWidget(self.hex_display)
        bottom_view_layout.addWidget(self.bin_display)

        right_layout.addWidget(self.right_editor_container)
        right_layout.addWidget(bottom_view_container)

        main_layout.addWidget(left_container)
        main_layout.addWidget(right_container, 1)

    def setup_editor(self):
        """Override this in subclasses to inject the specific editor widget."""
        raise NotImplementedError

    def get_value(self):
        return self.current_val

    def _install_event_filters(self):
        if self.editor_widget:
            self.editor_widget.installEventFilter(self)
            for child in self.editor_widget.findChildren(QWidget):
                child.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.FocusIn:
            self._emit_info()
        return super().eventFilter(source, event)

    def _emit_info(self):
        type_name = self.field_desc.__class__.__name__.replace("Field", "")
        info_text = f"<b>Type:</b> {type_name}<br>"
        info_text += f"<b>Size:</b> {self._get_size_string(self.field_desc)}<br>"

        if hasattr(self.field_desc, "default") and self.field_desc.default is not None:
            try:
                default_val = self.field_desc.i2repr(None, self.field_desc.default)
            except Exception:
                default_val = str(self.field_desc.default)
            info_text += f"<b>Default:</b> {default_val}<br>"

        self.infoRequested.emit(self.cls_name, self.field_desc.name, info_text)

    def _update_displays_from_int(self, int_val):
        try:
            if int_val == -1:
                self.hex_display.setText("Auto")
                self.bin_display.setText("Auto")
                return

            total_bits = self._get_bits_count(self.field_desc, int_val)
            if total_bits == 0:
                total_bits = int_val.bit_length()

            raw_bin = f"{int_val:0{total_bits}b}"
            bin_chunks = [raw_bin[i:i + 8] for i in range(0, len(raw_bin), 8)]
            self.bin_display.setText(" ".join(bin_chunks))

            nibbles = (total_bits + 3) // 4
            if nibbles % 2 != 0:
                nibbles += 1

            raw_hex = f"{int_val:0{nibbles}X}"
            hex_chunks = [raw_hex[i:i + 2] for i in range(0, len(raw_hex), 2)]
            self.hex_display.setText(" ".join(hex_chunks))

        except Exception as e:
            log.error(f"Format error: {e}")
            self.hex_display.setText("Err")
            self.bin_display.setText("Err")

    def _get_size_string(self, f):
        if isinstance(f, BitField): return f"{f.size} bits"
        if hasattr(f, "sz"):
            size = f.sz
            if isinstance(size, float) and not size.is_integer():
                return f"{int(size * 8)} bits"
            return f"{int(size)} bytes"
        if isinstance(f, (ByteField, IPField)): return "1 byte"
        if isinstance(f, ShortField): return "2 bytes"
        if isinstance(f, (IntField, IPField)): return "4 bytes"
        if isinstance(f, LongField): return "8 bytes"
        if isinstance(f, MACField): return "6 bytes"
        return "Var"

    def _get_max_value(self, f):
        if isinstance(f, BitField): return (2 ** f.size) - 1
        if hasattr(f, "sz"): return (2 ** (f.sz * 8)) - 1
        return (2 ** 64) - 1

    def _get_bits_count(self, f, val=None):
        if isinstance(f, BitField): return f.size
        if hasattr(f, "sz"):
            return int(f.sz * 8)
        if val is not None:
            if isinstance(val, int): return val.bit_length()
            if isinstance(val, str): return len(val.encode('utf-8')) * 8
            if isinstance(val, bytes): return len(val) * 8
        return 0

    def _remove_emph(self, f):
        if isinstance(f, Emph): return f.fld
        return f