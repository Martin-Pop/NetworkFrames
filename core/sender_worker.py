from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
import time
from scapy.all import sendp
import logging

log = logging.getLogger(__name__)

class SenderWorker(QThread):
    packetSent = Signal(int)
    finished = Signal()
    errorOccurred = Signal(str)

    def __init__(self, scapy_packets, interface, count=1, interval=0.1):
        super().__init__()
        self.original_packets = scapy_packets
        self.iface = interface
        self.count = count
        self.interval = interval

        self._is_running = True
        self._is_paused = False
        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()

    def run(self):
        sent_count = 0
        try:
            while self._is_running:
                if self.count != -1 and sent_count >= self.count:
                    break

                for packet_to_send in self.original_packets:
                    if not self._is_running:
                        break

                    log.debug(f"Sending packet {packet_to_send} {self.iface}")
                    sendp(packet_to_send, iface=self.iface)

                    sent_count += 1
                    self.packetSent.emit(sent_count)

                    if self.count != -1 and sent_count >= self.count:
                        break

                    if self.interval > 0:
                        time.sleep(self.interval)

                    self._mutex.lock()
                    if self._is_paused:
                        self._wait_condition.wait(self._mutex)
                    self._mutex.unlock()

        except Exception as e:
            self.errorOccurred.emit(str(e))

        log.debug('sender finished, emitting signal now')
        self.finished.emit()

    def stop(self):
        self._is_running = False
        self._mutex.lock()
        self._is_paused = False
        self._wait_condition.wakeAll()
        self._mutex.unlock()

    def toggle_pause(self):
        self._mutex.lock()
        self._is_paused = not self._is_paused
        if not self._is_paused:
            self._wait_condition.wakeAll()
        self._mutex.unlock()

        return self._is_paused