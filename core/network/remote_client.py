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
        except Exception:
            if temp_sock:
                try: temp_sock.close()
                except: pass
            return False

    def connect_to_host(self, ip, port):
        """
        Tries to establish a persistent TCP connection for sending commands.
        """
        self.disconnect_from_host(emit_signal=False)

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
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
            try: self.sock.close()
            except Exception: pass

        self.sock = None
        was_connected = self.is_connected
        self.is_connected = False

        if was_connected and emit_signal:
            self.connectionLost.emit()

    def send_start_command(self, filter_str=""):
        if not self.sock or not self.is_connected:
            return False

        try:
            cmd = {"cmd": "START", "filter": filter_str}
            self._send_json(cmd)
            self.sock.settimeout(5.0)

            resp = self._recv_json()
            if resp and resp.get("status") == "LISTENING":
                return True
            return False

        except Exception as e:
            log.error(f"Error sending START: {e}")
            self.disconnect_from_host(emit_signal=True)
            return False

    def send_pause_command(self):
        if self.sock and self.is_connected:
            try:
                self._send_json({"cmd": "PAUSE"})
            except Exception:
                pass

    def send_resume_command(self):
        if self.sock and self.is_connected:
            try:
                self._send_json({"cmd": "RESUME"})
            except Exception:
                pass

    def send_stop_command(self):
        """
        Sends STOP command and waits for the Frame Report.
        """
        if not self.sock or not self.is_connected:
            return None

        try:
            cmd = {"cmd": "STOP"}
            self._send_json(cmd)

            self.sock.settimeout(15.0)
            raw_data = b""
            while True:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk: break
                    raw_data += chunk
                    if raw_data.strip().endswith(b"}"):
                        try:
                            json.loads(raw_data)
                            break
                        except json.JSONDecodeError:
                            pass
                except socket.timeout:
                    log.warning("Socket timed out while reading report")
                    break
                except Exception as e:
                    log.error(f"Error reading chunk: {e}")
                    break

            if not raw_data: return []
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
        except Exception:
            return None