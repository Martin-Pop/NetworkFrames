from utils.pcap import read_pcap
from PySide6.QtCore import QObject, Signal


class FramePageController(QObject):

    onFrameSelected = Signal(int)
    sendRequest = Signal(int)

    def __init__(self, frame_page, frame_manager):
        super().__init__()

        self._frame_page = frame_page
        self._frame_manager = frame_manager

        self._frame_page.addNewFrame.connect(self._on_new_frame_added_request)
        self._frame_page.frameSelected.connect(self.onFrameSelected)
        self._frame_page.sendRequest.connect(self.sendRequest)


    def _on_new_frame_added_request(self, file_path):
        """
        When user want to add new frames, if filepath exists it is loaded from pcap otherwise its new emty frame
        :param file_path: filepath to pcap file
        """
        if file_path:
            for packet in read_pcap(file_path):
                new_frame = self._frame_manager.add(packet)
                self._frame_page.add_frame(new_frame)
        else:
            new_frame = self._frame_manager.add(None)
            self._frame_page.add_frame(new_frame)
