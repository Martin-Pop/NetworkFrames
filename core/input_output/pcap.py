import logging
from scapy.all import wrpcap
from utils.pcap import read_pcap

log = logging.getLogger(__name__)


def read_pcap_generator(file_path):
    """
    Generator that yields Scapy packets from a PCAP file one by one.
    """
    try:
        for pkt in read_pcap(file_path):
            yield pkt
    except Exception as e:
        log.error(f"Error reading PCAP file {file_path}: {e}")


def write_pcap_file(file_path, ids, frame_manager):
    """
    Writes selected frames to a PCAP file.
    :param file_path: Target .pcap file path
    :param ids: List of frame IDs to save
    :param frame_manager: Instance of FrameManager to retrieve packet data
    """
    packets_to_write = []

    try:
        for frame_id in ids:
            frame = frame_manager.get_frame(frame_id)
            if frame:
                scapy_pkt = frame.scapy

                if scapy_pkt:
                    packets_to_write.append(scapy_pkt)
                else:
                    continue

        if packets_to_write:
            wrpcap(file_path, packets_to_write)
        else:
            log.warning("No valid packets found to write.")

    except Exception as e:
        log.error(f"Error writing PCAP file {file_path}: {e}")