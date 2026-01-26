from PySide6.QtCore import QObject, Slot
from core.input_output.interfaces import get_interfaces
import logging

log = logging.getLogger(__name__)


class ReceiverController(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main_ctrl = main_controller
        self._receiver_page = None
        self._engine = None

        self._is_listening = False

    def set_view(self, receiver_page):
        self._receiver_page = receiver_page
        self._connect_signals()
        self._init_data()

    def _connect_signals(self):
        self._receiver_page.configSaved.connect(self._on_config_saved)
        self._receiver_page.syncRequested.connect(self._on_sync_requested)
        self._receiver_page.clearRequested.connect(self._on_clear_requested)
        self._receiver_page.saveRequested.connect(self._on_save_pcap_requested)

    def _init_data(self):
        try:
            self._receiver_page.set_interfaces(get_interfaces())
        except Exception as e:
            log.error(f"Failed to load interfaces: {e}")


    @Slot(dict)
    def _on_config_saved(self, config):

        local_port = config.get('local_port')
        local_iface = config.get('local_iface')

        log.info(f"Applying local config: Interface={local_iface}, Port={local_port}")

        # TODO: restart receiver
        # if self._engine:
        #     self._engine.stop()
        # self._engine = ReceiverEngine(port=local_port, iface=local_iface)
        # self._engine.start()

        log.info("Local Listener updated")

    @Slot(dict)
    def _on_sync_requested(self, config):

        remote_ip = config.get('remote_ip')
        remote_port = config.get('remote_port')

        log.info(f"Syncing with remote device at {remote_ip}:{remote_port}...")

        # TODO: implement this

        import random
        success = random.choice([True, False])

        if success:
            self._receiver_page.set_sync_status(True, "Connected")
        else:
            self._receiver_page.set_sync_status(False, "Connection Refused")

    @Slot()
    def _on_clear_requested(self):
        self._receiver_page.clear_table()

    @Slot()
    def _on_save_pcap_requested(self):
        log.info("Export PCAP requested (Not implemented yet)")


    def handle_incoming_packet(self, packet_dict):
        self._receiver_page.add_packet_to_table(packet_dict)
        # self._view.show_capture()