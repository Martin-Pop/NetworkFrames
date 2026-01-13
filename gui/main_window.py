from PySide6.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt
from .pages.editor_page.editor_page import EditorPage
from .pages.frame_page.frame_page import FramePage
from .pages.fuzzing_page.fuzzing_page import FuzzingPage
from .pages.sender_page.sender_page import SenderPage


def _create_page(title):
    """
    Temporary function to create page
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    label = QLabel(f"--- {title} ---")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    layout.addWidget(label)

    return page


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Network Frames")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        control_bar = QWidget()
        control_bar.setObjectName('control_bar')
        self.control_layout = QHBoxLayout(control_bar)

        # pages
        self.stacked_widget = QStackedWidget()
        self.page_map = {}

        #frames
        self.frame_page = FramePage()
        self._init_page(self.frame_page, 'frames')

        #editor
        self.editor_page = EditorPage()
        self._init_page(self.editor_page, 'editor')

        #fuzzer
        self.fuzzing_page = FuzzingPage()
        self._init_page(self.fuzzing_page, 'fuzzing')

        #sender
        self.sender_page = SenderPage()
        self._init_page(self.sender_page, 'sender')

        #receiver
        self.receiver_page = _create_page("--receiver--")
        self._init_page(self.receiver_page, 'receiver')

        # settings
        self.settings_page = _create_page("--settings--")
        self.control_layout.addStretch()
        self._init_page(self.settings_page, 'settings')

        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(control_bar)
        main_layout.addWidget(self.stacked_widget)

        self.switch_to('frames')

    def _init_page(self, page, name):
        self.page_map[name] = self.stacked_widget.addWidget(page)

        btn = QPushButton(name.title())
        btn.setFixedWidth(90)
        btn.setObjectName(name+'_button')
        btn.clicked.connect(lambda: self.switch_to(name))

        self.control_layout.addWidget(btn)


    def switch_to(self, name: str):
        self.stacked_widget.setCurrentIndex(self.page_map[name])
        for i in range(self.stacked_widget.count()):
            widget = self.control_layout.itemAt(i).widget()

            if isinstance(widget, QPushButton):
                is_selected = widget.objectName() == name + '_button'
                widget.setProperty("selected", is_selected)

                widget.style().unpolish(widget)
                widget.style().polish(widget)