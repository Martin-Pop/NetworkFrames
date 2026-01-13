from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QStackedWidget,
    QSpinBox, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt


class FuzzingStrategyPanel(QWidget):
    """
    Panel for configuring HOW to fuzz the selected field.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fuzz_strategy_panel")
        self._init_ui()

        # self.setEnabled(False)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # header
        lbl = QLabel("2. Configure Strategy")
        lbl.setStyleSheet("font-weight: bold; color: @SECONDARY;")
        layout.addWidget(lbl)

        container = QWidget()
        container.setObjectName("sender_conf")  # reuse
        c_layout = QVBoxLayout(container)

        # strategy
        c_layout.addWidget(QLabel("Method:"))
        self.combo_strategy = QComboBox()
        self.combo_strategy.addItems(["Random Integer", "Bit Flip"])
        self.combo_strategy.currentIndexChanged.connect(self._on_strategy_changed)
        c_layout.addWidget(self.combo_strategy)

        c_layout.addSpacing(10)

        # dynamic settings based on strategy
        self.stack = QStackedWidget()

        # 1 - random int
        self.page_random = QWidget()
        l_rand = QVBoxLayout(self.page_random)
        l_rand.setContentsMargins(0, 0, 0, 0)

        self.spin_min = QSpinBox()
        self.spin_min.setRange(-99999999, 99999999)
        self.spin_min.setValue(0)

        self.spin_max = QSpinBox()
        self.spin_max.setRange(-99999999, 99999999)
        self.spin_max.setValue(65535)

        l_rand.addWidget(QLabel("Min Value:"))
        l_rand.addWidget(self.spin_min)
        l_rand.addWidget(QLabel("Max Value:"))
        l_rand.addWidget(self.spin_max)
        l_rand.addStretch()
        self.stack.addWidget(self.page_random)

        # 2 - bit flip
        self.page_flip = QWidget()
        l_flip = QVBoxLayout(self.page_flip)
        l_flip.addWidget(QLabel("Randomly flips bits in the value."))
        l_flip.addStretch()
        self.stack.addWidget(self.page_flip)

        c_layout.addWidget(self.stack)

        c_layout.addSpacing(15)

        #count
        c_layout.addWidget(QLabel("Frame Count (Limit 5000):"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 5000)
        self.spin_count.setValue(50)
        c_layout.addWidget(self.spin_count)

        c_layout.addStretch()

        layout.addWidget(container)

    def _on_strategy_changed(self, index):
        self.stack.setCurrentIndex(index)

    def set_locked(self, locked):
        self.setEnabled(not locked)

    def get_settings(self):
        """
        Returns config dict
        """
        strategy = self.combo_strategy.currentText()

        cfg = {
            "strategy": strategy,
            "count": self.spin_count.value(),
            "params": {}
        }

        if strategy == "Random Integer":
            cfg["params"] = {
                "min": self.spin_min.value(),
                "max": self.spin_max.value()
            }

        return cfg