from PySide6.QtCore import QObject


class FuzzingController(QObject):

    def __init__(self, fuzzing_page, frame_manager):
        super().__init__()

        self._fuzzing_page = fuzzing_page
        self._frame_manager = frame_manager
