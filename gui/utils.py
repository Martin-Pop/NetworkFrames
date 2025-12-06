from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

def setup_placeholder(widget, label_text):
    layout = QVBoxLayout(widget)
    label = QLabel(label_text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)