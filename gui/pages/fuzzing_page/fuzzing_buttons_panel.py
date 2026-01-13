from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal


class FuzzingButtonsPanel(QWidget):
    generateClicked = Signal()
    backClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sender_buttons")  # Reuse sender style
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_status = QLabel("Ready")

        self.btn_back = QPushButton("Back")
        self.btn_back.setProperty("styleClass", "common_button")

        self.btn_gen = QPushButton("Generate")
        self.btn_gen.setProperty("styleClass", "send_button")
        self.btn_gen.setEnabled(False)  # disable until target

        layout.addWidget(self.btn_back)
        layout.addStretch()
        layout.addWidget(self.lbl_status)
        layout.addSpacing(20)
        layout.addWidget(self.btn_gen)

        self.btn_back.clicked.connect(self.backClicked)
        self.btn_gen.clicked.connect(self.generateClicked)

    def set_generate_enabled(self, enabled):
        self.btn_gen.setEnabled(enabled)

    def set_status(self, text, color="gray"):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-weight: bold; color: {color};")