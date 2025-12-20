from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QFormLayout, QFrame, QScrollArea,
    QStackedWidget, QLabel, QLineEdit,
    QGroupBox, QComboBox, QGridLayout, QCheckBox, QSpinBox
)

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
