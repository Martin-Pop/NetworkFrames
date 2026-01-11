import time
from PySide6.QtCore import QThread, Signal
from scapy.all import sendp, conf, send
import logging
log = logging.getLogger(__name__)

conf.verb = 0


class SenderWorker(QThread):
    packetSent = Signal(int)
    finished = Signal()
    errorOccurred = Signal(str)

    def __init__(self, scapy_packet, interface, count=1, interval=0.1, fuzz_enabled=False):
        super().__init__()
        self.original_packet = scapy_packet
        self.iface = interface
        self.count = count  # -1 for inf
        self.interval = interval
        self.fuzz_enabled = fuzz_enabled

        self._is_running = True

    def run(self):
        sent_count = 0
        try:
            while self._is_running:
                if self.count != -1 and sent_count >= self.count:
                    break

                packet_to_send = self.original_packet


                log.debug(f"Sending packet {packet_to_send} {self.iface}")
                sendp(packet_to_send, iface=self.iface)

                sent_count += 1
                self.packetSent.emit(sent_count)

                if self.interval > 0:
                    time.sleep(self.interval)

        except Exception as e:
            self.errorOccurred.emit(str(e))

        log.debug('sender finished, emitting signal now')
        self.finished.emit()

    def stop(self):
        self._is_running = False

    def _fuzz_packet(self, packet):
        pass