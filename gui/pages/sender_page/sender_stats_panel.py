from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QFrame


class SenderStatsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('sender_stats')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 10, 0)

        header = QLabel("Statistics")
        layout.addWidget(header)

        # counter
        self.lbl_counter = QLabel("0")
        self.lbl_counter.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.lbl_counter)

        # status text
        self.lbl_status = QLabel("Ready")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

    def update_count(self, count):
        self.lbl_counter.setText(str(count))

    def set_status(self, text, color="gray"):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-size: 12px; color: {color}; font-weight: bold;")