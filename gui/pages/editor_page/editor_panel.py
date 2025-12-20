from PySide6.QtWidgets import (
    QWidget, QVBoxLayout,
    QFormLayout, QFrame, QScrollArea,
    QStackedWidget, QLabel, QLineEdit
)

from PySide6.QtCore import Qt, Signal, Slot

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

    def create_protocol_form(self, protocol_name, fields_data):
        """
        Creates new editor page for protocol
        :param protocol_name: Protocol name (key)
        :param fields_data: ...
        """

        if protocol_name in self.pages:
            self.remove_protocol_page(protocol_name)

        #scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        #container
        content_widget = QWidget()

        #form layout
        form_layout = QFormLayout(content_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)

        #title
        title = QLabel(protocol_name)
        # title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        form_layout.addRow(title)

        #fields
        for label_text, default_value, placeholder in fields_data:
            label = QLabel(label_text)
            input_field = QLineEdit()
            input_field.setText(str(default_value))
            input_field.setPlaceholderText(placeholder)

            form_layout.addRow(label, input_field)

        scroll_area.setWidget(content_widget)

        self.stack.addWidget(scroll_area)
        self.pages[protocol_name] = scroll_area

        print(f"Editor for '{protocol_name}' created.")

    def switch_to(self, protocol_name):
        """
        Switches editor page to desirable protocol
        :param protocol_name: name
        """
        if protocol_name in self.pages:
            widget = self.pages[protocol_name]
            self.stack.setCurrentWidget(widget)
            print(f"Switched to: {protocol_name}")

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
