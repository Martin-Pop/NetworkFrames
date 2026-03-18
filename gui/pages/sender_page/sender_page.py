from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSplitter
)
from PySide6.QtCore import Signal, Qt

from gui.pages.sender_page.sender_conf_panel import SenderConfPanel, SenderInfoPanel
from gui.pages.sender_page.sender_stats_panel import SenderStatsPanel
from gui.pages.sender_page.sender_buttons_panel import SenderButtonsPanel

import logging

log = logging.getLogger(__name__)

class SenderPage(QWidget):
    # Re-emit signals to controller
    startClicked = Signal()
    stopClicked = Signal()
    pauseClicked = Signal()
    backClicked = Signal()
    refreshInterfaces = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_interfaces = []  # Store raw data to lookup info
        self._init_ui()
        self._connect_internals()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # target frame
        self.target_widget = QFrame(self)
        self.target_widget.setObjectName('sender_target')
        target_layout = QVBoxLayout(self.target_widget)

        self.frame_label = QLabel("ID / Group: None selected")
        target_layout.addWidget(self.frame_label)

        self.main_layout.addWidget(self.target_widget)

        # conf Conf | Info
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.conf_panel = SenderConfPanel()
        self.info_panel = SenderInfoPanel()

        # need new widgets just for space around splitter bar ? or i cant find some hidden splitter property that does exactly this
        left_w = QWidget()
        left_layout = QVBoxLayout(left_w)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.addWidget(self.conf_panel)

        right_w = QWidget()
        right_layout = QVBoxLayout(right_w)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.addWidget(self.info_panel)

        splitter.addWidget(left_w)
        splitter.addWidget(right_w)

        self.main_layout.addWidget(splitter, 1)

        # 4. actions Stats | Buttons
        action_area = QHBoxLayout()

        self.stats_panel = SenderStatsPanel()
        self.btns_panel = SenderButtonsPanel()

        action_area.addWidget(self.stats_panel, stretch=1)
        action_area.addWidget(self.btns_panel, stretch=0)

        self.main_layout.addLayout(action_area)

    def _connect_internals(self):
        self.conf_panel.interfaceChanged.connect(self._on_interface_changed)
        self.conf_panel.refreshInterfaces.connect(self.refreshInterfaces.emit)

        self.btns_panel.startClicked.connect(self.startClicked)
        self.btns_panel.stopClicked.connect(self.stopClicked)
        self.btns_panel.pauseClicked.connect(self.pauseClicked)
        self.btns_panel.backClicked.connect(self.backClicked)


    def set_interfaces(self, int_list):
        """
        Saves interfaces to use
        :param int_list: list of interfaces
        """
        self.current_interfaces = int_list
        names = [interface.get('name') for interface in int_list]
        self.conf_panel.set_interfaces(names)

    def _on_interface_changed(self, iface_name):
        """
        Finds the interface from the interface list and updates info UI
        :param iface_name: name of the interface
        """
        selected_data = next((i for i in self.current_interfaces if i["name"] == iface_name), None)
        self.info_panel.update_info(selected_data)

    def set_frame_info(self, identification, description):
        self.frame_label.setText(f"ID / Group - {identification}: {description}")
        self.stats_panel.update_count(0)
        self.stats_panel.set_status("Ready", "green")

    def set_running_state(self, is_running):
        self.btns_panel.set_running_state(is_running)
        self.conf_panel.set_locked(is_running)

        if is_running:
            self.stats_panel.set_status("Sending...", "green")
        else:
            self.stats_panel.set_status("Stopped / Finished", "orange")

    def set_pause_state(self, is_paused):
        self.btns_panel.set_pause_state(is_paused)
        if is_paused:
            self.stats_panel.set_status("Paused", "orange")
        else:
            self.stats_panel.set_status("Sending...", "green")

    def show_error(self, message):
        log.error(message)
        self.stats_panel.set_status(message, "red")

    def update_counter(self, count):
        self.stats_panel.update_count(count)

    def get_config(self):
        cfg = self.conf_panel.get_settings()
        return cfg

    def update_receiver_status(self, config):
        self.stats_panel.set_receiver_status(f"{config['remote_ip']}  {config['remote_port']}")