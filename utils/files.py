from PySide6.QtWidgets import QFileDialog
import os
import sys

def get_resource_path(relative_path):
    """
    Gets abs path for a file
    Works for local execution and for PyInstaller
    :param relative_path: relative path to resolve
    """
    try:
        # pyinstallers temp path is stored in sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

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