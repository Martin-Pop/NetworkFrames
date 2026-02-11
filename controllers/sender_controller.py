from PySide6.QtCore import QObject, Signal

from core.sender_worker import SenderWorker
from core.input_output.interfaces import get_interfaces
import logging
log = logging.getLogger(__name__)

class SenderController(QObject):
    senderClosed = Signal()

    def __init__(self, sender_page, frame_manager):
        super().__init__()
        self._sender_page = sender_page
        self._frame_manager = frame_manager

        self._worker = None
        self._current_frame_ids = None

        # signals
        self._sender_page.startClicked.connect(self._start_sending)
        self._sender_page.stopClicked.connect(self._stop_sending)
        self._sender_page.backClicked.connect(self._close_sender)
        self._sender_page.pauseClicked.connect(self._toggle_sending)

        self._sender_page.set_interfaces(get_interfaces())

    def load_frames(self, ids):
        """
        Saves the frame ids and updates UI
        :param ids: ids to save
        :return:
        """
        log.debug(f"Loading: {ids}")
        self._current_frame_ids = ids
        if len(ids) == 1:
            frame = self._frame_manager.get_frame(ids[0])
            if frame:
                self._sender_page.set_frame_info(str(frame.get_info()))
        else:
            self._sender_page.set_frame_info(str(ids))

            # self._sender_page.update_counter(0)
            # self._sender_page.set_running_state(False)

        # self._sender_page.reset_status() #

    def _start_sending(self):
        """
        Starts sending process, gets the frame from frame_manager by saved id
        """
        if not self._current_frame_ids:
            self._sender_page.show_error("No frame selected")
            return


        scapy_pkts = []
        log.debug(self._current_frame_ids)
        for frame_id in self._current_frame_ids:
            frame = self._frame_manager.get_frame(frame_id)
            if not frame or not frame.scapy:
                self._sender_page.show_error("Invalid frame data")
                continue
            scapy_pkts.append(frame.scapy)

        # get settings
        config = self._sender_page.get_config()
        iface = config.get("interface")
        count = config.get("count")
        interval = config.get("interval")

        log.debug(f"Starting sender: frame_count={len(scapy_pkts)}, Iface={iface}, Count={count}")

        self._worker = SenderWorker(scapy_pkts, iface, count, interval)
        self._worker.packetSent.connect(self._sender_page.update_counter)
        self._worker.finished.connect(self._on_sending_finished)
        self._worker.errorOccurred.connect(self._on_worker_error)

        self._sender_page.set_running_state(True)
        self._worker.start()

        # self._sender_page.set_running_state(True)
        # self._sender_page.update_counter(0)

    def _stop_sending(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()

    def _toggle_sending(self):
        if self._worker:
            is_paused = self._worker.toggle_pause()
            self._sender_page.set_pause_state(is_paused)

    def _on_sending_finished(self):
        self._sender_page.set_running_state(False)
        self._worker = None
        log.debug("Worker finished job.")

    def _on_worker_error(self, msg):
        log.debug(msg)
        self._sender_page.show_error(msg)

    def _close_sender(self):
        self._stop_sending()
        self.senderClosed.emit()