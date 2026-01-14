from PySide6.QtCore import QObject, Signal
from core.input_output.pcap import write_pcap_file, read_pcap_generator
import logging
log = logging.getLogger(__name__)

class FramePageController(QObject):

    onFrameSelected = Signal(int)
    sendRequest = Signal(list)
    openFuzzingRequest = Signal(int)

    def __init__(self, frame_page, frame_manager):
        super().__init__()

        self._frame_page = frame_page
        self._frame_manager = frame_manager

        self._frame_page.addNewFrame.connect(self._on_new_frame_added_request)
        self._frame_page.frameSelected.connect(self.onFrameSelected)
        self._frame_page.sendRequest.connect(self.sendRequest)
        self._frame_page.framesSaved.connect(self._save_to_pcap_requested)
        self._frame_page.openFuzzingRequest.connect(self.openFuzzingRequest)


    def _save_to_pcap_requested(self, file_path, ids):
        write_pcap_file(file_path, ids, self._frame_manager)

    def _on_new_frame_added_request(self, file_path, group_id):
        """
        When user want to add new frames.
        If filepath exists -> Batch load from PCAP.
        If empty -> Add single empty frame.
        :param file_path: filepath to pcap file
        :param group_id: target group id
        """
        if file_path:
            new_frames = []
            for packet in read_pcap_generator(file_path):
                frame = self._frame_manager.add(packet)
                new_frames.append(frame)

            if new_frames:
                self._frame_page.add_frames(new_frames, group_id)
                log.info(f"Loaded {len(new_frames)} frames from {file_path}")
        else:
            new_frame = self._frame_manager.add(None)
            self._frame_page.add_frame(new_frame, group_id)

    def add_fuzzed_frames(self, frame_ids, group_id):
        """
        Called by MainController (or Fuzzing Logic) when new packets are generated.
        :param frame_ids: list of int (IDs of newly created frames in DB)
        :param group_id: UUID of the group where they should be displayed
        """
        frames_to_add = []

        for fid in frame_ids:
            frame = self._frame_manager.get_frame(fid)
            if frame:
                frames_to_add.append(frame)

        if frames_to_add:
            self._frame_page.add_frames(frames_to_add, group_id)
            log.info(f"Added {len(frames_to_add)} fuzzed frames to group {group_id}")
