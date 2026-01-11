from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QDialog, QComboBox, QFrame
)

from PySide6.QtCore import Qt, Signal, Slot
import logging
log = logging.getLogger(__name__)

class ProtocolStackWidget(QFrame):
    protocolSelected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName('protocol_stack_widget')

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Protocol stack editor
        self.editor = ProtocolEditorDialog(self)

        self.button_container = QVBoxLayout()
        self.button_container.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.button_container.setContentsMargins(10,10,10,10)

        self.edit_button = QPushButton("Edit Protocol Stack")
        self.edit_button.setObjectName("protocol_stack_edit_button")
        self.edit_button.clicked.connect(lambda: self.editor.exec())

        main_layout.addWidget(self.edit_button, 1)
        main_layout.addLayout(self.button_container,5)

    def _clear_buttons(self):
        while self.button_container.count():
            item = self.button_container.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def load_buttons(self, protocol_list):

        self._clear_buttons()

        for protocol in reversed(protocol_list):
            btn = QPushButton(protocol)
            btn.setProperty('styleClass', 'common_button')
            btn.clicked.connect(lambda checked, p=protocol: self.protocolSelected.emit(p))
            self.button_container.addWidget(btn)

    def clear(self):
        self._clear_buttons()

class ProtocolEditorDialog(QDialog):
    stackUpdated = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Stack editor")
        self.setGeometry(100, 100, 600, 400)

        main_layout = QVBoxLayout(self)

        self.editor_container = QVBoxLayout()
        self.editor_container.addWidget(QComboBox())
        self.editor_container.addWidget(QComboBox())

        main_layout.addLayout(self.editor_container)
        main_layout.addStretch()

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.save_button.setProperty('styleClass', 'common_button')
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty('styleClass', 'common_button')

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def rebuild(self, stack):

        log.debug('rebuilding stack editor' + str(stack))

        self._clear_layout()
        self.editor_container.addStretch()

        for i in range(len(stack) - 1, -1, -1):
            node = stack[i]
            if node.current is None and node.options is None:
                widget = QPushButton('Add')
                widget.clicked.connect(lambda checked, index=i: self.stackUpdated.emit((index, None)))
            else:
                widget = QComboBox()
                widget.addItems(node.options)
                widget.setPlaceholderText('Select protocol')
                if node.current is None:
                    widget.setCurrentIndex(-1)
                else:
                    widget.setCurrentText(node.current)

                widget.currentIndexChanged.connect(lambda idx, combo=widget, index=i: self._on_protocol_selected(combo, index))

            self.editor_container.addWidget(widget)

    def _on_protocol_selected(self, combo_widget, index):
        selected_text = combo_widget.currentText()
        self.stackUpdated.emit((index, selected_text))

    def _clear_layout(self):
        while self.editor_container.count():
            item = self.editor_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()