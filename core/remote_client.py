import socket
import json
import logging
from PySide6.QtCore import QObject, Signal, QThread

log = logging.getLogger(__name__)


class ConnectionWorker(QThread):
    """
    Runs the blocking socket connection in a separate thread
    so the GUI doesn't freeze.
    """
    result = Signal(bool, str, int)

    def __init__(self, client, ip, port):
        super().__init__()
        self.client = client
        self.ip = ip
        self.port = port

    def run(self):
        success = self.client.connect_to_host(self.ip, self.port)
        self.result.emit(success, self.ip, self.port)


class RemoteClient(QObject):
    connectionLost = Signal()

    def __init__(self):
        super().__init__()
        self.sock = None
        self.is_connected = False

    def ping_host(self, ip, port):
        """
        Stateless check. Tries to connect and immediately closes.
        Returns True if reachable, False otherwise.
        This does NOT set self.is_connected or self.sock.
        """
        temp_sock = None
        try:
            temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_sock.settimeout(2.0)
            temp_sock.connect((ip, port))
            temp_sock.close()
            return True
        except Exception as e:
            if temp_sock:
                try:
                    temp_sock.close()
                except:
                    pass
            return False

    def connect_to_host(self, ip, port):
        """
        Tries to establish a persistent TCP connection for sending commands.
        """
        self.disconnect_from_host(emit_signal=False)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)  # Standard timeout
            self.sock.connect((ip, port))

            self.is_connected = True
            return True

        except Exception as e:
            log.error(f"Connection failed: {e}")
            self.disconnect_from_host(emit_signal=False)
            return False

    def disconnect_from_host(self, emit_signal=True):
        """
        Closes the socket and resets state.
        :param emit_signal: If True, emits connectionLost signal.
        """
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

        self.sock = None
        was_connected = self.is_connected
        self.is_connected = False

        if was_connected and emit_signal:
            log.debug('Connection lost signal emitted')
            self.connectionLost.emit()

    def send_start_command(self, filter_str="", count=1, interval=0.1):
        """
        Sends START command with capture details.
        Calculates timeout for the receiver based on count * interval.
        """
        if not self.sock or not self.is_connected:
            return False

        # Calculate how long the capture will theoretically take
        # We add a 5-second buffer for network latency/processing
        estimated_duration = 0
        if count > 0:
            estimated_duration = (count * interval) + 5.0
        else:
            # If count is infinite or 0, set a very long timeout (e.g., 1 hour)
            estimated_duration = 3600.0

        try:
            cmd = {
                "cmd": "START",
                "filter": filter_str,
                "count": count,
                "interval": interval,
                "timeout": estimated_duration
            }
            self._send_json(cmd)

            # Wait for confirmation (LISTENING)
            self.sock.settimeout(5.0)
            resp = self._recv_json()

            if resp and resp.get("status") == "LISTENING":
                return True
            return False

        except Exception as e:
            log.error(f"Error sending START: {e}")
            # Connection died, notify controller
            self.disconnect_from_host(emit_signal=True)
            return False

    def send_stop_command(self):
        """
        Sends STOP command and waits for the Frame Report.
        """
        if not self.sock or not self.is_connected:
            return None

        try:
            cmd = {"cmd": "STOP"}
            self._send_json(cmd)

            # Increase timeout for large data transfer
            self.sock.settimeout(15.0)

            # Read potentially large data (report)
            raw_data = b""
            while True:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    raw_data += chunk

                    # Basic check if JSON is likely complete
                    if raw_data.strip().endswith(b"}"):
                        # Try to parse to confirm it's complete
                        json.loads(raw_data)
                        break
                except json.JSONDecodeError:
                    continue  # Not complete yet, keep reading
                except socket.timeout:
                    log.warning("Socket timed out while reading report")
                    break
                except Exception as e:
                    log.error(f"Error reading chunk: {e}")
                    break

            if not raw_data:
                return []

            data = json.loads(raw_data.decode('utf-8'))
            if data.get("type") == "REPORT":
                return data.get("packets", [])
            return []

        except Exception as e:
            log.error(f"Error sending STOP: {e}")
            self.disconnect_from_host(emit_signal=True)
            return None

    def _send_json(self, data):
        msg = json.dumps(data).encode('utf-8')
        self.sock.sendall(msg)

    def _recv_json(self):
        try:
            data = self.sock.recv(4096)
            if not data: return None
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            return None
        except Exception:
            return None