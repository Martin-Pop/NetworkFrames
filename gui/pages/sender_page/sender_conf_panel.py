from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QComboBox,
    QSpinBox, QDoubleSpinBox, QLabel, QFrame, QCheckBox
)
from PySide6.QtCore import Signal, Qt


class SenderConfPanel(QFrame):
    """
    Left side: Interface selection, Count, Interval.
    """
    interfaceChanged = Signal(str)  # Emits interface internal name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('sender_conf')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)

        # header
        header = QLabel("Configuration")
        header.setObjectName('header_label')
        layout.addWidget(header)

        # form
        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(15)

        # int
        self.interface_combo = QComboBox()
        self.interface_combo.currentIndexChanged.connect(self._on_interface_change)
        self.form_layout.addRow("Interface:", self.interface_combo)

        # count
        self.count_spin = QSpinBox()
        self.count_spin.setRange(-1, 999999)
        self.count_spin.setValue(1)
        self.count_spin.setSpecialValueText("Infinite Loop")
        self.form_layout.addRow("Count:", self.count_spin)

        # interval
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.0, 60.0)
        self.interval_spin.setSingleStep(0.01)
        self.interval_spin.setValue(0.10)
        self.interval_spin.setSuffix(" sec")
        self.form_layout.addRow("Interval:", self.interval_spin)

        # try use receiver
        self.use_receiver = QCheckBox()
        self.use_receiver.setChecked(False)
        self.use_receiver.setEnabled(False)
        self.form_layout.addRow("Use Receiver:", self.use_receiver)

        layout.addLayout(self.form_layout)
        layout.addStretch()

    def set_interfaces(self, int_list):
        """
        Updates interface selection.
        :param int_list: list of interface names
        """

        self.interface_combo.blockSignals(True)
        self.interface_combo.clear()

        for name in int_list:
            self.interface_combo.addItem(name, name)

        self.interface_combo.blockSignals(False)

        # manual update
        if self.interface_combo.count() > 0:
            self._on_interface_change()

    def _on_interface_change(self):
        data = self.interface_combo.currentData()
        self.interfaceChanged.emit(data)

    def get_settings(self):
        return {
            "interface": self.interface_combo.currentData(),
            "count": self.count_spin.value(),
            "interval": self.interval_spin.value()
        }

    def set_locked(self, locked):
        """
        Locks configuration. Used during sending process
        :param locked: True for locked, False for unlocked
        """
        self.setEnabled(not locked)


class SenderInfoPanel(QFrame):
    """
    Right side: Details about selected interface or future info.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('sender_info')
        self.setContentsMargins(5,0,0,0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10,10,10,10)

        # header
        header = QLabel("Information")
        header.setObjectName('header_label')
        layout.addWidget(header)

        # info
        self.info_form = QFormLayout()
        self.info_form.setVerticalSpacing(5)

        self.lbl_ip = QLabel("-")
        self.lbl_mac = QLabel("-")

        self.info_form.addRow("IP Addresses:", self.lbl_ip)
        self.info_form.addRow("MAC Address:", self.lbl_mac)

        layout.addLayout(self.info_form)
        layout.addStretch()

    def update_info(self, interface_data):
        if not interface_data:
            self.lbl_ip.setText("-")
            self.lbl_mac.setText("-")
            return
        ips = interface_data.get("ips", None)
        if ips:
            self.lbl_ip.setText('\n'.join(ips))
        else:
            self.lbl_ip.setText("Unknown")
        self.lbl_mac.setText(interface_data.get("mac", "Unknown"))