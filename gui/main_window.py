from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt
from .pages.editor_page.editor_page import EditorPage
from .pages.frame_page.frame_page import FramePage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Network Frames")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        control_bar = QWidget()
        control_bar.setObjectName('control_bar')
        control_layout = QHBoxLayout(control_bar)

        self.btn_frames = QPushButton("Frames")
        self.btn_editor = QPushButton("Editor")
        self.btn_settings = QPushButton("Settings")

        self.editor_page = self._create_page("--editor--") #EditorPage()

        control_layout.addWidget(self.btn_frames)
        control_layout.addWidget(self.btn_editor)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_settings)

        self.stacked_widget = QStackedWidget()

        # self.ethernet_page = self._create_page("--editor--")
        self.frame_page = FramePage()
        self.settings_page = self._create_page("--settings--")

        self.stacked_widget.addWidget(self.frame_page)
        self.stacked_widget.addWidget(self.editor_page)
        self.stacked_widget.addWidget(self.settings_page)

        main_layout.addWidget(control_bar)
        main_layout.addWidget(self.stacked_widget)

        self.btn_frames.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_editor.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

    def _create_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel(f"--- {title} ---")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)

        return page