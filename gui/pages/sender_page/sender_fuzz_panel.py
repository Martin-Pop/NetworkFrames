from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel, QFrame


class SenderFuzzPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('sender_fuzz')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)

        # header
        header = QLabel("Fuzzing & Modification")
        layout.addWidget(header)

        # content
        self.chk_enable = QCheckBox("Enable Fuzzing / Malformation")
        self.chk_enable.setToolTip("Randomizes packet fields based on rules (Coming soon)")

        layout.addWidget(self.chk_enable)
        # ....

    def is_fuzzing_enabled(self):
        return self.chk_enable.isChecked()

    def set_locked(self, locked):
        self.setEnabled(not locked)