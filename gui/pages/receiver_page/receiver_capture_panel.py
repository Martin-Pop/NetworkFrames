from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

class ReceiverCapturePanel(QWidget):
    backRequested = Signal()
    clearRequested = Signal()
    saveRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # placeholder
        label = QLabel("Capture Panel (TODO)")
        layout.addWidget(label)

        # temporary back button to test navigation
        btn_back = QPushButton("Back to Config")
        btn_back.clicked.connect(self.backRequested.emit)
        layout.addWidget(btn_back)

    def add_packet(self, packet_data):
        # TODO implement packet adding to table
        pass

    def clear_table(self):
        # TODO implement clear
        pass