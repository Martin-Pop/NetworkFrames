from PySide6.QtCore import QObject, Signal
import logging

log = logging.getLogger(__name__)

class FuzzingController(QObject):

    fuzzingExit = Signal()

    def __init__(self, fuzzing_page, frame_manager):
        super().__init__()

        self._fuzzing_page = fuzzing_page
        self._frame_manager = frame_manager
        self._connect_signals()

    def _connect_signals(self):

        self._fuzzing_page.backClicked.connect(self._on_back_clicked)
        self._fuzzing_page.generateClicked.connect(self._on_fuzz_generate)

    def load_fuzzer(self, frame_id):

        frame = self._frame_manager.get_frame(frame_id)
        if not frame:
            return

        scapy_pkt = frame.scapy

        info_text = f"Frame #{frame.id} ({frame.get_info()})"
        self._fuzzing_page.set_frame(info_text, scapy_pkt)

    def _on_back_clicked(self):
        self._fuzzing_page.reset_fuzzer()
        self.fuzzingExit.emit()

    def _on_fuzz_generate(self):

        config = self._fuzzing_page.get_config()
        log.debug(config)
        # call fuzzing here