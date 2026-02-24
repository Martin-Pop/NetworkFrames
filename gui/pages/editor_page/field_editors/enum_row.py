from PySide6.QtWidgets import QWidget, QHBoxLayout, QSpinBox, QComboBox
from .base_row import BaseFieldRow


class EnumRow(BaseFieldRow):
    def setup_editor(self):
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        options = getattr(self.field_desc, "i2s", {})
        max_val = self._get_max_value(self.field_desc)

        self.spin_widget = QSpinBox()
        self.spin_widget.setRange(0, max_val)
        current_int = int(self.current_val) if self.current_val is not None else 0
        self.spin_widget.setValue(current_int)

        self.combo_widget = QComboBox()
        self.combo_widget.addItem("Custom / Unknown", -1)

        for v, name in options.items():
            self.combo_widget.addItem(f"{name} ({v})", v)

        self.combo_widget.currentIndexChanged.connect(self._on_combo_changed)
        self.spin_widget.valueChanged.connect(self._on_spin_changed)

        container_layout.addWidget(self.spin_widget, 1)
        container_layout.addWidget(self.combo_widget, 1)

        self.editor_widget = container
        self.mid_layout.insertWidget(0, self.editor_widget)

        self._on_spin_changed(current_int)

    def _on_combo_changed(self, idx):
        data = self.combo_widget.currentData()
        if data != -1:
            self.spin_widget.blockSignals(True)
            self.spin_widget.setValue(int(data))
            self.spin_widget.blockSignals(False)
            self._update_displays_from_int(data)

    def _on_spin_changed(self, val):
        idx = self.combo_widget.findData(val)
        self.combo_widget.blockSignals(True)
        if idx >= 0:
            self.combo_widget.setCurrentIndex(idx)
        else:
            self.combo_widget.setCurrentIndex(0)
        self.combo_widget.blockSignals(False)
        self._update_displays_from_int(val)

    def get_value(self):
        return int(self.spin_widget.value())