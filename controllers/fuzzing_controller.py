from PySide6.QtCore import QObject, Signal
import logging

from PySide6.QtWidgets import QInputDialog

from core.fuzzing.fuzzing_engine import FuzzingEngine

log = logging.getLogger(__name__)

class FuzzingController(QObject):

    fuzzingFinished = Signal(list, str)
    fuzzingExit = Signal()

    def __init__(self, fuzzing_page, frame_manager):
        super().__init__()

        self._fuzzing_page = fuzzing_page
        self._frame_manager = frame_manager

        self._engine = FuzzingEngine(frame_manager)
        self._current_frame_id = None
        self._connect_signals()

    def _connect_signals(self):

        self._fuzzing_page.backClicked.connect(self._on_back_clicked)
        self._fuzzing_page.generateClicked.connect(self._on_fuzz_generate)

    def load_fuzzer(self, frame_id):

        frame = self._frame_manager.get_frame(frame_id)
        if not frame:
            return False

        scapy_pkt = frame.scapy
        if not scapy_pkt:
            log.warning(f"Can not fuzz frame #{frame_id} because it has no layers")
            return False

        info_text = f"Frame #{frame.id}"
        self._current_frame_id = frame_id
        self._fuzzing_page.set_frame(info_text, scapy_pkt)
        return True

    def _on_back_clicked(self):
        self._fuzzing_page.reset_fuzzer()
        self.fuzzingExit.emit()

    def _on_fuzz_generate(self):
        if self._current_frame_id is None:
            return

        config = self._fuzzing_page.get_config()

        default_name = f"Fuzz_{config['target_field']}_{config['strategy'][:3]}"
        group_name, ok = QInputDialog.getText(
            self._fuzzing_page, "Group Name", "Create group for results:", text=default_name
        )
        if not ok:
            return

        new_ids = self._engine.execute_fuzzing(self._current_frame_id, config)

        if new_ids:
            self.fuzzingFinished.emit(new_ids, group_name)
        else:
            log.warning("Fuzzing engine returned 0 frames.")