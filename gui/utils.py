from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QFileDialog


def setup_placeholder(label_text):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    label = QLabel(label_text)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)

    return widget

def get_file(parent_widget, file_filter):
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select a file",
        "",
        file_filter
    )
    return file_path
