from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter,
    QVBoxLayout, QTextEdit, QTabWidget, QLabel
)

from PySide6.QtCore import Qt, Signal

from gui.pages.editor_page.action_panel import ActionPanelWidget
from gui.pages.editor_page.protocol_stack_panel import ProtocolStackWidget
from gui.pages.editor_page.editor_panel import FieldEditorWidget


class EditorPage(QWidget):

    stackUpdated = Signal(tuple)
    stackEditorExit = Signal(int)

    saveActivated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_editor_panel")

        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)

        # ID label
        self.frame_id_label = QLabel('Frame ID:')
        self.frame_id_label.setObjectName("frame_id_label")
        left_layout.addWidget(self.frame_id_label,0)

        # Protocol Stack
        self.protocol_stack_widget = ProtocolStackWidget()
        self.protocol_stack_widget.editor.stackUpdated.connect(self.stackUpdated)
        self.protocol_stack_widget.editor.finished.connect(self.stackEditorExit)
        left_layout.addWidget(self.protocol_stack_widget,1)

        # Info
        self.info_widget = InfoOutputWidget()
        left_layout.addWidget(self.info_widget,0)

        # Action buttons
        self.action_panel_widget = ActionPanelWidget()
        self.action_panel_widget.saveActivated.connect(self.saveActivated)
        left_layout.addWidget(self.action_panel_widget)

        self.right_panel = QWidget()
        self.right_panel.setObjectName("right_editor_panel")

        right_layout = QVBoxLayout(self.right_panel)

        # Protocol field Editor
        self.editor_widget = FieldEditorWidget()
        right_layout.addWidget(self.editor_widget)

        # setup_placeholder(self.right_panel, "Right panel")
        self.protocol_stack_widget.protocolSelected.connect(self.editor_widget.switch_to)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([200, 300])

        main_layout.addWidget(self.splitter)

    def clear_page(self):
        self.protocol_stack_widget.clear()
        self.editor_widget.clear()

    def load_page(self, _id , layers, cls_names):
        self.frame_id_label.setText('Frame ID: ' + str(_id))

        self.protocol_stack_widget.load_buttons(cls_names)
        self.editor_widget.load_editor(layers)

    def update_stack_editor(self, stack):
        self.protocol_stack_widget.editor.rebuild(stack)

    def update_page(self, stack, layers):
        #update stack and field editor
        self.protocol_stack_widget.load_buttons(stack)
        self.editor_widget.update_editor(layers)

    def get_editor_data(self):
        return self.editor_widget.get_collected_data()


class InfoOutputWidget(QTextEdit):
    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setPlaceholderText("Select something to show info")
        self.setObjectName("info_widget")


class PreviewOutput(QTabWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("preview_tabs")
        self.setTabPosition(QTabWidget.TabPosition.South)

        self.hex_preview = QTextEdit()
        self.bin_preview = QTextEdit()

        self.hex_tab = self._create_preview(self.hex_preview, "Hexadecimal...")
        self.bin_tab = self._create_preview(self.bin_preview, "Binary...")

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
