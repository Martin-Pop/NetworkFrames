from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QSplitter
)
from PySide6.QtCore import Signal, Qt

from gui.pages.fuzzing_page.fuzzing_target_panel import FuzzingTargetPanel
from gui.pages.fuzzing_page.fuzzing_strategy_panel import FuzzingStrategyPanel
from gui.pages.fuzzing_page.fuzzing_buttons_panel import FuzzingButtonsPanel


class FuzzingPage(QWidget):

    generateClicked = Signal()
    backClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_internals()

        self.current_layer = None
        self.current_field = None

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # header
        self.header_widget = QFrame(self)
        self.header_widget.setObjectName('sender_target')  # reuse
        header_layout = QVBoxLayout(self.header_widget)

        self.frame_label = QLabel("Fuzzing Session: { No Frame Selected }")
        header_layout.addWidget(self.frame_label)

        self.main_layout.addWidget(self.header_widget)

        # middle (target tree | strategy conf)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.target_panel = FuzzingTargetPanel()
        self.strategy_panel = FuzzingStrategyPanel()

        left_w = QWidget()
        left_layout = QVBoxLayout(left_w)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.addWidget(self.target_panel)

        right_w = QWidget()
        right_layout = QVBoxLayout(right_w)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.addWidget(self.strategy_panel)

        splitter.addWidget(left_w)
        splitter.addWidget(right_w)

        # does this even work?
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        self.main_layout.addWidget(splitter)

        self.main_layout.addStretch()

        # buttons
        self.btns_panel = FuzzingButtonsPanel()
        self.main_layout.addWidget(self.btns_panel)

    def _connect_internals(self):
        self.target_panel.fieldSelected.connect(self._on_target_selected)

        # Buttons
        self.btns_panel.generateClicked.connect(self.generateClicked)
        self.btns_panel.backClicked.connect(self.backClicked)

    def set_frame(self, frame_desc, scapy_pkt):
        """
        Sets the frame and resets the UI
        :param frame_desc: description of the frame
        :param scapy_pkt: scapy object
        """
        self.frame_label.setText(f"Fuzzing Session: {frame_desc}")

        # load tree
        self.target_panel.load_packet_structure(scapy_pkt)

        # reset
        self.strategy_panel.setEnabled(False)
        self.btns_panel.set_generate_enabled(False)
        self.btns_panel.set_status("Please select a field to fuzz")
        self.current_layer = None
        self.current_field = None

    def reset_fuzzer(self):
        self.frame_label.setText("Fuzzing Session: { No Frame Selected }")
        self.target_panel.reset()
        self.strategy_panel.setEnabled(True)
        self.btns_panel.set_generate_enabled(True)
        self.current_layer = None
        self.current_field = None

    def _on_target_selected(self, layer, field):
        #unlock settings

        self.current_layer = layer
        self.current_field = field

        self.strategy_panel.setEnabled(True)
        self.btns_panel.set_generate_enabled(True)
        self.btns_panel.set_status(f"Selected: {layer} -> {field}", "green")

    def get_config(self):
        strat_cfg = self.strategy_panel.get_settings()
        return {
            "target_layer": self.current_layer,
            "target_field": self.current_field,
            "strategy": strat_cfg["strategy"],
            "count": strat_cfg["count"],
            "params": strat_cfg["params"]
        }