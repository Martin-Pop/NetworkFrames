from utils.pcap import read_pcap
from PySide6.QtCore import QObject, Signal


class FramePageController(QObject):

    onFrameSelected = Signal(int)

    def __init__(self, frame_page, frame_manager):
        super().__init__()

        self._frame_page = frame_page
        self._frame_manager = frame_manager
        self._frame_page.frame_list_panel.addNewFrame.connect(self._on_new_frame_added)
        self._frame_page.frame_list_panel.frameSelected.connect(self.onFrameSelected)

    def _on_new_frame_added(self, file_path):
        if file_path:
            for packet in read_pcap(file_path):
                new_frame = self._frame_manager.add(packet)
                self._frame_page.frame_list_panel.add_frame(new_frame)
        else:
            new_frame = self._frame_manager.add(None)
            self._frame_page.frame_list_panel.add_frame(new_frame)
