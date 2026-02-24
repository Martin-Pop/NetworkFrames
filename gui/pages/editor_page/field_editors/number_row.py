from PySide6.QtWidgets import QDoubleSpinBox
from .base_row import BaseFieldRow


class NumberRow(BaseFieldRow):
    def setup_editor(self):
        self.editor_widget = QDoubleSpinBox()
        self.editor_widget.setDecimals(0)
        max_val = self._get_max_value(self.field_desc)
        self.editor_widget.setRange(-1, max_val)
        self.editor_widget.setSpecialValueText("Auto")

        initial_val = int(self.current_val) if self.current_val is not None else -1
        self.editor_widget.setValue(initial_val)

        self.mid_layout.insertWidget(0, self.editor_widget)
        self.editor_widget.valueChanged.connect(self._on_value_changed)
        self._on_value_changed(self.editor_widget.value())

    def _on_value_changed(self, val):
        self._update_displays_from_int(int(val))

    def get_value(self):
        return int(self.editor_widget.value())