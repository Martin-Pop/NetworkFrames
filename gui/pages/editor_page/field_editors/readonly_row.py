from PySide6.QtWidgets import QLabel
from .base_row import BaseFieldRow

class ReadOnlyRow(BaseFieldRow):
    def setup_editor(self):
        repr_val = "None"
        if self.current_val is not None:
            try:
                repr_val = self.field_desc.i2repr(None, self.current_val)
            except Exception:
                repr_val = str(self.current_val)

        self.editor_widget = QLabel(repr_val)
        self.editor_widget.setStyleSheet("color: gray; font-style: italic;")
        self.mid_layout.insertWidget(0, self.editor_widget)

        self.hex_display.setText("-")
        self.bin_display.setText("-")

    def get_value(self):
        return self.current_val