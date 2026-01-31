import socket
import logging
from PySide6.QtCore import QThread, Signal

log = logging.getLogger(__name__)


class ReceiverEngine(QThread):
    """
    Worker thread that listens on a TCP port for incoming connections.
    """
    serverStarted = Signal(str, int)  # ip, port
    serverStopped = Signal()
    clientConnected = Signal(str, int)  # ip, port
    dataReceived = Signal(bytes)
    errorOccurred = Signal(str)

    def __init__(self, port, iface_ip="0.0.0.0"):
        super().__init__()
        self.port = port
        self.iface_ip = iface_ip
        self._is_running = False
        self._server_socket = None

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

                    log.info(f"Accepted connection from {addr}")
                    self.clientConnected.emit(addr[0], addr[1])

                    with conn:
                        while self._is_running:
                            data = conn.recv(1024)
                            if not data:
                                break
                            self.dataReceived.emit(data)

                except socket.timeout:
                    continue
                except OSError:
                    log.debug('some error idk')
                    break

        except Exception as e:
            log.error(f"Receiver Engine Error: {e}")
            self.errorOccurred.emit(str(e))
        finally:
            self.stop()

    def stop(self):
        self._is_running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        self._server_socket = None
        self.serverStopped.emit()