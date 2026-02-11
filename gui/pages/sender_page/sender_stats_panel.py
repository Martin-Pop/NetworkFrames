from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QLabel, QFrame, QFormLayout


class SenderStatsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('sender_stats')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)

        header = QLabel("Statistics")
        header.setObjectName('header_label')
        layout.addWidget(header)

        self.stats_form = QFormLayout()
        self.stats_form.setVerticalSpacing(5)
        self.stats_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # status
        self.val_status = QLabel()
        self.set_status('No frame selected', 'red')
        self.stats_form.addRow("Sender status:", self.val_status)

        # counter
        self.val_counter = QLabel("0")
        self.stats_form.addRow("Packets Sent:", self.val_counter)

        # receiver
        self.val_receiver = QLabel("Not Configured")
        self.stats_form.addRow("Remote Receiver:", self.val_receiver)

        layout.addLayout(self.stats_form)

        layout.addStretch()

    def update_count(self, count):
        self.val_counter.setText(str(count))

    def set_status(self, text, color="gray"):
        self.val_status.setText(text)
        self.val_status.setStyleSheet(f"color: {color}; font-weight: bold;")

    def set_receiver_status(self, text, color="gray"):
        self.val_receiver.setText(text)
        self.val_receiver.setStyleSheet(f"color: {color};")