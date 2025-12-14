from PySide6.QtWidgets import (
    QWidget, QHBoxLayout,QPushButton,
)

class ActionPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(5)

        self.btn_build = QPushButton("Build")
        self.btn_build.setProperty('styleClass', 'common_button')
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setProperty('styleClass', 'common_button')

        main_layout.addWidget(self.btn_build)
        main_layout.addStretch()
        main_layout.addWidget(self.btn_clear)