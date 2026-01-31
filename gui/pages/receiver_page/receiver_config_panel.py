from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QSpinBox, QPushButton,
    QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
import logging

log = logging.getLogger(__name__)


class ReceiverRemotePanel(QFrame):
    """
    Left/Top panel: Remote Device Settings.
    Contains inputs for remote IP/Port and a Test Connection button.
    """
    syncRequested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('receiver_remote_panel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

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
        self.ip_input.textChanged.connect(self._validate_inputs)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(5000)

        self.form_layout.addRow("Remote IP:", self.ip_input)
        self.form_layout.addRow("Remote Port:", self.port_spin)

        layout.addLayout(self.form_layout)

        self.sync_btn = QPushButton("Test Connection")
        self.sync_btn.setMinimumHeight(35)
        self.sync_btn.setProperty("styleClass", "common_button")
        self.sync_btn.setEnabled(False)  # Disabled by default
        self.sync_btn.clicked.connect(self._on_sync_clicked)

        layout.addStretch()
        layout.addWidget(self.sync_btn)

    def _validate_inputs(self):
        text = self.ip_input.text().strip()
        self.sync_btn.setEnabled(len(text) > 0)

    def _on_sync_clicked(self):
        data = self.get_data()
        self.syncRequested.emit(data)

    def get_data(self):
        return {
            "remote_ip": self.ip_input.text(),
            "remote_port": self.port_spin.value()
        }

    def set_sync_status(self, success, message=""):
        if success:
            self.sync_btn.setText(f"Connected! ({message})")
        else:
            self.sync_btn.setText(f"Failed ({message})")


class ReceiverLocalPanel(QFrame):
    """
    Right/Bottom panel: Local Settings.
    Controls the Listener server directly.
    """
    interfaceChanged = Signal(str)
    startListening = Signal(dict)  # Emits config when start requested
    stopListening = Signal()  # Emits when stop requested

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._init_ui()

    def _init_ui(self):
        self.setObjectName('receiver_local_panel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

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

        self.status_lbl = QLabel("Status: Inactive")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.status_lbl)

        self.action_btn = QPushButton("Start Listening")
        self.action_btn.setMinimumHeight(35)
        self.action_btn.setProperty("styleClass", "common_button")  # Or 'action_button'
        self.action_btn.clicked.connect(self._on_action_clicked)

        layout.addStretch()
        layout.addWidget(self.action_btn)

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
        self.lbl_ip.setText('\n'.join(ips) if ips else "Unknown")
        self.lbl_mac.setText(interface_data.get("mac", "Unknown"))

    def _on_action_clicked(self):
        if self._is_running:
            self.stopListening.emit()
        else:
            config = self.get_data()
            self.startListening.emit(config)

    def set_listening_state(self, is_running, client_count=0):
        """
        Updates the UI to reflect the engine state.
        """
        self._is_running = is_running

        if is_running:
            self.action_btn.setText("Stop Listening")

            if client_count > 0:
                self.status_lbl.setText(f"Status: Active ({client_count} connected)")
                self.status_lbl.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_lbl.setText("Status: Listening...")
                self.status_lbl.setStyleSheet("color: green; font-weight: bold;")

            # Lock inputs while running
            self.interface_combo.setEnabled(False)
            self.port_spin.setEnabled(False)
        else:
            self.action_btn.setText("Start Listening")
            self.status_lbl.setText("Status: Inactive")
            self.status_lbl.setStyleSheet("color: gray; font-weight: bold;")

            # Unlock inputs
            self.interface_combo.setEnabled(True)
            self.port_spin.setEnabled(True)

    def get_data(self):
        return {
            "local_iface": self.interface_combo.currentText(),
            "local_port": self.port_spin.value()
        }


class ReceiverConfigurationPanel(QWidget):
    """
    Main container.
    """
    # Signals to Controller
    startListening = Signal(dict)  # Formerly configSaved
    stopListening = Signal()
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
        # Footer is gone, buttons are inside panels

    def _connect_signals(self):
        self.local_panel.interfaceChanged.connect(self.interfaceChanged)
        self.local_panel.startListening.connect(self.startListening)
        self.local_panel.stopListening.connect(self.stopListening)

        self.remote_panel.syncRequested.connect(self.syncRequested)

    def set_interfaces(self, ifaces):
        self.local_panel.set_interfaces(ifaces)

    def update_local_interface_info(self, interface_data):
        self.local_panel.update_interface_info(interface_data)

    def set_sync_status(self, success, message=""):
        self.remote_panel.set_sync_status(success, message)

    def set_listener_status(self, is_running, client_count=0):
        self.local_panel.set_listening_state(is_running, client_count)

    def get_remote_config(self):
        return self.remote_panel.get_data()

    def get_local_config(self):
        return self.local_panel.get_data()