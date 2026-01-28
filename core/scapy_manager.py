from scapy.all import *
import logging

log = logging.getLogger(__name__)


class ScapyManager:
    """
    Replaces PacketBuilder and ProtocolWrapper.
    Dynamically discovers protocol relationships from Scapy's internal registry.
    """

    def __init__(self, allowed_protocols=None):
        """
        :param allowed_protocols: Optional list of protocol names to whitelist.
        If None, it tries to discover common ones.
        """
        self.upper_relations = {}
        self.lower_relations = {}
        self.all_protocols = set()

        #whitelist
        if allowed_protocols is None:
            self.whitelist = {
                'Ether', 'Dot1Q', 'ARP',
                'IP', 'IPv6', 'ICMP', 'TCP', 'UDP',
                'DNS', 'Raw', 'Padding'
            }
        else:
            self.whitelist = set(allowed_protocols)

        self._build_graph()

    def _build_graph(self):
        """
        Builds the relationship graph by inspecting 'payload_guess' of whitelisted classes.
        """

        loaded_classes = {}  # {'Ether': <class scapy.layers.l2.Ether>, ...}

        for name in self.whitelist:
            cls = globals().get(name)
            if cls and isinstance(cls, type) and issubclass(cls, Packet):
                loaded_classes[name] = cls
                self.all_protocols.add(name)
            else:
                if name not in ['Raw', 'Padding']:
                    log.debug(f"Warning: Protocol '{name}' from whitelist not found in Scapy globals.")

        for lower_name, lower_cls in loaded_classes.items():

            # payload_guess example: Ether: [({'type': 2048}, <class IP>),...]
            if not hasattr(lower_cls, 'payload_guess') or not lower_cls.payload_guess:
                continue

            for item in lower_cls.payload_guess:
                try:
                    upper_cls = item[1]

                    if not isinstance(upper_cls, type):
                        continue

                    upper_name = upper_cls.__name__

                    if upper_name in self.whitelist:

                        if lower_name == upper_name:
                            continue

                        if lower_name not in self.upper_relations:
                            self.upper_relations[lower_name] = set()
                        self.upper_relations[lower_name].add(upper_name)

                        if upper_name not in self.lower_relations:
                            self.lower_relations[upper_name] = set()
                        self.lower_relations[upper_name].add(lower_name)

                except Exception:
                    continue

        # raw, padding
        for proto in self.all_protocols:
            if proto not in self.upper_relations:
                self.upper_relations[proto] = set()

            if 'Raw' in self.whitelist:
                self.upper_relations[proto].add('Raw')
                if 'Raw' not in self.lower_relations: self.lower_relations['Raw'] = set()
                self.lower_relations['Raw'].add(proto)

            if 'Padding' in self.whitelist:
                self.upper_relations[proto].add('Padding')
                if 'Padding' not in self.lower_relations: self.lower_relations['Padding'] = set()
                self.lower_relations['Padding'].add(proto)

    def is_supported(self, protocol_name: str) -> bool:
        return globals().get(protocol_name) is not None

    def get_possible_upper_protocols(self, protocol_name: str) -> list:
        return list(self.upper_relations.get(protocol_name, []))

    def get_possible_lower_protocols(self, protocol_name: str) -> list:
        return list(self.lower_relations.get(protocol_name, []))

    def get_commutable_protocols(self, upper_name: str | None, lower_name: str | None) -> list:
        if lower_name:
            candidates = self.get_possible_upper_protocols(lower_name)
        else:
            candidates = list(self.all_protocols)

        if upper_name:
            required_bases = self.get_possible_lower_protocols(upper_name)
            valid_replacements = [p for p in candidates if p in required_bases]
            return valid_replacements

        return candidates