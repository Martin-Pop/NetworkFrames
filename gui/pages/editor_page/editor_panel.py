from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QFormLayout, QFrame, QScrollArea,
    QStackedWidget, QLabel, QLineEdit,
    QGroupBox, QComboBox, QGridLayout, QCheckBox,
    QSpinBox, QHBoxLayout, QDoubleSpinBox, QToolButton
)
from PySide6.QtCore import Signal, QEvent, Qt

from scapy.fields import *
import logging, struct, socket

log = logging.getLogger(__name__)


class ScapyFieldRow(QWidget):
    """
    A unified row widget containing:
    1. Main Editor (Editable - Type specific)
    2. Hex View (Read-only)
    3. Binary View (Read-only)
    4. Size Label (Static info)
    """

    infoRequested = Signal(str, str, str) #layer, field, text

    def __init__(self, cls_name, field_desc, current_val, parent=None):
        super().__init__(parent)
        self.cls_name = cls_name
        self.field_desc = field_desc
        self.current_val = current_val

        # main
        # [mid] [size] [info]
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # mid
        # [    editor widget    ]
        # [bottom_view_container]
        self.mid_container = QWidget()
        self.mid_layout = QVBoxLayout(self.mid_container)
        self.mid_layout.setContentsMargins(0, 0, 0, 0)
        self.mid_layout.setSpacing(5)

        # bottom
        # [Bin display] [Hex display]
        self.bottom_view_container = QWidget()
        self.bottom_view_layout = QHBoxLayout(self.bottom_view_container)
        self.bottom_view_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_view_layout.setSpacing(5)

        self.editor_widget = None

        # Bin
        self.bin_display = QLineEdit()
        self.bin_display.setPlaceholderText("BIN")
        self.bin_display.setReadOnly(True)
        self.bin_display.setFrame(False)

        # Hex
        self.hex_display = QLineEdit()
        self.hex_display.setPlaceholderText("HEX")
        self.hex_display.setReadOnly(True)
        self.hex_display.setFixedWidth(100)

        # Size Label
        size_str = self._get_size_string(field_desc)
        self.size_label = QLabel(size_str)
        self.size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        # self.size_label.setFixedWidth(60)

        # Info Button
        self.info_btn = QToolButton()
        self.info_btn.setText("?")
        self.info_btn.setFixedWidth(25)
        self.info_btn.setToolTip("Show field info")
        self.info_btn.clicked.connect(self._emit_info)

        self.bottom_view_layout.addWidget(self.bin_display)
        self.bottom_view_layout.addWidget(self.hex_display)

        self.mid_layout.addWidget(self.bottom_view_container)

        self.layout.addWidget(self.mid_container)
        self.layout.addWidget(self.size_label)
        self.layout.addWidget(self.info_btn)

        self._init_editor_by_type()

        if self.editor_widget:
            self.editor_widget.installEventFilter(self)
            for child in self.editor_widget.findChildren(QWidget):
                child.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.FocusIn:
            self._emit_info()
        return super().eventFilter(source, event)

    def _emit_info(self):
        f = self.field_desc
        info_text = f"<b>Type:</b> {f.__class__.__name__}<br>"
        info_text += f"<b>Size:</b> {self._get_size_string(f)}<br>"

        if hasattr(f, "default"):
            info_text += f"<b>Default:</b> {f.default}<br>"

        self.infoRequested.emit(self.cls_name, f.name ,info_text)

    def get_value(self):
        """Returns the value from the main editor."""
        if hasattr(self.editor_widget, "currentData"):  # Prob unused now
            return self.editor_widget.currentData()
        elif hasattr(self.editor_widget, "value"):  # SpinBox
            return int(self.editor_widget.value())
        elif isinstance(self.editor_widget, QLineEdit):  # String/IP
            return self.editor_widget.text()
        elif isinstance(self.editor_widget, QGroupBox):  # Flags Custom method
            return self._get_flags_value()
        return self.current_val  # Fallback

    # factory init helpers
    def _init_editor_by_type(self):
        f = self._remove_emph(self.field_desc)
        val = self.current_val

        # enum
        if isinstance(f, (EnumField, MultiEnumField)):
            self._setup_enum(f, val)

        # flags
        elif isinstance(f, FlagsField):
            self._setup_flags(f, val)

        # number value
        elif isinstance(f, (IntField, ShortField, ByteField, LongField, BitField)):
            self._setup_number(f, val)

        # string / ip / mac
        elif isinstance(f, (IPField, MACField, StrField)):
            self._setup_string(f, val)

        # fallback raed-only
        else:
            self._setup_readonly(f, val)

    # setup methods
    def _setup_number(self, f, val):
        self.editor_widget = QDoubleSpinBox()
        self.editor_widget.setDecimals(0)
        self.editor_widget.setRange(0, self._get_max_value(f))
        self.editor_widget.setGroupSeparatorShown(False)
        self.editor_widget.setValue(int(val) if val is not None else 0)

        self.editor_widget.valueChanged.connect(self._update_from_int)

        self.mid_layout.insertWidget(0, self.editor_widget, 1)
        self._update_from_int(self.editor_widget.value())

    def _setup_enum(self, f, val):

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        options = getattr(f, "i2s", {})

        max_val = self._get_max_value(f)

        spin_widget = QSpinBox()
        spin_widget.setRange(0, max_val)
        current_int = int(val) if val is not None else 0
        spin_widget.setValue(current_int)

        self.editor_widget = spin_widget  # make spinbox main

        # combobox helper
        combo_widget = QComboBox()
        combo_widget.addItem("Custom / Unknown", -1)  # index 0

        # sorted_options = sorted(options.items(), key=lambda item: item[0])
        for v, name in options.items():
            combo_widget.addItem(f"{name} ({v})", v)

        # sync
        def on_combo_changed(idx):
            data = combo_widget.currentData()
            if data != -1:  # ignore -1 (unknown/custom)
                spin_widget.blockSignals(True)
                spin_widget.setValue(int(data))
                spin_widget.blockSignals(False)
                self._update_from_int(data)

        def on_spin_changed(val):
            idx = combo_widget.findData(val)
            combo_widget.blockSignals(True)
            if idx >= 0:
                combo_widget.setCurrentIndex(idx)
            else:
                combo_widget.setCurrentIndex(0)  # unknown / custom
            combo_widget.blockSignals(False)

            self._update_from_int(val)

        combo_widget.currentIndexChanged.connect(on_combo_changed)
        spin_widget.valueChanged.connect(on_spin_changed)
        on_spin_changed(current_int)

        container_layout.addWidget(spin_widget, 1)
        container_layout.addWidget(combo_widget, 1)

        self.mid_layout.insertWidget(0, container)
        self._update_from_int(current_int)

    def _setup_flags(self, f, val):
        # Container for checkboxes
        self.editor_widget = QGroupBox()
        self.editor_widget.setStyleSheet("border: none; margin: 0; padding: 0;")
        self.flags_layout = QGridLayout(self.editor_widget)
        self.flags_layout.setContentsMargins(0, 0, 0, 0)

        self.checkboxes = []
        flag_names = getattr(f, "names", [])
        current_int = int(val) if val is not None else 0

        for i, name in enumerate(flag_names):
            chk = QCheckBox(name)
            mask = 1 << i
            chk.setProperty("mask", mask)
            if current_int & mask:
                chk.setChecked(True)

            chk.toggled.connect(self._update_from_flags)

            self.checkboxes.append(chk)
            self.flags_layout.addWidget(chk, i // 2, i % 2)  # 2 columns

        self.mid_layout.insertWidget(0, self.editor_widget)
        self._update_from_flags()

    def _setup_string(self, f, val):
        self.editor_widget = QLineEdit()
        txt = ""
        if val is not None:
            if isinstance(val, bytes):
                txt = val.decode('utf-8', errors='ignore')
            else:
                txt = str(val)
        self.editor_widget.setText(txt)

        self.editor_widget.textChanged.connect(self._update_from_string)

        self.mid_layout.insertWidget(0, self.editor_widget)
        self._update_from_string(txt)

    def _setup_readonly(self, f, val):
        log.debug(f'setting up readonly for: {f} {val}')
        if val is not None:
            try:
                repr_val = f.i2repr(None, val)
            except (AttributeError, TypeError, ValueError):
                repr_val = str(val)
        else:
            repr_val = "None"
        self.editor_widget = QLabel(repr_val)
        self.editor_widget.setStyleSheet("color: gray; font-style: italic;")
        self.mid_layout.insertWidget(0, self.editor_widget)

        self.hex_display.setText("-")
        self.bin_display.setText("-")

    # update sync
    def _update_from_int(self, val):
        """Updates Hex/Bin based on integer value with padding."""
        try:
            int_val = int(val)

            total_bits = self._get_bits_count(self.field_desc, int_val)

            if total_bits == 0:
                total_bits = int_val.bit_length()

            # bin - split by 8
            raw_bin = f"{int_val:0{total_bits}b}"
            chunk_size = 8
            bin_chunks = [raw_bin[i:i + chunk_size] for i in range(0, len(raw_bin), chunk_size)]
            formatted_bin = " ".join(bin_chunks)

            self.bin_display.setText(formatted_bin)

            # hex 4 bits = one symbol
            # (total_bits + 3) // 4 => integer division with rounding up
            hex_chars = (total_bits + 3) // 4
            formatted_hex = f"0x{int_val:0{hex_chars}X}"

            self.hex_display.setText(formatted_hex)

        except Exception as e:
            log.error(f"Format error: {e}")
            self.hex_display.setText("Err")
            self.bin_display.setText("Err")

    def _update_from_flags(self):
        """Calculates int from checkboxes and updates displays."""
        total = self._get_flags_value()
        self._update_from_int(total)

    def _get_flags_value(self):
        total = 0
        for chk in self.checkboxes:
            if chk.isChecked():
                total |= chk.property("mask")
        return total

    def _update_from_string(self, text):
        """
        Updates hex and bin displays, if its MAC or IP address its converted to int then handled with _update_from_int.
        :param text: string to use
        """
        f = self._remove_emph(self.field_desc)

        try:

            # MAC
            if isinstance(f, MACField):
                clean_mac = text.replace(":", "").replace("-", "").replace(".", "")
                if len(clean_mac) <= 12:  # Basic validation
                    val_int = int(clean_mac, 16)
                    self._update_from_int(val_int)
                    return

            # IPV4
            if isinstance(f, IPField):
                packed = socket.inet_aton(text)
                val_int = struct.unpack("!I", packed)[0]  # ! = Network (Big) Endian
                self._update_from_int(val_int)
                return

            # IPV6
            if isinstance(f, (IP6Field, SourceIP6Field, DestIP6Field)):
                packed = socket.inet_pton(socket.AF_INET6, text)
                val_int = int.from_bytes(packed, byteorder='big')
                self._update_from_int(val_int)
                return

            # raw text
            if isinstance(text, str):
                b = text.encode('utf-8', errors='ignore')
            else:
                b = bytes(text)


            h = b.hex().upper()
            formatted_hex = " ".join([h[i:i + 2] for i in range(0, len(h), 2)])
            self.hex_display.setText(formatted_hex)

            if len(b) <= 8:  # max 8 bytes
                int_val = int.from_bytes(b, byteorder='big')
                total_bits = len(b) * 8
                raw_bin = f"{int_val:0{total_bits}b}"
                bin_chunks = [raw_bin[i:i + 8] for i in range(0, len(raw_bin), 8)]
                self.bin_display.setText(" ".join(bin_chunks))
            else:
                self.bin_display.setText("(Too long)")

        except Exception as e:
            self.hex_display.setText("-")
            self.bin_display.setText("-")

    # size calc
    def _get_size_string(self, f):
        """
        Determines the size of the field in bits or bytes.
        Handles fractional bytes (bits) correctly.
        """

        if isinstance(f, BitField):
            return f"{f.size} bits"

        if hasattr(f, "sz"):
            size = f.sz

            if isinstance(size, float) and not size.is_integer():
                return f"{int(size * 8)} bits"

            # Je to celé číslo (např. 1, 2, 4) -> jsou to bajty
            return f"{int(size)} bytes"

        if isinstance(f, (ByteField, IPField)): return "1 byte"
        if isinstance(f, ShortField): return "2 bytes"
        if isinstance(f, (IntField, IPField)): return "4 bytes"
        if isinstance(f, LongField): return "8 bytes"
        if isinstance(f, MACField): return "6 bytes"

        return "Var"  # fallback

    def _get_max_value(self, f):

        if isinstance(f, BitField):
            return (2 ** f.size) - 1

        if hasattr(f, "sz"):
            return (2 ** (f.sz * 8)) - 1

        return (2 ** 64) - 1

    def _get_bits_count(self, f, val=None):
        """
        Gets exact number of bits in a field.
        :param f: field
        :param val: current value
        :return: number of bits
        """
        if isinstance(f, BitField):
            return f.size

        if hasattr(f, "sz"):
            size = f.sz
            if isinstance(size, float) and not size.is_integer():
                return int(size * 8)
            return int(size * 8)

        if val is not None:
            if isinstance(val, int):
                return val.bit_length()
            if isinstance(val, str):
                return len(val.encode('utf-8')) * 8
            if isinstance(val, bytes):
                return len(val) * 8

        return 0  # Fallback

    def _remove_emph(self, f):
        """
        Removes emphasis from a field if it exists.
        :param f: field
        :return: field without emphasis
        """
        if isinstance(f, Emph):
            return f.fld
        return f


class FieldEditorWidget(QWidget):
    """
    Editor for frame's layers / protocols
    """

    infoRequested = Signal(str, str, str)  # layer name, field, text

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.pages = {}  # dictionary to store editor page of the frames layers
        self._create_empty_page()
        self.switch_to('None')

    def _create_empty_page(self):
        """
        Creates an empty page used when no layer is selected.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        label = QLabel("Select a protocol / layer to edit it's fields")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.stack.addWidget(container)
        self.pages['None'] = container

    def clear(self):
        """
        Calls function to remove protocol page on every layer. Empty page remains.
        """
        to_remove = [name for name in self.pages.keys() if name != 'None']  # necessary because _remove_protocol_page alters self.pages
        for name in to_remove:
            self._remove_protocol_page(name)

    def load_editor(self, layers):
        """
        Calls function to create editor page for every layer. Automatically switches to empty page (no layer selected)
        :param layers: layers to create editor page for
        """
        for layer in layers:
            self._create_protocol_page(layer)

        self.switch_to('None')

    def update_editor(self, layers):
        """
        Calls function to create protocol page for every layer that doesn't have one yet.
        :param layers: layers to update editor page for
        """
        for layer in layers:
            if layer.name not in self.pages:
                self._create_protocol_page(layer)

    def _create_protocol_page(self, layer):
        """
        Creates editor page for specific layer. Page gets added to pages dictionary.
        :param layer: layer to create editor page for
        """

        layer_name = layer.name
        cls_name = layer.__class__.__name__
        log.debug(f'creating protocol page for {layer_name}')

        # Scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Container
        content_widget = QWidget()
        content_widget.setObjectName("editor_scroll_content")
        form_layout = QFormLayout(content_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        # title
        title = QLabel(layer_name)
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333; margin-bottom: 10px;")
        form_layout.addRow(title)

        for f in layer.fields_desc:
            val = layer.getfieldval(f.name)

            row_container = QWidget()
            row_layout = QHBoxLayout(row_container)
            row_layout.setContentsMargins(0, 2, 0, 2)

            lbl = QLabel(f.name)
            lbl.setFixedWidth(100)

            field_widget = ScapyFieldRow(cls_name,f, val)

            field_widget.infoRequested.connect(self.infoRequested)

            row_layout.addWidget(lbl)
            row_layout.addWidget(field_widget)

            form_layout.addRow(row_container)

        scroll_area.setWidget(content_widget)
        self.stack.addWidget(scroll_area)
        self.pages[cls_name] = scroll_area
        self.switch_to('None')

    def switch_to(self, protocol_name):
        """
        Switches editor page to desirable protocol / layer
        :param protocol_name: name
        """
        log.debug('SWITCHING TO ' + protocol_name)
        if protocol_name in self.pages:
            widget = self.pages[protocol_name]
            self.stack.setCurrentWidget(widget)

    def _remove_protocol_page(self, protocol_name):
        """
        Removes protocol page for specified protocol / layer
        :param protocol_name: name
        """
        if protocol_name in self.pages:
            widget = self.pages[protocol_name]
            self.stack.removeWidget(widget)
            widget.deleteLater()
            del self.pages[protocol_name]

    def get_collected_data(self):
        """
        Collects data from editor.
        :return: list of {"layer_class": <layer_name>, "fields": {<field_name> : <field_value>}}
        """

        collected_layers = []

        for layer_name, scroll_area in self.pages.items():
            if layer_name == 'None':
                continue

            layer_data = {
                "layer_class": layer_name,
                "fields": {}
            }

            content_widget = scroll_area.widget()
            if not content_widget:
                continue

            layout = content_widget.layout()
            if not layout:
                continue

            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget()

                if widget and isinstance(widget, QWidget):
                    scapy_row = widget.findChild(ScapyFieldRow)

                    if scapy_row:
                        field_name = scapy_row.field_desc.name
                        value = scapy_row.get_value()
                        layer_data["fields"][field_name] = value

            collected_layers.append(layer_data)

        return collected_layers