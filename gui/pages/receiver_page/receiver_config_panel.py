from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QSpinBox, QPushButton,
    QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
import logging

log = logging.getLogger(__name__)

class ReceiverRemotePanel(QFrame):
    """
    Left/Top panel: Remote Device Settings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('receiver_remote_panel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("Remote Device")
        header.setObjectName('header_label')
        layout.addWidget(header)

        # Form
        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(15)

        # Validator
        ip_regex = QRegularExpression(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        self.ip_validator = QRegularExpressionValidator(ip_regex)

        # Inputs
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g. 192.168.1.50")
        self.ip_input.setValidator(self.ip_validator)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(5000)

        self.form_layout.addRow("Remote IP:", self.ip_input)
        self.form_layout.addRow("Remote Port:", self.port_spin)

        layout.addLayout(self.form_layout)
        layout.addStretch()

    def get_data(self):
        return {
            "remote_ip": self.ip_input.text(),
            "remote_port": self.port_spin.value()
        }


class ReceiverLocalPanel(QFrame):
    """
    Right/Bottom panel: Local Settings.
    Styled to match SenderInfoPanel.
    """
    interfaceChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('receiver_local_panel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QLabel("Local Listener")
        header.setObjectName('header_label')
        layout.addWidget(header)

        # Form
        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(15)

        # Inputs
        self.interface_combo = QComboBox()
        self.interface_combo.currentIndexChanged.connect(self._on_interface_change)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(6000)

        self.form_layout.addRow("Interface:", self.interface_combo)
        self.form_layout.addRow("Listen Port:", self.port_spin)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.form_layout.addRow(line)

        self.lbl_ip = QLabel("-")
        self.lbl_mac = QLabel("-")

        self.form_layout.addRow("IP Addresses:", self.lbl_ip)
        self.form_layout.addRow("MAC Address:", self.lbl_mac)

        layout.addLayout(self.form_layout)
        layout.addStretch()

    def set_interfaces(self, int_list):
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

    def update_interface_info(self, interface_data):
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

    def get_data(self):
        return {
            "local_iface": self.interface_combo.currentText(),
            "local_port": self.port_spin.value()
        }


class ReceiverConfigurationPanel(QWidget):
    """
    Main container for the configuration view.
    """
    configSaved = Signal(dict)
    syncRequested = Signal(dict)
    interfaceChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        panels_layout = QHBoxLayout()

        self.remote_panel = ReceiverRemotePanel()
        self.local_panel = ReceiverLocalPanel()

        panels_layout.addWidget(self.remote_panel, 1)
        panels_layout.addWidget(self.local_panel, 1)

        main_layout.addLayout(panels_layout)

        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)

        self.status_lbl = QLabel("Status: Not Synced")
        self.status_lbl.setObjectName("ReceiverStatusLabel")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setProperty("styleClass", "common_button")
        self.save_btn.clicked.connect(self._on_save_clicked)

        self.sync_btn = QPushButton("Sync / Test Connection")
        self.sync_btn.setMinimumHeight(35)
        self.sync_btn.setProperty("styleClass", "common_button")
        self.sync_btn.clicked.connect(self._on_sync_clicked)
        self.sync_btn.setEnabled(False)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.sync_btn)

        footer_layout.addWidget(self.status_lbl)
        footer_layout.addLayout(btn_layout)

        main_layout.addWidget(footer_widget)

    def _connect_signals(self):
        self.local_panel.interfaceChanged.connect(self.interfaceChanged)

    def _on_save_clicked(self):
        config = self.get_config()

        if not config['remote_ip']:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid Remote IP address.")
            return

        self.configSaved.emit(config)

        self.sync_btn.setEnabled(True)
        self.status_lbl.setText("Status: Configuration Saved")
        self.status_lbl.setProperty("status", "saved")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

    def _on_sync_clicked(self):
        config = self.get_config()
        self.status_lbl.setText("Status: Syncing...")
        self.status_lbl.setProperty("status", "syncing")
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)

        self.syncRequested.emit(config)

    def get_config(self):
        data = {}
        data.update(self.remote_panel.get_data())
        data.update(self.local_panel.get_data())
        return data

    def set_interfaces(self, ifaces):
        self.local_panel.set_interfaces(ifaces)

    def update_local_interface_info(self, interface_data):
        self.local_panel.update_interface_info(interface_data)

    def set_sync_status(self, success, message=""):
        if success:
            self.status_lbl.setText(f"Status: Synced! ({message})")
            self.status_lbl.setProperty("status", "success")
        else:
            self.status_lbl.setText(f"Status: Sync Failed ({message})")
            self.status_lbl.setProperty("status", "error")

        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)