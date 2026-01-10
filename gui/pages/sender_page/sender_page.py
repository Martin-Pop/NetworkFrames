from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QGroupBox, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Signal, Qt


class SenderPage(QWidget):

    startClicked = Signal()
    stopClicked = Signal()
    exitActivated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # header
        title_label = QLabel("Packet Sender")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        self.main_layout.addWidget(title_label)

        # info
        self.info_group = QGroupBox("Target Frame")
        self.info_layout = QVBoxLayout(self.info_group)

        self.frame_name_label = QLabel("- No frame selected -")
        self.frame_name_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #E8834A;")
        self.info_layout.addWidget(self.frame_name_label)

        self.main_layout.addWidget(self.info_group)

        # config
        self.config_group = QGroupBox("Configuration")
        self.form_layout = QFormLayout(self.config_group)
        self.form_layout.setSpacing(10)

        # Interface selection
        self.interface_combo = QComboBox()
        self.form_layout.addRow("Interface:", self.interface_combo)

        # send count
        self.count_spin = QSpinBox()
        self.count_spin.setRange(-1, 999999)
        self.count_spin.setValue(1)
        self.count_spin.setSpecialValueText("Infinite Loop")  # if -1 => inf loop
        self.form_layout.addRow("Count:", self.count_spin)

        # interval
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.0, 60.0)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setValue(0.1)
        self.interval_spin.setSuffix(" sec")
        self.form_layout.addRow("Interval:", self.interval_spin)

        self.main_layout.addWidget(self.config_group)

        # fuzzing wip
        self.fuzz_group = QGroupBox("Fuzzing & Modification")
        fuzz_layout = QVBoxLayout(self.fuzz_group)

        self.fuzz_checkbox = QCheckBox("Enable Fuzzing / Malformation")
        self.fuzz_checkbox.setToolTip("If checked, packet fields might be randomized based on rules.")
        fuzz_layout.addWidget(self.fuzz_checkbox)

        # fuzzing config here

        self.main_layout.addWidget(self.fuzz_group)

        # status ---
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        status_layout = QHBoxLayout(self.status_frame)

        self.counter_label = QLabel("Sent: 0")
        self.counter_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray;")

        status_layout.addWidget(self.counter_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)

        self.main_layout.addWidget(self.status_frame)

        self.main_layout.addStretch()

        # actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        # Start Button
        self.btn_start = QPushButton("Start Sending")
        self.btn_start.setMinimumHeight(40)

        self.btn_start.clicked.connect(self.startClicked.emit)

        # Stop Button
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)

        self.btn_stop.clicked.connect(self.stopClicked.emit)

        # Exit Button
        self.btn_exit = QPushButton("Back")
        self.btn_exit.setMinimumHeight(40)

        self.btn_exit.clicked.connect(self.exitActivated.emit)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_exit)

        self.main_layout.addLayout(btn_layout)


    def set_interfaces(self, iface_list):
        self.interface_combo.clear()
        for iface in iface_list:
            name = str(iface)
            self.interface_combo.addItem(name)

    def set_frame_info(self, frame_name):
        self.frame_name_label.setText(f"Frame: {frame_name}")
        self.counter_label.setText("Sent: 0")
        self.status_label.setText("Ready")
        self.status_label.setStyleSheet("color: gray;")

    def get_selected_interface(self):
        return self.interface_combo.currentText()

    def get_count(self):
        return self.count_spin.value()

    def get_interval(self):
        return self.interval_spin.value()

    def is_fuzzing_enabled(self):
        return self.fuzz_checkbox.isChecked()

    def update_counter(self, count):
        self.counter_label.setText(f"Sent: {count}")

    def show_error(self, message):
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def set_running_state(self, is_running):

        self.btn_start.setEnabled(not is_running)
        self.btn_stop.setEnabled(is_running)
        self.btn_exit.setEnabled(not is_running)

        self.config_group.setEnabled(not is_running)
        self.fuzz_group.setEnabled(not is_running)
        self.info_group.setEnabled(not is_running)

        if is_running:
            self.status_label.setText("Sending...")
            self.status_label.setStyleSheet("color: #E8834A; font-weight: bold;")
        else:
            self.status_label.setText("Finished / Stopped")
            self.status_label.setStyleSheet("color: green;")