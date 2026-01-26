import scapy.all as scapy_all
from scapy.layers.inet import IP, DestIPField
from scapy.layers.inet6 import IPv6
from scapy.fields import RawVal
from PySide6.QtCore import QObject, Signal

import logging

from scapy.layers.l2 import Ether, SourceMACField, DestMACField
from scapy.fields import *

log = logging.getLogger(__name__)

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

        src, dst, protocol = "", "", ""
        info = "empty frame"
        length = 0

        if self._scapy_object:
            try:
                # len forces scapy to build -> errors on malformed packet
                length = len(self._scapy_object)

                if IP in self._scapy_object:
                    src, dst = str(self._scapy_object[IP].src), str(self._scapy_object[IP].dst)
                elif IPv6 in self._scapy_object:
                    src, dst = str(self._scapy_object[IPv6].src), str(self._scapy_object[IPv6].dst)
                elif Ether in self._scapy_object:
                    src, dst = str(self._scapy_object[Ether].src), str(self._scapy_object[Ether].dst)

                protocol = self._scapy_object.lastlayer().name

                try:
                    info = self._scapy_object.summary()
                except Exception:
                    info = "Summary unavailable"

            except Exception as e:
                log.warning(f"Frame {self._id} has invalid data: {e}")
                protocol = "MALFORMED"
                info = f"Invalid Data: {str(e)}"

        self._info = {
            "id": str(self._id),
            "src_ip": src,
            "dst_ip": dst,
            "protocol": protocol,
            "len": length,
            "info": info
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
                log.warning(f"Warning: Unknown Scapy layer '{layer_name}', skipping.")
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

    def reconstruct_scapy(self, editor_data):
        packet = None

        for layer_info in editor_data:
            class_name = layer_info['layer_class']
            raw_fields = layer_info['fields']

            layer_cls = getattr(scapy_all, class_name, None)
            if not layer_cls:
                continue

            final_fields = {}
            layer_field_map = {f.name: f for f in layer_cls.fields_desc}

            for key, val in raw_fields.items():

                if val is None or val == "":
                    continue

                field_desc = layer_field_map.get(key)

                if field_desc and isinstance(val, str):
                    string_types = (
                        StrField,
                        IPField, SourceIPField, DestIPField,
                        IP6Field, SourceIP6Field, DestIP6Field,
                        MACField, SourceMACField, DestMACField
                    )

                    if not isinstance(field_desc, string_types):
                        try:
                            val = int(val, 0)
                        except ValueError:
                            pass

                if field_desc and isinstance(val, bytes):
                    if isinstance(field_desc,
                                  (IPField, SourceIPField, DestIPField, IP6Field, SourceIP6Field, DestIP6Field,
                                   StrField)):
                        try:
                            val = val.decode('utf-8')
                        except:
                            pass

                try:
                    test_layer = layer_cls(**{key: val})
                    bytes(test_layer)

                    final_fields[key] = val
                except Exception as e:

                    if isinstance(val, str):
                        raw_data = val.encode('utf-8')
                    elif isinstance(val, bytes):
                        raw_data = val
                    else:
                        raw_data = str(val).encode('utf-8')

                    final_fields[key] = RawVal(raw_data)
            try:
                new_layer = layer_cls(**final_fields)
                if packet is None:
                    packet = new_layer
                else:
                    packet = packet / new_layer
            except Exception as e:
                log.critical(f"Failed to build layer {class_name}: {e}")

        self._scapy_object = packet
        self._update_info()

    def _get_zero_value(self, field_desc):
        if isinstance(field_desc, (IPField, SourceIPField, DestIPField)):
            return "0.0.0.0"
        elif isinstance(field_desc, (MACField, SourceMACField, DestMACField)):
            return "00:00:00:00:00:00"
        elif isinstance(field_desc, (ByteField, ShortField, IntField, BitField)):
            return 0
        else:
            return 0

class FrameManager:

    def __init__(self):
        self.frames = {}
        self._current_id = 1

    def get_frame(self, _id):
        return self.frames.get(str(_id), None)

    def remove_frame(self, _id):
        self.frames.pop(str(_id), None)

    def add(self, frame):
        log.debug(frame)
        new_frame = NetworkFrame(self._current_id, frame)
        self.frames[str(self._current_id)] = new_frame
        self._current_id += 1
        return new_frame