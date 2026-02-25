import socket
import logging
import json
from PySide6.QtCore import QThread, Signal
from scapy.all import AsyncSniffer

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
    clientDisconnected = Signal(str, int)

    errorOccurred = Signal(str)

    def __init__(self, port, iface_ip="0.0.0.0", iface_name=None):
        super().__init__()
        self.port = port
        self.iface_ip = iface_ip
        self.iface_name = iface_name

        self._is_running = False
        self._server_socket = None
        self._active_conn = None
        self.sniffer = None

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

                    log.debug(f"Remote Sender connected from {addr}")
                    self.clientConnected.emit(addr[0], addr[1])
                    self._active_conn = conn

                    with conn:
                        while self._is_running:
                            try:
                                conn.settimeout(1.0)
                                data = conn.recv(8192)
                                if not data:
                                    break

                                self._process_command(data, conn)

                            except socket.timeout:
                                continue
                            except OSError:
                                break

                    self._active_conn = None
                    self.clientDisconnected.emit(addr[0], addr[1])
                    log.debug(f"Remote Sender {addr} disconnected")

                    if self.sniffer and self.sniffer.running:
                        self.sniffer.stop()

                except socket.timeout:
                    continue
                except OSError as e:
                    if self._is_running:
                        log.error(f"Socket error: {e}")
                    break

        except Exception as e:
            self.errorOccurred.emit(str(e))
        finally:
            self.stop()

    def _process_command(self, data, conn):
        try:
            msg = data.decode('utf-8').strip()
            payload = json.loads(msg)
            cmd = payload.get("cmd")

            if cmd == "START":
                filter_str = payload.get("filter", "")
                log.debug(f"Received START command. Filter: [{filter_str}]")

                if self.sniffer and self.sniffer.running:
                    self.sniffer.stop()

                self.sniffer = AsyncSniffer(iface=self.iface_name, filter=filter_str)
                self.sniffer.start()

                resp = json.dumps({"status": "LISTENING"}).encode('utf-8')
                conn.sendall(resp)

            elif cmd == "PAUSE":
                log.debug("Received PAUSE command. Waiting...")
                conn.sendall(json.dumps({"status": "PAUSED"}).encode('utf-8'))

            elif cmd == "RESUME":
                log.debug("Received RESUME command.")
                conn.sendall(json.dumps({"status": "RESUMED"}).encode('utf-8'))


            elif cmd == "STOP":
                log.debug("Received STOP command. Stopping sniffer...")

                if self.sniffer:
                    try:
                        if self.sniffer.running:
                            self.sniffer.stop()
                    except Exception as e:
                        log.debug(f"Could not cleanly stop sniffer: {e}")

                    try:
                        self.sniffer.join(timeout=2.0)
                    except Exception:
                        pass

                captured = getattr(self.sniffer, 'results', None)
                if captured is None:
                    captured = []

                log.debug(f"Captured {len(captured)} packets.")
                packet_list = []
                for pkt in captured:
                    try:
                        packet_list.append({
                            "summary": pkt.summary(),
                            "hex_data": bytes(pkt).hex(),
                            "len": len(pkt)
                        })
                    except Exception as e:
                        log.error(f"Failed to serialize packet: {e}")

                report = {
                    "type": "REPORT",
                    "packets": packet_list
                }

                resp = json.dumps(report).encode('utf-8')
                conn.sendall(resp)

        except json.JSONDecodeError:
            log.warning(f"Invalid JSON command received: {data}")
        except Exception as e:
            log.error(f"Error processing command: {e}")

    def stop(self):
        self._is_running = False

        if self.sniffer:
            try:
                if self.sniffer.running:
                    self.sniffer.stop()
            except Exception:
                pass

            try:
                self.sniffer.join(timeout=2.0)
            except Exception:
                pass

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