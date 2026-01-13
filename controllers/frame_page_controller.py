from PySide6.QtCore import QObject, Signal
from core.input_output.pcap import write_pcap_file, read_pcap_generator
import logging
log = logging.getLogger(__name__)

class FramePageController(QObject):

    onFrameSelected = Signal(int)
    sendRequest = Signal(list)

    def __init__(self, frame_page, frame_manager):
        super().__init__()

        self._frame_page = frame_page
        self._frame_manager = frame_manager

        self._frame_page.addNewFrame.connect(self._on_new_frame_added_request)
        self._frame_page.frameSelected.connect(self.onFrameSelected)
        self._frame_page.sendRequest.connect(self.sendRequest)


    def _save_to_pcap_requested(self, file_path, ids):
        write_pcap_file(file_path, ids, self._frame_page)


    def _on_new_frame_added_request(self, file_path, group_id):
        """
        When user want to add new frames, if filepath exists it is loaded from pcap otherwise its new emty frame
        :param file_path: filepath to pcap file
        """
        if file_path:
            for packet in read_pcap_generator(file_path):
                new_frame = self._frame_manager.add(packet)
                self._frame_page.add_frame(new_frame, group_id)
        else:
            new_frame = self._frame_manager.add(None)
            self._frame_page.add_frame(new_frame, group_id)
