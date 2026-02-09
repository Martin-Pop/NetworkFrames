import socket
import logging
import json
from PySide6.QtCore import QThread, Signal

log = logging.getLogger(__name__)


class ReceiverEngine(QThread):
    """
    Worker thread that acts as a Control Server.
    It accepts a connection from a Remote Device, sends commands (START/STOP),
    and receives JSON reports containing captured packets.
    """
    serverStarted = Signal(str, int)
    serverStopped = Signal()
    clientConnected = Signal(str, int)
    clientDisconnected = Signal()

    dataReceived = Signal(bytes)
    reportReceived = Signal(list)
    errorOccurred = Signal(str)

    def __init__(self, port, iface_ip="0.0.0.0"):
        super().__init__()
        self.port = port
        self.iface_ip = iface_ip
        self._is_running = False
        self._server_socket = None
        self._active_conn = None

    def run(self):
        self._is_running = True
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._server_socket.bind((self.iface_ip, self.port))
            self._server_socket.listen(1)

            self.serverStarted.emit(self.iface_ip, self.port)

            while self._is_running:
                try:
                    self._server_socket.settimeout(1.0)
                    conn, addr = self._server_socket.accept()

                    log.info(f"Remote Device connected from {addr}")
                    self.clientConnected.emit(addr[0], addr[1])
                    self._active_conn = conn

                    with conn:
                        while self._is_running:
                            # We expect larger JSON data
                            try:
                                data = conn.recv(16384)
                                if not data:
                                    break

                                self._process_incoming_data(data)

                            except OSError:
                                break

                    self._active_conn = None
                    self.clientDisconnected.emit()
                    log.info(f"Remote Device {addr} disconnected")

                except socket.timeout:
                    continue
                except OSError as e:
                    if self._is_running:
                        log.error(f"Socket error: {e}")
                    break

        except Exception as e:
            log.error(f"Receiver Engine Error: {e}")
            self.errorOccurred.emit(str(e))
        finally:
            self.stop()

    def _process_incoming_data(self, data):
        """
        Parses raw bytes as JSON and emits signal if it's a valid report.
        """
        try:
            msg = data.decode('utf-8')
            payload = json.loads(msg)

            if payload.get('type') == 'REPORT':
                packets = payload.get('packets', [])
                log.info(f"Received report with {len(packets)} packets")
                self.reportReceived.emit(packets)

            elif payload.get('status') == 'LISTENING':
                log.info("Remote Device confirmed: Listening started")

        except json.JSONDecodeError:
            log.warning(f"Received invalid JSON data: {data[:50]}...")
        except Exception as e:
            log.error(f"Error processing data: {e}")

    def send_command(self, cmd_type, **kwargs):
        """
        Sends a JSON command to the connected Remote Device.
        Example: send_command("START", filter="tcp")
        """
        if not self._active_conn:
            log.warning("Cannot send command: No Remote Device connected")
            return

        payload = {
            "cmd": cmd_type,
            **kwargs
        }

        try:
            data = json.dumps(payload).encode('utf-8')
            self._active_conn.sendall(data)
            log.info(f"Sent command: {cmd_type}")
        except Exception as e:
            log.error(f"Failed to send command: {e}")

    def stop(self):
        self._is_running = False
        if self._active_conn:
            try:
                self._active_conn.close()
            except:
                pass
        if self._server_socket:
            try:
                self._server_socket.close()
            except:
                pass
        self._server_socket = None
        self.serverStopped.emit()