from PySide6.QtCore import QObject, Slot, Signal
from core.input_output.interfaces import get_interfaces
from core.receiver_engine import ReceiverEngine
from core.remote_client import RemoteClient, ConnectionWorker
import logging

log = logging.getLogger(__name__)


class ReceiverController(QObject):
    remoteConnectionChanged = Signal(bool, str, int)

    def __init__(self, main_controller):
        super().__init__()
        self.main_ctrl = main_controller
        self._receiver_page = None
        self._engine = None
        self._client_count = 0

        self._remote_client = RemoteClient()
        self._conn_worker = None

    def set_view(self, receiver_page):
        self._receiver_page = receiver_page
        self._connect_signals()
        self._init_data()

    def _connect_signals(self):
        self._receiver_page.startListening.connect(self._on_start_listening)
        self._receiver_page.stopListening.connect(self._on_stop_listening)

        self._receiver_page.clearRequested.connect(self._on_clear_requested)
        self._receiver_page.saveRequested.connect(self._on_save_pcap_requested)

        self._receiver_page.pingRequested.connect(self._on_ping_requested)
        # self._receiver_page.remoteConfigChanged.connect(self._on_remote_config_changed)

        # self._remote_client.connectionLost.connect(self._on_connection_lost)

    def _init_data(self):
        try:
            self._receiver_page.set_interfaces(get_interfaces())
        except Exception as e:
            log.error(f"Failed to load interfaces: {e}")

    def _on_start_listening(self, config):
        local_port = config.get('local_port')
        local_iface_name = config.get('local_iface')
        bind_ip = "0.0.0.0"

        try:
            all_interfaces = get_interfaces()
            selected_iface = next((i for i in all_interfaces if i['name'] == local_iface_name), None)
            if selected_iface and selected_iface.get('ips'):
                bind_ip = selected_iface['ips'][1]

        except Exception as e:
            log.warning(f"Could not resolve IP for interface {local_iface_name}, defaulting to 0.0.0.0: {e}")

        if self._engine:
            self._engine.stop()
            self._engine.wait()

        self._client_count = 0
        log.debug(f"Starting ReceiverEngine on {bind_ip}:{local_port}")
        self._engine = ReceiverEngine(port=local_port, iface_ip=bind_ip)

        self._engine.serverStarted.connect(self._on_server_started)
        self._engine.serverStopped.connect(self._on_server_stopped)
        self._engine.clientConnected.connect(self._on_client_connected)
        self._engine.dataReceived.connect(self._on_data_received)
        self._engine.errorOccurred.connect(self._on_engine_error)

        self._engine.start()

    def _on_stop_listening(self):
        """
        Stops the ReceiverEngine.
        """
        if self._engine:
            self._engine.stop()


    def _on_server_started(self, ip, port):
        log.info(f"Server started on {ip}:{port}")
        self._receiver_page.set_listener_status(True, 0)

    def _on_server_stopped(self):
        self._client_count = 0
        self._receiver_page.set_listener_status(False, 0)

    def _on_client_connected(self, ip, port):
        self._client_count += 1
        self._receiver_page.set_listener_status(True, self._client_count)

    def _on_engine_error(self, error_msg):
        log.error(f"Engine Error: {error_msg}")
        self._receiver_page.set_listener_status(False, 0)

    def _on_data_received(self, data):
        try:
            msg = data.decode('utf-8', errors='replace')
            log.debug(f"Received {msg}")
        except Exception as e:
            log.error(f"Error processing data: {e}")

    def _on_ping_requested(self, ip, port):
        success = self._remote_client.ping_host(ip, port)
        self._receiver_page.set_ping_result(success)
        if success:
            log.info(f"Ping {ip}:{port} succeeded")
        else:
            log.error(f"Ping {ip}:{port} failed")


    def _on_clear_requested(self):
        self._receiver_page.clear_table()

    def _on_save_pcap_requested(self):
        log.info("Export PCAP requested (Not implemented yet)")

    def handle_incoming_packet(self, packet_dict):
        self._receiver_page.add_packet_to_table(packet_dict)