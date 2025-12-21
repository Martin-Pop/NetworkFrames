from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QFormLayout, QFrame, QScrollArea,
    QStackedWidget, QLabel, QLineEdit,
    QGroupBox, QComboBox, QGridLayout, QCheckBox, QSpinBox, QHBoxLayout, QDoubleSpinBox
)

from scapy.fields import *

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
        self.bin_display.setFixedWidth(120)
        #self.bin_display.setStyleSheet("QLineEdit { background-color: #f0f0f0; color: #555; }")

        # size label
        size_str = self._get_size_string(field_desc)
        self.size_label = QLabel(size_str)
        # self.size_label.setStyleSheet("color: #888; font-size: 10px;")
        self.size_label.setFixedWidth(50)

        # factory
        self._init_editor_by_type()

        self.layout.addWidget(self.hex_display)
        self.layout.addWidget(self.bin_display)
        self.layout.addWidget(self.size_label)

    def get_value(self):
        """Returns the value from the main editor."""
        if hasattr(self.editor_widget, "currentData"):  # ComboBox
            return self.editor_widget.currentData()
        elif hasattr(self.editor_widget, "value"):  # SpinBox
            return int(self.editor_widget.value())
        elif isinstance(self.editor_widget, QLineEdit):  # String/IP
            return self.editor_widget.text()
        elif hasattr(self, "_get_flags_value"):  # Flags Custom method
            return self._get_flags_value()
        return self.current_val  # Fallback


    # factory init helpers
    def _init_editor_by_type(self):
        f = self.field_desc
        val = self.current_val

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
        self.editor_widget.setRange(0, 2 ** 64)
        self.editor_widget.setGroupSeparatorShown(False)
        self.editor_widget.setValue(int(val) if val is not None else 0)

        self.editor_widget.valueChanged.connect(self._update_from_int)

        self.layout.insertWidget(0, self.editor_widget, 1)
        self._update_from_int(self.editor_widget.value())

    def _setup_enum(self, f, val):
        self.editor_widget = QComboBox()
        options = getattr(f, "i2s", {})

        safe_val = val if val is not None else 0

        for v, name in options.items():
            self.editor_widget.addItem(f"{name} ({v})", v)

        idx = self.editor_widget.findData(safe_val)
        if idx >= 0:
            self.editor_widget.setCurrentIndex(idx)
        else:
            self.editor_widget.addItem(f"Unknown ({safe_val})", safe_val)
            self.editor_widget.setCurrentIndex(self.editor_widget.count() - 1)

        self.editor_widget.currentIndexChanged.connect(lambda: self._update_from_int(self.editor_widget.currentData()))

        self.layout.insertWidget(0, self.editor_widget, 1)
        self._update_from_int(self.editor_widget.currentData())

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

        self.layout.insertWidget(0, self.editor_widget, 1)
        self._update_from_flags()

    def _setup_string(self, f, val):
        print('SETING UP STRING for: ', f, val)
        self.editor_widget = QLineEdit()
        txt = ""
        if val is not None:
            if isinstance(val, bytes):
                txt = val.decode('utf-8', errors='ignore')
            else:
                txt = str(val)
        self.editor_widget.setText(txt)

        self.editor_widget.textChanged.connect(self._update_from_string)

        self.layout.insertWidget(0, self.editor_widget, 1)
        self._update_from_string(txt)

    def _setup_readonly(self, f, val):
        print('setting up readonly for: ', f, val)
        if val is not None:
            try:
                repr_val = f.i2repr(None, val)
            except (AttributeError, TypeError, ValueError):
                repr_val = str(val)
        else:
            repr_val = "None"
        self.editor_widget = QLabel(repr_val)
        self.editor_widget.setStyleSheet("color: gray; font-style: italic;")
        self.layout.insertWidget(0, self.editor_widget, 1)

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
            self.bin_display.setText(f"Len: {len(b)}")  # Bin for string too long
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


