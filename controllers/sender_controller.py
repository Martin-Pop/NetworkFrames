from PySide6.QtCore import QObject, Signal

from core.sender_worker import SenderWorker
from core.input_output.interfaces import get_interfaces
import logging
log = logging.getLogger(__name__)

class SenderController(QObject):
    senderClosed = Signal()
    remoteReportReceived = Signal(list)

    def __init__(self, sender_page, frame_manager):
        super().__init__()
        self._sender_page = sender_page
        self._frame_manager = frame_manager

        self._worker = None
        self._identification = ''
        self._current_frame_ids = []
        self._current_receiver_config = {"remote_ip": '127.0.0.1', "remote_port": 5000}

        # signals
        self._sender_page.startClicked.connect(self._start_sending)
        self._sender_page.stopClicked.connect(self._stop_sending)
        self._sender_page.backClicked.connect(self._close_sender)
        self._sender_page.pauseClicked.connect(self._toggle_sending)

        self._sender_page.set_interfaces(get_interfaces())

    def load_frames(self, ids, group_name):
        """
        Saves the frame ids and updates UI
        :param ids: ids to save
        :param group_name: name of group in which frames are
        """

        log.debug(f"Loading: {ids}")
        self._current_frame_ids = ids

        if not ids:
            self._identification = "None selected"
            self._sender_page.set_frame_info(self._identification, '')
            return

        if len(ids) == 1:
            frame = self._frame_manager.get_frame(ids[0])
            if frame:
                self._identification = ids[0]
                self._sender_page.set_frame_info(self._identification, str(frame.get_info().get('info', 'Info unavailable')))
        else:
            self._identification = group_name if group_name else 'mixed selection'
            self._sender_page.set_frame_info(self._identification, f"({len(ids)}) frames")

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
                continue
            scapy_pkts.append(frame.scapy)

        # get settings
        config = self._sender_page.get_config()
        iface = config.get("interface")
        count = config.get("count")
        interval = config.get("interval")
        use_receiver = config.get("use_receiver")

        log.debug(f"Starting sender: frame_count={len(scapy_pkts)}, Iface={iface}, Count={count}")

        self._worker = SenderWorker(scapy_pkts, iface, count, interval, self._current_receiver_config if use_receiver else None)
        self._worker.packetSent.connect(self._sender_page.update_counter)
        self._worker.finished.connect(self._on_sending_finished)
        self._worker.errorOccurred.connect(self._on_worker_error)
        self._worker.remoteReportReceived.connect(self.remoteReportReceived.emit)

        self._sender_page.set_running_state(True)
        self._worker.start()

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

    def sync_current_with_removed_frames(self, ids):
        """
        Syncs current frames that are
        :param ids:
        :return:
        """
        if not set(ids).isdisjoint(self._current_frame_ids):
            new_ids = list(set(self._current_frame_ids) - set(ids))
            self.load_frames(new_ids, self._identification)

    def update_remote_config_status(self, config):
        self._current_receiver_config = config
        self._sender_page.update_receiver_status(config)