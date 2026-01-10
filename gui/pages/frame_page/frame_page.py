from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout
)

from gui.pages.frame_page.frame_list_panel import FrameListPanel

class FramePage(QFrame):

    frameSelected = Signal(int)  # when frame gets selected
    framesDeleted = Signal(list)  # when frames get deleted
    addNewFrame = Signal(str)  # when new frame is added
    sendRequest = Signal(int)

    def __init__(self, parent=None):
        super(FramePage, self).__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName('frame_page')

        self._frame_list_panel = FrameListPanel()
        #signal chain
        self._frame_list_panel.frameSelected.connect(self.frameSelected)
        self._frame_list_panel.framesDeleted.connect(self.framesDeleted)
        self._frame_list_panel.addNewFrame.connect(self.addNewFrame)
        self._frame_list_panel.sendRequest.connect(self.sendRequest)

        main_layout.addWidget(self._frame_list_panel)

    def add_frame(self, frame):
        self._frame_list_panel.add_frame(frame)