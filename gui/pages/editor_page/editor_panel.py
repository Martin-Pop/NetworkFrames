from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QFrame, QScrollArea,
    QStackedWidget, QLabel
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QSizePolicy
from gui.pages.editor_page.field_editors.factory import FieldRowFactory
from gui.pages.editor_page.field_editors.base_row import BaseFieldRow
import logging

log = logging.getLogger(__name__)

class FieldEditorWidget(QWidget):
    infoRequested = Signal(str, str, str)

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
        to_remove = [name for name in self.pages.keys() if name != 'None']
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

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_widget.setObjectName("editor_scroll_content")
        form_layout = QFormLayout(content_widget)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        title = QLabel(layer_name)
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #333; margin-bottom: 10px;")
        form_layout.addRow(title)

        for f in layer.fields_desc:
            val = layer.getfieldval(f.name)

            field_widget = FieldRowFactory.create_row(f.name, cls_name, f, val)
            field_widget.infoRequested.connect(self.infoRequested)

            form_layout.addRow(field_widget)

        spacer_widget = QWidget()
        spacer_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        form_layout.addRow(spacer_widget)

        scroll_area.setWidget(content_widget)
        self.stack.addWidget(scroll_area)
        self.pages[cls_name] = scroll_area
        self.switch_to('None')

    def switch_to(self, protocol_name):
        """
        Switches editor page to desirable protocol / layer
        :param protocol_name: name
        """
        # log.debug('SWITCHING TO ' + protocol_name)
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

                if isinstance(widget, BaseFieldRow):
                    field_name = widget.field_desc.name
                    value = widget.get_value()
                    layer_data["fields"][field_name] = value

            collected_layers.append(layer_data)

        return collected_layers