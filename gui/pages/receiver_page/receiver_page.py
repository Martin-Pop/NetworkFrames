from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QButtonGroup, QFrame
)
from PySide6.QtCore import Signal, Slot, Qt

from gui.pages.receiver_page.receiver_config_panel import ReceiverConfigurationPanel
from gui.pages.receiver_page.receiver_capture_panel import ReceiverCapturePanel


class ReceiverPage(QWidget):
    # Config Panel signals

    startListening = Signal(dict)
    stopListening = Signal()
    syncRequested = Signal(dict)

    # Capture Panel signals
    clearRequested = Signal()
    saveRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_interfaces = []  # Store data for lookup (IPs/MACs)
        self._init_ui()
        self._connect_internal_signals()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        nav_bar = QFrame()
        nav_bar.setObjectName("receiver_nav_bar")

        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(5)

        self.btn_config = QPushButton("Settings")
        self.btn_config.setCheckable(True)
        self.btn_config.setChecked(True)
        self.btn_config.setMinimumHeight(30)

        self.btn_capture = QPushButton("Captured Packets")
        self.btn_capture.setCheckable(True)
        self.btn_capture.setMinimumHeight(30)

        self.nav_group = QButtonGroup(self)
        self.nav_group.addButton(self.btn_config, 0)
        self.nav_group.addButton(self.btn_capture, 1)
        self.nav_group.idClicked.connect(self._on_nav_clicked)

        nav_layout.addWidget(self.btn_config)
        nav_layout.addWidget(self.btn_capture)
        nav_layout.addStretch()

        layout.addWidget(nav_bar)

        self.stack = QStackedWidget()

        # config
        self.config_panel = ReceiverConfigurationPanel()
        self.stack.addWidget(self.config_panel)

        # capture results
        self.capture_panel = ReceiverCapturePanel()
        self.stack.addWidget(self.capture_panel)

        layout.addWidget(self.stack)

    def _connect_internal_signals(self):
        # Forward signals from panels up to the controller
        self.config_panel.startListening.connect(self.startListening)
        self.config_panel.stopListening.connect(self.stopListening)

        self.config_panel.syncRequested.connect(self.syncRequested)
        self.config_panel.interfaceChanged.connect(self._on_interface_changed)

        self.config_panel.interfaceChanged.connect(self._on_interface_changed)

        self.capture_panel.clearRequested.connect(self.clearRequested)
        self.capture_panel.saveRequested.connect(self.saveRequested)

    def _on_nav_clicked(self, id):
        self.stack.setCurrentIndex(id)

    @Slot()
    def show_config(self):
        self.btn_config.setChecked(True)
        self.stack.setCurrentIndex(0)

    @Slot()
    def show_capture(self):
        self.btn_capture.setChecked(True)
        self.stack.setCurrentIndex(1)

    def set_interfaces(self, int_list):
        """
        Saves interfaces to use and updates the combo box in config panel.
        Matches SenderPage logic.
        :param int_list: list of interfaces [{'name': '...', 'ips': [...], 'mac': '...'}]
        """
        self.current_interfaces = int_list
        names = [interface.get('name') for interface in int_list]
        self.config_panel.set_interfaces(names)

    def _on_interface_changed(self, iface_name):
        """
        Finds the interface data and updates the Info labels in the panel.
        :param iface_name: name of changed interface
        """
        selected_data = next((i for i in self.current_interfaces if i["name"] == iface_name), None)
        self.config_panel.update_local_interface_info(selected_data)

    def set_sync_status(self, success, message=""):
        self.config_panel.set_sync_status(success, message)

    def add_packet_to_table(self, packet_data):
        self.capture_panel.add_packet(packet_data)

    def clear_table(self):
        self.capture_panel.clear_table()

    def set_listener_status(self, is_running, count=0):
        self.config_panel.set_listener_status(is_running, count)