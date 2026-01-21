from PySide6.QtWidgets import  QVBoxLayout, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Signal


class SenderButtonsPanel(QFrame):
    startClicked = Signal()
    stopClicked = Signal()
    pauseClicked = Signal()
    backClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('sender_buttons')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(8)

        # start
        self.btn_start = QPushButton("Start")
        self.btn_start.setObjectName('sender_buttons')
        self.btn_start.clicked.connect(self.startClicked.emit)
        layout.addWidget(self.btn_start)

        # pause
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName('sender_buttons')
        self.btn_pause.setCheckable(True)  # Toggle button
        self.btn_pause.clicked.connect(self.pauseClicked.emit)
        layout.addWidget(self.btn_pause)

        #stop
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName('sender_buttons')
        self.btn_stop.clicked.connect(self.stopClicked.emit)
        layout.addWidget(self.btn_stop)

        # Back
        self.btn_back = QPushButton("Back")
        self.btn_back.setObjectName('sender_buttons')
        self.btn_back.setMinimumWidth(120)
        self.btn_back.clicked.connect(self.backClicked.emit)
        layout.addWidget(self.btn_back)

        # Set initial state
        self.set_running_state(False)

    def set_running_state(self, is_running):
        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
        self.btn_pause.setEnabled(is_running)
        self.btn_back.setEnabled(not is_running)

        if not is_running:
            self.btn_pause.setChecked(False)
            self.btn_pause.setText("Pause")