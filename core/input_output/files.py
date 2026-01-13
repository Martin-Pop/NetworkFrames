from PySide6.QtWidgets import QFileDialog


def get_file(parent_widget, file_filter):
    file_path, _ = QFileDialog.getOpenFileName(
        parent_widget,
        "Select a file",
        "",
        file_filter
    )
    return file_path

def save_file(parent_widget, file_filter, default_name=""):
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Save file",
        default_name,
        file_filter
    )
    return file_path