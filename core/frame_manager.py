from scapy.layers.l2 import Ether
from PySide6.QtCore import QObject, Signal


class NetworkFrame(QObject):

    infoUpdated = Signal()

    def __init__(self, id, scapy_obj=None):
        super().__init__()
        self.info = {
            "id": id,
        }
        self._scapy_object = scapy_obj
        self.update_info()

    @property
    def scapy(self):
        return self._scapy_object

    @scapy.setter
    def scapy(self, value):
        self._scapy_object = value

    def update_info(self):

        if self._scapy_object is not None:
            if self._scapy_object.haslayer(Ether):
                eth = self._scapy_object[Ether]
                self.info['src'] = eth.fields['src']
                self.info['dst'] = eth.fields['dst']

        print('info updated')
        self.infoUpdated.emit()

class FrameManager:

    def __init__(self):
        self.frames = {}
        self._current_id = 1

    def add(self, frame):
        new_frame = NetworkFrame(self._current_id, frame)
        self.frames[str(self._current_id)] = new_frame
        self._current_id += 1
        return new_frame
