from PySide6.QtCore import QObject, Slot
from core.input_output.interfaces import get_interfaces
from core.receiver_engine import ReceiverEngine
import logging
import socket

log = logging.getLogger(__name__)


class ReceiverController(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main_ctrl = main_controller
        self._receiver_page = None
        self._engine = None
        self._client_count = 0

    def set_view(self, receiver_page):
        self._receiver_page = receiver_page
        self._connect_signals()
        self._init_data()

    def _connect_signals(self):
        self._receiver_page.startListening.connect(self._on_start_listening)
        self._receiver_page.stopListening.connect(self._on_stop_listening)

        self._receiver_page.syncRequested.connect(self._on_sync_requested)
        self._receiver_page.clearRequested.connect(self._on_clear_requested)
        self._receiver_page.saveRequested.connect(self._on_save_pcap_requested)

    def _init_data(self):
        try:
            self._receiver_page.set_interfaces(get_interfaces())
        except Exception as e:
            log.error(f"Failed to load interfaces: {e}")


    @Slot(dict)
    def _on_start_listening(self, config):
        """
        Starts the ReceiverEngine with the provided config.
        :param config: configuration with ip and port
        """
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

    @Slot()
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
            log.debug(f"Received data ({len(data)} bytes): {msg}")

            #mock for now
            fake_packet_data = {
                "time": "Now",
                "src": "Remote",
                "dst": "Local",
                "protocol": "TCP/RAW",
                "len": len(data),
                "info": msg[:50] + "..." if len(msg) > 50 else msg
            }
            self.handle_incoming_packet(fake_packet_data)

        except Exception as e:
            log.error(f"Error processing data: {e}")


    @Slot(dict)
    def _on_sync_requested(self, config):
        """
        Tries to connect to the Remote Device defined in settings to verify reachability.
        :param config: ip and port
        """
        remote_ip = config.get('remote_ip')
        remote_port = config.get('remote_port')

        log.info(f"Syncing (Checking connection) with remote device at {remote_ip}:{remote_port}...")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)

        try:
            result = sock.connect_ex((remote_ip, remote_port))
            if result == 0:
                self._receiver_page.set_sync_status(True, "Connected / Available")
                log.info("Sync success!")
            else:
                self._receiver_page.set_sync_status(False, f"Unreachable (Err: {result})")
                log.warning("Sync failed: Host unreachable or connection refused")
        except Exception as e:
            self._receiver_page.set_sync_status(False, f"Error: {str(e)}")
            log.error(f"Sync exception: {e}")
        finally:
            sock.close()

    @Slot()
    def _on_clear_requested(self):
        self._receiver_page.clear_table()

    @Slot()
    def _on_save_pcap_requested(self):
        log.info("Export PCAP requested (Not implemented yet)")

    def handle_incoming_packet(self, packet_dict):
        self._receiver_page.add_packet_to_table(packet_dict)