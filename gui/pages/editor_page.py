from PySide6.QtWidgets import (
QWidget, QHBoxLayout, QSplitter, QLabel,
QVBoxLayout, QTextEdit, QPushButton,
QTabWidget
)

from PySide6.QtCore import Qt

class EditorPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_editor_panel")

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)

        # Protokol Stack
        self.protocol_stack_widget = ProtocolStackWidget()
        left_layout.addWidget(self.protocol_stack_widget)

        # Preview
        self.preview_widget = PreviewOutput()
        left_layout.addWidget(self.preview_widget)

        # Action buttons
        self.action_panel_widget = ActionPanelWidget()
        left_layout.addWidget(self.action_panel_widget)

        self.right_panel = QWidget()
        self.right_panel.setObjectName("right_editor_panel")
        self._setup_placeholder(self.right_panel, "Right panel")


        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([200, 300])

        main_layout.addWidget(self.splitter)

    def _setup_placeholder(self, widget, label_text):
        layout = QVBoxLayout(widget)
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

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
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        self.content_placeholder = QLabel("Protocol Stack Content")
        self.content_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.content_placeholder)
        main_layout.addStretch()


class ActionPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(1,1,1,1)
        main_layout.setSpacing(5)

        self.btn_build = QPushButton("Build Frame")
        self.btn_build.setProperty('styleClass','common_button')
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setProperty('styleClass', 'common_button')
        self.btn_save = QPushButton("Save Config")
        self.btn_save.setProperty('styleClass', 'common_button')

        main_layout.addWidget(self.btn_build)
        main_layout.addWidget(self.btn_clear)
        main_layout.addStretch()
        main_layout.addWidget(self.btn_save)
