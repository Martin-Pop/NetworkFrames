from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout,
    QPushButton, QDialog, QComboBox, QFrame, QCompleter
)
from PySide6.QtCore import Qt, Signal
import logging
log = logging.getLogger(__name__)


class SearchableComboBox(QComboBox):
    """
    Custom QComboBox that fixes the PySide6 'flash and close' bug.
    It uses a custom QCompleter and safely detaches it while the
    main dropdown is open, preventing popups from fighting for focus.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self._custom_completer = QCompleter(self)
        self._custom_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._custom_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._custom_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        self._custom_completer.setModel(self.model())
        self.setCompleter(self._custom_completer)

    def showPopup(self):
        """
        Temporarily detaches the completer before the main dropdown opens.
        This stops the completer from stealing focus and closing the menu.
        """
        self.setCompleter(None)
        super().showPopup()

    def hidePopup(self):
        """
        Restores the custom completer once the main dropdown is closed,
        so typing works again.
        """
        super().hidePopup()
        self.setCompleter(self._custom_completer)

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
    layerAdded = Signal(int)
    layerRemoved = Signal(int)
    layerUpdated = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Stack editor")
        self.setGeometry(100, 100, 600, 400)

        main_layout = QVBoxLayout(self)

        self.editor_container = QVBoxLayout()
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

    def rebuild(self, stack, can_add_top=True, can_add_bottom=True):
        self._clear_layout()

        if can_add_top:
            btn_add_top = QPushButton("+ Add Upper Layer")
            btn_add_top.setProperty('styleClass', 'common_button')
            btn_add_top.clicked.connect(lambda: self.layerAdded.emit(len(stack)))
            self.editor_container.addWidget(btn_add_top)

        for i in range(len(stack) - 1, -1, -1):
            node = stack[i]

            row_frame = QFrame()
            row_frame.setObjectName("layer_card")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(5, 5, 5, 5)

            combo = SearchableComboBox()

            if node.options:
                sorted_options = sorted(node.options)
                combo.addItems(sorted_options)

            combo.setPlaceholderText('Select protocol')

            combo.blockSignals(True)
            if node.current is None:
                combo.setCurrentIndex(-1)
            else:
                combo.setCurrentText(node.current)
            combo.blockSignals(False)

            combo.currentIndexChanged.connect(lambda idx, c=combo, index=i: self.layerUpdated.emit(index, c.currentText()))

            remove_btn = QPushButton("X")
            remove_btn.setObjectName("btn_remove_layer")
            remove_btn.clicked.connect(lambda checked, index=i: self.layerRemoved.emit(index))

            if not (i == 0 or i == len(stack) - 1):
                remove_btn.setEnabled(False)

            row_layout.addWidget(combo, 1)
            row_layout.addWidget(remove_btn, 0)
            self.editor_container.addWidget(row_frame)

        if can_add_bottom:
            btn_add_bottom = QPushButton("+ Add Lower Layer")
            btn_add_bottom.setProperty('styleClass', 'common_button')
            btn_add_bottom.clicked.connect(lambda: self.layerAdded.emit(0))
            self.editor_container.addWidget(btn_add_bottom)

    def _clear_layout(self):
        while self.editor_container.count():
            item = self.editor_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()