from scapy.utils import rdpcap
from pathlib import Path

def read_pcap(file_path):
    path = Path(file_path)
    return rdpcap(str(path))