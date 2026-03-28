import platform
import logging
from scapy.all import get_if_list, get_if_addr, get_if_hwaddr, conf

log = logging.getLogger(__name__)

def get_os_type():
    """
    Get OS type
    :return: 'Windows', 'Linux' or 'Darwin' (macOS).
    """
    return platform.system()


def get_interfaces():
    """
    Detects os type and returns list of interfaces.
    {
    "name": "eth0" or "Ethernet",
    "description": "Intel Ethernet..." or "eth0",
    "ips": [ipv6, ipv4],
    "mac": "aa:bb:cc:dd:ee:ff"
    },
    ...
    :return: list of interfaces.
    """
    os_type = get_os_type()

    if os_type == "Windows":
        return _get_windows_interfaces()
    elif os_type == "Linux":
        return _get_linux_interfaces()
    else:
        log.warning(f"Unsupported OS: {os_type}")
        return []


def _get_windows_interfaces():
    """
    Gets interfaces on windows
    :return: list of windows interfaces.
    """
    interfaces = []
    try:
        from scapy.arch.windows import get_windows_if_list
        win_list = get_windows_if_list()

        for iface in win_list:
            ips = iface.get("ips")
            if ips:
                sorted_ips = sorted(ips, key=lambda x: ':' in x)

                interfaces.append({
                    "name": iface["name"],
                    "description": iface["description"],
                    "ips": sorted_ips,
                    "mac": iface.get("mac", "00:00:00:00:00:00")
                })

    except ImportError:
        log.error("Could not import get_windows_if_list. Are you on Windows?")
    except Exception as e:
        log.error(f"Error getting Windows interfaces: {e}")

    return interfaces

    return interfaces


def _get_linux_interfaces():
    """
    Gets interfaces on linux
    :return: list of linux interfaces
    """
    interfaces = []
    try:
        # ['eth0', 'lo', 'wlan0']
        if_list = get_if_list()

        for iface_name in if_list:

            try:
                ip = get_if_addr(iface_name)
                mac = get_if_hwaddr(iface_name)

                if ip and ip != "0.0.0.0":
                    interfaces.append({
                        "name": iface_name,
                        "description": iface_name,
                        "ips": [ip],
                        "mac": mac
                    })
            except Exception:
                continue

    except Exception as e:
        log.error(f"Error getting Linux interfaces: {e}")

    return interfaces