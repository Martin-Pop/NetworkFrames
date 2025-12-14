from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton,QDialog, QComboBox
)

from PySide6.QtCore import Qt, Signal, Slot

class ProtocolStackWidget(QWidget):
    protocolSelected = Signal(str)

    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Protocol stack editor
        self.editor = ProtocolEditorDialog(self)

        self.button_container = QVBoxLayout()
        self.button_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(lambda: self.editor.exec())

        self.main_layout.addWidget(self.edit_button)
        self.main_layout.addLayout(self.button_container)
        # self.main_layout.addStretch()

    def _clear_buttons(self):
        while self.button_container.count():
            item = self.button_container.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def update_buttons(self, protocol_list):

        self._clear_buttons()
        self.button_container.addStretch()

        for protocol in reversed(protocol_list):
            btn = QPushButton(protocol)
            btn.clicked.connect(lambda checked, p=protocol: self._on_protocol_clicked(p))
            self.button_container.addWidget(btn)

    @Slot(str)
    def _on_protocol_clicked(self, protocol_name):
        self.protocolSelected.emit(protocol_name)


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

    def rebuild(self, protocol_list):
        self._clear_layout()
        self.editor_container.addStretch()

        reversed_indexes = range(len(protocol_list) - 1, -1, -1)

        for i, protocol in zip(reversed_indexes, reversed(protocol_list)):
            current, other = protocol

            if current is None and other is None:
                widget = QPushButton('Add')
                widget.clicked.connect(lambda checked, index=i: self.stackUpdated.emit((index, None)))
            else:
                widget = QComboBox()
                widget.addItems(other)
                widget.setPlaceholderText('Select protocol')
                if current is None:
                    widget.setCurrentIndex(-1)
                else:
                    widget.setCurrentText(current)

                widget.currentIndexChanged.connect(
                    lambda idx, combo=widget, index=i: self._on_protocol_selected(combo, index))

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