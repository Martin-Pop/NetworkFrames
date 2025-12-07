from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter, QLabel,
    QVBoxLayout, QTextEdit, QPushButton,
    QTabWidget, QDialog, QStackedWidget, QComboBox
)

from PySide6.QtCore import Qt, Signal, Slot

from gui.utils import setup_placeholder

class EditorPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_editor_panel")

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        left_layout.setSpacing(10)

        # Protocol Stack
        self.protocol_stack_widget = ProtocolStackWidget()
        left_layout.addWidget(self.protocol_stack_widget)

        left_layout.addStretch()

        # Preview
        self.preview_widget = PreviewOutput()
        left_layout.addWidget(self.preview_widget)

        # Action buttons
        self.action_panel_widget = ActionPanelWidget()
        left_layout.addWidget(self.action_panel_widget)

        self.right_panel = QWidget()
        self.right_panel.setObjectName("right_editor_panel")
        setup_placeholder(self.right_panel, "Right panel")

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([200, 300])

        main_layout.addWidget(self.splitter)

class PreviewOutput(QTabWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("preview_tabs")
        self.setTabPosition(QTabWidget.TabPosition.South)

        self.hex_preview = QTextEdit()
        self.bin_preview = QTextEdit()

        self.hex_tab = self._create_preview(self.hex_preview,"Hexadecimal...")
        self.bin_tab = self._create_preview(self.bin_preview,"Binary...")

        self.addTab(self.hex_tab, 'hex')
        self.addTab(self.bin_tab, 'bin')

    def _create_preview(self, qtext_edit, placeholder_text):
        tab_page = QWidget()

        layout = QVBoxLayout(tab_page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        qtext_edit.setReadOnly(True)
        qtext_edit.setPlaceholderText(placeholder_text)

        layout.addWidget(qtext_edit)

        return tab_page


class ProtocolStackWidget(QWidget):

    protocolSelected = Signal(str)

    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Protocol stack editor
        self.protocol_stack_editor_widget = ProtocolEditorDialog(self)

        self.button_container = QVBoxLayout()
        self.button_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(lambda: self.protocol_stack_editor_widget.exec())

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

    protocolStackUpdated = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Stack editor")
        self.setGeometry(100,100,600, 400)

        main_layout = QVBoxLayout(self)

        self.editor_container = QVBoxLayout()
        self.editor_container.addWidget(QComboBox())
        self.editor_container.addWidget(QComboBox())

        main_layout.addLayout(self.editor_container)
        main_layout.addStretch()

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.save_button.setProperty('styleClass','common_button')
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setProperty('styleClass','common_button')

        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        main_layout.addLayout(button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def rebuild(self, protocol_list):
        self._clear_layout()
        self.editor_container.addStretch()

        reversed_indexes = range(len(protocol_list)-1 , -1, -1)

        for i,protocol in zip(reversed_indexes, reversed(protocol_list)):
            current, other = protocol

            if current is None and other is None:
                widget = QPushButton('Add')
                widget.clicked.connect(lambda checked, index=i: self.protocolStackUpdated.emit((index, None)))
            else:
                widget = QComboBox()
                widget.addItems(other)
                widget.setPlaceholderText('Select protocol')
                if current is None:
                    widget.setCurrentIndex(-1)
                else:
                    widget.setCurrentText(current)

                widget.currentIndexChanged.connect(lambda idx, combo=widget, index=i: self._on_protocol_selected(combo, index))

            self.editor_container.addWidget(widget)

    def _on_protocol_selected(self, combo_widget, index):
        selected_text = combo_widget.currentText()
        self.protocolStackUpdated.emit((index, selected_text))

    def _clear_layout(self):
        while self.editor_container.count():
            item = self.editor_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


class ActionPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(1,1,1,1)
        main_layout.setSpacing(5)

        self.btn_build = QPushButton("Build")
        self.btn_build.setProperty('styleClass','common_button')
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setProperty('styleClass', 'common_button')

        main_layout.addWidget(self.btn_build)
        main_layout.addStretch()
        main_layout.addWidget(self.btn_clear)