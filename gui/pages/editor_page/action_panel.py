from PySide6.QtWidgets import (
    QWidget, QHBoxLayout,QPushButton, QSizePolicy
)

from PySide6.QtCore import Qt, Signal

class ActionPanelWidget(QWidget):

    saveActivated = Signal()
    exitActivated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        self.btn_save = QPushButton("Save")
        self.btn_exit = QPushButton("Exit")

        self.btn_save.clicked.connect(self.saveActivated)
        self.btn_exit.clicked.connect(self.exitActivated)

        for btn in (self.btn_save, self.btn_exit):
            btn.setProperty('styleClass', 'common_button')
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        main_layout.addWidget(self.btn_save)
        main_layout.addWidget(self.btn_exit)