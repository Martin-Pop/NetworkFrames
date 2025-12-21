import scapy.all as scapy_all
from scapy.fields import EnumField, FlagsField, MultiEnumField, BitField
from PySide6.QtCore import QObject, Signal


class NetworkFrame(QObject):

    infoUpdated = Signal()

    def __init__(self, _id, scapy_obj=None):
        super().__init__()
        self._id = _id
        self._scapy_object = scapy_obj
        self._scapy_edited_object = scapy_obj

        self.update_info()

    @property
    def id(self):
        return self._id

    @property
    def scapy(self):
        return self._scapy_object

    def update_info(self):
        self.infoUpdated.emit()

    def sync_layers(self, stack):

        if not stack:
            self._scapy_edited_object = None
            return

        new_packet = None

        for layer_name in stack:
            layer_cls = getattr(scapy_all, layer_name, None)

            if layer_cls is None:
                print(f"Warning: Unknown Scapy layer '{layer_name}', skipping.")
                continue

            layer_instance = None

            if self._scapy_edited_object:
                found_layer = self._scapy_edited_object.getlayer(layer_cls)

                if found_layer:
                    layer_instance = found_layer.copy()
                    layer_instance.remove_payload()

            if layer_instance is None:
                layer_instance = layer_cls()

            if new_packet is None:
                new_packet = layer_instance
            else:
                new_packet = new_packet / layer_instance

        self._scapy_edited_object = new_packet

    def prepare_layers(self):
        layers = []
        frame = self._scapy_edited_object

        if frame is None:
            return layers

        for i in range(len(frame.layers())):
            layers.append(frame.getlayer(i))

        return layers

    def prepare_data_for_editor(self):
        structure = []
        frame = self._scapy_edited_object

        if frame is None:
            return []

        for i in range(len(frame.layers())):
            layer = frame.getlayer(i)

            data = {
                "class_name": layer.__class__.__name__,
                "layer_name": layer.name,
                "fields": []
            }

            for f in layer.fields_desc:
                val = layer.getfieldval(f.name)

                field_info = {
                    "name": f.name,
                    "value": val,
                    "display_value": f.i2repr(layer, val),
                    "type": "text",
                    "options": None
                }

                if isinstance(f, (EnumField, MultiEnumField)):
                    field_info["type"] = "dropdown"
                    field_info["options"] = getattr(f, "i2s", {})

                elif isinstance(f, FlagsField):
                    field_info["type"] = "flags"
                    field_info["options"] = f.names

                elif isinstance(f, BitField) or "Int" in f.__class__.__name__:
                    field_info["type"] = "number"

                elif "IPField" in f.__class__.__name__:
                    field_info["type"] = "ip"

                elif "MACField" in f.__class__.__name__:
                    field_info["type"] = "mac"

                data["fields"].append(field_info)

            structure.append(data)

        return structure

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