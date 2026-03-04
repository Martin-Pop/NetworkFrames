from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition
import time
from scapy.all import sendp
import logging

from core.remote_client import RemoteClient

log = logging.getLogger(__name__)

class SenderWorker(QThread):
    packetSent = Signal(int)
    finished = Signal()
    errorOccurred = Signal(str)
    remoteReportReceived = Signal(list)

    def __init__(self, scapy_packets, interface, count=1, interval=0.1, remote_config=None):
        super().__init__()
        self.original_packets = scapy_packets
        self.iface = interface
        self.count = count
        self.interval = interval

        self.remote_config = remote_config
        self.remote_client = None

        self._is_running = True
        self._is_paused = False
        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()

    def _generate_strict_bpf_filter(self):
        filter_parts = set()
        iface_str = str(self.iface).lower()
        is_loopback = "loopback" in iface_str or "lo" == iface_str or "127.0.0.1" in iface_str

        for pkt in self.original_packets:
            pkt_filters = []
            has_l3 = pkt.haslayer('IP') or pkt.haslayer('IPv6') or pkt.haslayer('ARP')

            if pkt.haslayer('Ether') and not is_loopback and not has_l3:
                if pkt['Ether'].dst and pkt['Ether'].dst != "ff:ff:ff:ff:ff:ff":
                    pkt_filters.append(f"ether dst {pkt['Ether'].dst}")

            if pkt.haslayer('ARP'):
                pkt_filters.append("arp")
            elif pkt.haslayer('IP'):
                if pkt['IP'].dst and pkt['IP'].dst != "0.0.0.0" and pkt['IP'].dst != "255.255.255.255":
                    pkt_filters.append(f"dst host {pkt['IP'].dst}")
            elif pkt.haslayer('IPv6'):
                if pkt['IPv6'].dst and pkt['IPv6'].dst != "::":
                    pkt_filters.append(f"dst host {pkt['IPv6'].dst}")

            if pkt.haslayer('TCP'):
                pkt_filters.append("tcp")
                if pkt['TCP'].dport:
                    pkt_filters.append(f"dst port {pkt['TCP'].dport}")
            elif pkt.haslayer('UDP'):
                pkt_filters.append("udp")
                if pkt['UDP'].dport:
                    pkt_filters.append(f"dst port {pkt['UDP'].dport}")
            elif pkt.haslayer('ICMP'):
                pkt_filters.append("icmp")

            if pkt_filters:
                filter_parts.add("(" + " and ".join(pkt_filters) + ")")

        if not filter_parts:
            return ""

        return " or ".join(filter_parts)

    def run(self):
        sent_count = 0

        try:
            if not self.original_packets:
                raise Exception("Frames are empty")

            if self.remote_config:
                auto_filter = self._generate_strict_bpf_filter()
                self.remote_client = RemoteClient()
                ip = self.remote_config.get("remote_ip")
                port = self.remote_config.get("remote_port")

                if self.remote_client.connect_to_host(ip, port):
                    started = self.remote_client.send_start_command(auto_filter)

                    if not started:
                        self.errorOccurred.emit("Remote receiver refused START command. Aborting.")
                        self.remote_client.disconnect_from_host()
                        return
                else:
                    self.errorOccurred.emit("Could not connect to remote receiver. Aborting.")
                    return

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
        finally:
            if self.remote_client and self.remote_client.is_connected:
                try:
                    log.debug("Sending STOP to remote receiver")
                    report = self.remote_client.send_stop_command()
                    if report is not None:
                        self.remoteReportReceived.emit(report)
                except Exception:
                    pass
                self.remote_client.disconnect_from_host()

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

        if self.remote_client and self.remote_client.is_connected:
            try:
                if self._is_paused:
                    self.remote_client.send_pause_command()
                else:
                    self.remote_client.send_resume_command()
            except Exception:
                pass

        if not self._is_paused:
            self._wait_condition.wakeAll()
        self._mutex.unlock()

        return self._is_paused