class FieldEditorWidget(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        self.pages = {}
        self._create_empty_page()
        self.switch_to('None')

    def _create_empty_page(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        label = QLabel('Please select protocol to edit')
        layout.addWidget(label)

        self.stack.addWidget(container)
        self.pages['None'] = container

    def clear(self):
        to_remove = [name for name in self.pages.keys() if name != 'None']
        for name in to_remove:
            self.remove_protocol_page(name)

    def load_editor(self, data):
        print('loading editor with', data)
        for d in data:
            self.create_protocol_page(d["class_name"], d["layer_name"], d["fields"])

    def update_editor(self, editor_data):
        self.clear()
        self.load_editor(editor_data)

    def load_editor2(self, layers):
        for layer in layers:
            self.create_protocol_page2(layer)

    def update_editor2(self, layers):
        for layer in layers:
            if layer.name not in self.pages:
                self.create_protocol_page2(layer)


    def create_protocol_page2(self, layer):

        layer_name = layer.name
        cls_name = layer.__class__.__name__
        print('creating protocol page 2 for', layer_name)

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

    def create_protocol_page(self, protocol_name, display_name, fields_data):
        print('protocol_name', protocol_name)
        if protocol_name in self.pages:
            self.remove_protocol_page(protocol_name)

        # Scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        #Container
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        #itle
        title = QLabel(display_name)
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333; margin-bottom: 10px;")
        form_layout.addRow(title)

        for field in fields_data:
            f_name = field.get("name", "Unknown")
            f_value = field.get("value")
            f_display = field.get("display_value", "")
            f_type = field.get("type", "text")
            f_options = field.get("options")

            label = QLabel(f_name)
            widget = None

            # Dropdown
            if f_type == "dropdown" and f_options:
                widget = QComboBox()
                for val, text in f_options.items():
                    # save as userData
                    widget.addItem(str(text), val)

                index = widget.findData(f_value)
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    # unknown?
                    widget.addItem(f"Unknown ({f_value})", f_value)
                    widget.setCurrentIndex(widget.count() - 1)

            # 2. FLAGS
            elif f_type == "flags" and isinstance(f_options, list):
                # scapy flag fields returns int
                widget = QGroupBox()
                widget.setStyleSheet("QGroupBox { border: none; }")
                flag_layout = QGridLayout(widget)
                flag_layout.setContentsMargins(0, 0, 0, 0)

                current_flags_int = int(f_value) if f_value is not None else 0

                # checkboxes
                for i, flag_name in enumerate(f_options):
                    chk = QCheckBox(flag_name)

                    mask = 1 << i
                    if current_flags_int & mask:
                        chk.setChecked(True)

                    # Layout (3next to each other)
                    flag_layout.addWidget(chk, i // 3, i % 3)

            # NUM
            elif f_type == "number":
                widget = QSpinBox()
                widget.setRange(0, 2147483647)
                try:
                    widget.setValue(int(f_value))
                except (ValueError, TypeError):
                    widget.setValue(0)

            # IP
            elif f_type == "ip":
                widget = QLineEdit()
                widget.setText(str(f_display))
                # widget.setInputMask("000.000.000.000;_")

            # MAC
            elif f_type == "mac":
                widget = QLineEdit()
                widget.setText(str(f_display))
                # widget.setInputMask("HH:HH:HH:HH:HH:HH;_")

            # Fallback
            else:
                widget = QLineEdit()
                widget.setText(str(f_display))
                widget.setPlaceholderText(str(f_value))

            widget.setProperty("field_name", f_name)
            widget.setProperty("field_type", f_type)

            form_layout.addRow(label, widget)

        scroll_area.setWidget(content_widget)
        self.stack.addWidget(scroll_area)
        self.pages[protocol_name] = scroll_area

        print(f"Page for '{protocol_name}' created.")

    def switch_to(self, protocol_name):

        print('SWITCHING TO', protocol_name)

        """
        Switches editor page to desirable protocol
        :param protocol_name: name
        """
        if protocol_name in self.pages:
            widget = self.pages[protocol_name]
            self.stack.setCurrentWidget(widget)

    def remove_protocol_page(self, protocol_name):
        """
        Removes protocol page from stacked widget
        :param protocol_name: name
        """
        if protocol_name in self.pages:
            widget = self.pages[protocol_name]
            self.stack.removeWidget(widget)
            widget.deleteLater()
            del self.pages[protocol_name]
