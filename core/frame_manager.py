import scapy.all as scapy_all
from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6
from scapy.fields import EnumField, FlagsField, MultiEnumField, BitField
from PySide6.QtCore import QObject, Signal


class NetworkFrame(QObject):

    infoUpdated = Signal()

    def __init__(self, _id, scapy_obj=None):
        super().__init__()
        self._info = {}
        self._id = _id
        self._scapy_object = scapy_obj

        self._update_info()

    @property
    def id(self):
        return self._id

    @property
    def scapy(self):
        return self._scapy_object

    def _update_info(self):

        if self._scapy_object:
            if IP in self._scapy_object:
                src, dst = str(self._scapy_object[IP].src), str(self._scapy_object[IP].dst)
            elif IPv6 in self._scapy_object:
                src, dst = str(self._scapy_object[IPv6].src), str(self._scapy_object[IPv6].dst)
            else:
                src, dst = "",""
            protocol = self._scapy_object.lastlayer().name
        else:
            src, dst, protocol = "", "", ""

        self._info = {
            "id": str(self._id),
            "src_ip": src,
            "dst_ip": dst,
            "protocol": protocol
        }

        self.infoUpdated.emit()

    def get_info(self):
        return self._info


    def sync_layers(self, stack):

        if not stack:
            self._scapy_object = None
            return

        new_packet = None

        for layer_name in stack:
            layer_cls = getattr(scapy_all, layer_name, None)

            if layer_cls is None:
                print(f"Warning: Unknown Scapy layer '{layer_name}', skipping.")
                continue

            layer_instance = None

            if self._scapy_object:
                found_layer = self._scapy_object.getlayer(layer_cls)

                if found_layer:
                    layer_instance = found_layer.copy()
                    layer_instance.remove_payload()

            if layer_instance is None:
                layer_instance = layer_cls()

            if new_packet is None:
                new_packet = layer_instance
            else:
                new_packet = new_packet / layer_instance

        self._scapy_object = new_packet

    def prepare_layers(self):
        layers = []
        frame = self._scapy_object

        if frame is None:
            return layers

        for i in range(len(frame.layers())):
            layers.append(frame.getlayer(i))

        return layers

    def reconstruct_scapy(self,editor_data):

        packet = None

        for layer_info in editor_data:
            class_name = layer_info['layer_class']
            fields = layer_info['fields']

            try:
                layer_cls = getattr(scapy_all, class_name, None)

                if layer_cls:

                    new_layer = layer_cls(**fields)

                    if packet is None:
                        packet = new_layer
                    else:
                        packet = packet / new_layer
                else:
                    print(f"Warning unknown class:{class_name}")

            except Exception as e:
                print(f"Error creating layer{class_name}: {e}")

        self._scapy_object = packet
        self._update_info()

class FrameManager:

    def __init__(self):
        self.frames = {}
        self._current_id = 1

    def get_frame(self, _id):
        return self.frames.get(str(_id), None)

    def add(self, frame):
        print(frame)
        new_frame = NetworkFrame(self._current_id, frame)
        self.frames[str(self._current_id)] = new_frame
        self._current_id += 1
        return new_frame