from scapy.all import *

def get_scapy_layer(protocol_name: str):
    """
    Dynamicly loads scapy class by its name
    :param protocol_name: scapy class name
    :return: scapy class
    """
    layer_class = globals().get(protocol_name)
    if layer_class and issubclass(layer_class, Packet):
        return layer_class
    raise AttributeError(f"Class '{protocol_name}' was not found in Scapy.")


class ProtocolWrapper:
    def __init__(self, name: str, config: dict):
        self.name = name
        self.fields = config.get("fields", {})
        self.can_be_payload_of = config.get("can_be_payload_of", [])

        self.user_values = {}

        try:
            self.scapy_class = get_scapy_layer(name)
        except AttributeError as e:
            self.scapy_class = None
            print(f"Error: {e}")

    def set_field_value(self, field_name: str, value):
        """
        Saves user defined field value
        :param field_name: protocol field name
        :param value: protocol field value
        """
        if field_name in self.fields:
            self.user_values[field_name] = value
        else:
            raise ValueError(f"Pole '{field_name}' neexistuje v protokolu '{self.name}'.")

    def get_protocol_values(self) -> dict:
        """
        Creates a dictionary with user defined values or default values
        :return: dictionary of values
        """
        values = {}
        for field_name, field_data in self.fields.items():

            value = self.user_values.get(field_name)
            if value is None and 'default' in field_data:
                value = field_data['default']

            if value is not None:
                values[field_name] = value
        return values

    def build_scapy_protocol(self):
        """
        Builds scapy protocol
        :return: scapy class
        """
        if self.scapy_class is None:
            raise TypeError(f"Can not create scapy for {self.name}.")

        values = self.get_protocol_values()
        return self.scapy_class(**values)