from PySide6.QtWidgets import QGroupBox, QGridLayout, QCheckBox
from .base_row import BaseFieldRow

class FlagsRow(BaseFieldRow):
    def setup_editor(self):
        self.editor_widget = QGroupBox()
        self.editor_widget.setStyleSheet("border: none; margin: 0; padding: 0;")
        flags_layout = QGridLayout(self.editor_widget)
        flags_layout.setContentsMargins(0, 0, 0, 0)

        self.checkboxes = []
        flag_names = getattr(self.field_desc, "names", [])
        current_int = int(self.current_val) if self.current_val is not None else 0

        for i, name in enumerate(flag_names):
            chk = QCheckBox(name)
            mask = 1 << i
            chk.setProperty("mask", mask)
            if current_int & mask:
                chk.setChecked(True)

            chk.toggled.connect(self._on_flags_changed)
            self.checkboxes.append(chk)
            flags_layout.addWidget(chk, i // 2, i % 2)

        self.mid_layout.insertWidget(0, self.editor_widget)
        self._on_flags_changed()

    def _on_flags_changed(self):
        total = self.get_value()
        self._update_displays_from_int(total)

    def get_value(self):
        total = 0
        for chk in self.checkboxes:
            if chk.isChecked():
                total |= chk.property("mask")
        return total