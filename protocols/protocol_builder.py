from .protocol_wrapper import ProtocolWrapper


class PacketBuilder:
    def __init__(self, protocol_map):
        self.wrappers = {}
        for name, config in protocol_map.items():
            self.wrappers[name] = ProtocolWrapper(name, config)

    def get_possible_upper_protocols(self, protocol_name: str) -> list:
        """
        Returns a list of protocol that can be encapsulated into specified protocol_name
        :param protocol_name: name of the protocol
        :return: list of protocol names
        """
        names = []
        for name, wrapper in self.wrappers.items():
            if protocol_name in wrapper.can_be_payload_of:
                names.append(name)

        return names

    def get_possible_lower_protocols(self, protocol_name: str) -> list:
        """
        Returns a list of protocols that specified protocol_name can be encapsulated into
        :param protocol_name: name of the protocol
        :return: list of protocol names
        """
        return self.wrappers[protocol_name].can_be_payload_of

    def get_commutable_protocols(self, protocol_name: str, upper_name: str | None, lower_name: str | None) -> list:
        """
        Returns a list of protocols that can replace 'protocol_name' in the current stack position.

        :param protocol_name: The current protocol at this position (to be excluded from results)
        :param upper_name: The protocol immediately above (or None if top of stack)
        :param lower_name: The protocol immediately below (or None if bottom of stack)
        :return: List of valid replacement protocol names
        """

        if lower_name:
            candidates = set(self.get_possible_upper_protocols(lower_name))
        else:
            candidates = set(self.wrappers.keys())

        if upper_name:
            required_bases = set(self.get_possible_lower_protocols(upper_name))
            valid_replacements = list(candidates & required_bases)
        else:
            valid_replacements = list(candidates)

        # if protocol_name in valid_replacements:
        #     valid_replacements.remove(protocol_name)

        return valid_replacements

    def get_all_protocols(self) -> list:
        return list(self.wrappers.keys())

    def build_packet(self, layer_names: list):
        """
        Builds a packet from a list of layers
        :param layer_names: list of layer names - must be from lowest to highest layer
        :return: final scapy packet (frame)
        """

        # build scapy protocol object from wrappers
        layers_to_build = []
        for name in layer_names:
            wrapper = self.wrappers.get(name)
            if not wrapper:
                raise ValueError(f"Protocol {name} is not defined.")
            layers_to_build.append(wrapper.build_scapy_protocol())

        if not layers_to_build:
            return None

        # build the whole packet (frame) by combining with /
        packet = layers_to_build[0]  # Ether
        for layer in layers_to_build[1:]:
            packet = packet / layer

        return packet
