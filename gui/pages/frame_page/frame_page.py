from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QSplitter,
    QVBoxLayout, QTextEdit, QTabWidget, QLabel
)

from gui.pages.frame_page.frame_list_panel import FrameListPanel
from gui.utils import setup_placeholder

class FramePage(QWidget):

    def __init__(self, parent=None):
        super(FramePage, self).__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.frame_list_panel = FrameListPanel()
        main_layout.addWidget(self.frame_list_panel)
        # frl = QHBoxLayout(self.frame_list_panel)
        # frl.addWidget(setup_placeholder("Frame List"))



