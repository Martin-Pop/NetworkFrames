from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QFormLayout, QFrame, QScrollArea,
    QStackedWidget, QLabel, QLineEdit,
    QGroupBox, QComboBox, QGridLayout, QCheckBox, QSpinBox, QHBoxLayout, QDoubleSpinBox
)

from scapy.fields import *
import logging
log = logging.getLogger(__name__)

class ScapyFieldRow(QWidget):
    """
        A unified row widget containing:
        1. Main Editor (Editable - Type specific)
        2. Hex View (Read-only)
        3. Binary View (Read-only)
        4. Size Label (Static info)
        """

    def __init__(self, field_desc, current_val, parent=None):
        super().__init__(parent)
        self.field_desc = field_desc
        self.current_val = current_val

        # Main Layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        self.mid_container = QWidget(self)

        self.mid_layout = QVBoxLayout(self.mid_container)
        self.mid_layout.setContentsMargins(0, 0, 0, 0)
        self.mid_layout.setSpacing(10)

        # editor
        self.editor_widget = None

        # hex
        self.hex_display = QLineEdit()
        self.hex_display.setPlaceholderText("HEX")
        self.hex_display.setReadOnly(True)
        self.hex_display.setFixedWidth(80)
        #self.hex_display.setStyleSheet("QLineEdit { background-color: #f0f0f0; color: #555; }")

        self.bin_display = QLineEdit()
        self.bin_display.setPlaceholderText("BIN")
        self.bin_display.setReadOnly(True)
        # self.bin_display.setFixedWidth(120)
        #self.bin_display.setStyleSheet("QLineEdit { background-color: #f0f0f0; color: #555; }")

        # size label
        size_str = self._get_size_string(field_desc)
        self.size_label = QLabel(size_str)
        # self.size_label.setStyleSheet("color: #888; font-size: 10px;")
        # self.size_label.setFixedWidth(75)

        # factory
        self._init_editor_by_type()

        self.mid_layout.addWidget(self.bin_display)

        self.layout.addWidget(self.mid_container)
        self.layout.addWidget(self.hex_display)
        self.layout.addWidget(self.size_label)

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
        f = self.field_desc
        val = self.current_val

        log.debug(f'{f.name} {type(f)} {val}')

        #remove emph wrapper
        if isinstance(f, Emph):
            f = f.fld

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

    #setup methods
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

        self.editor_widget = spin_widget #make spinbox main

        # combobox helper
        combo_widget = QComboBox()
        combo_widget.addItem("Custom / Unknown", -1) #index 0


        #sorted_options = sorted(options.items(), key=lambda item: item[0])
        for v, name in options.items():
            combo_widget.addItem(f"{name} ({v})", v)

        #sync
        def on_combo_changed(idx):
            data = combo_widget.currentData()
            if data != -1:  #ignore -1 (unknown/custom)
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
                combo_widget.setCurrentIndex(0) # unknown / custom
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
        #TODO: add validation
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
        """Updates Hex/Bin based on integer value."""
        try:
            int_val = int(val)
            self.hex_display.setText(f"0x{int_val:X}")
            self.bin_display.setText(f"{int_val:b}")
        except:
            self.hex_display.setText("Err")

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
        """Updates Hex based on string/IP"""
        try:
            b = text.encode('utf-8')
            h = b.hex().upper()
            self.hex_display.setText(h)
            self.bin_display.setText(f"-")  # Bin for string too long
        except:
            self.hex_display.setText("Err")

    # size calc
    def _get_size_string(self, f):
        """
        Determines the size of the field in bits or bytes.
        """
        # explicit size in bits
        if isinstance(f, BitField):
            return f"{f.size} bits"

        # bytes
        if isinstance(f, ByteField): return "1 byte"  # 8 bits
        if isinstance(f, ShortField): return "2 bytes"  # 16 bits
        if isinstance(f, IntField): return "4 bytes"  # 32 bits
        if isinstance(f, LongField): return "8 bytes"  # 64 bits
        if isinstance(f, IPField): return "4 bytes"
        if isinstance(f, MACField): return "6 bytes"

        # from sz (struct size)
        if hasattr(f, "sz"):
            return f"{f.sz} bytes"

        return "Var"  # fallback

    def _get_max_value(self, f):

        if isinstance(f, BitField):
            return (2 ** f.size) - 1

        if hasattr(f, "sz"):
            return (2 ** (f.sz * 8)) - 1

        return (2 ** 64) - 1


class FieldEditorWidget(QWidget):
    """
    Editor for frame's layers / protocols
    """

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.pages = {} # dictionary to store editor page of the frames layers
        self._create_empty_page()
        self.switch_to('None')

    def _create_empty_page(self):
        """
        Creates an empty page used when no layer is selected.
        """
        container = QWidget()
        layout = QVBoxLayout(container)
        label = QLabel('Please select protocol to edit')
        layout.addWidget(label)

        self.stack.addWidget(container)
        self.pages['None'] = container

    def clear(self):
        """
        Calls function to remove protocol page on every layer. Empty page remains.
        """
        to_remove = [name for name in self.pages.keys() if name != 'None'] #necessary because _remove_protocol_page alters self.pages
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

            field_widget = ScapyFieldRow(f, val)

            row_layout.addWidget(lbl)
            row_layout.addWidget(field_widget)

            form_layout.addRow(row_container)

        scroll_area.setWidget(content_widget)
        self.stack.addWidget(scroll_area)
        self.pages[cls_name] = scroll_area

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
