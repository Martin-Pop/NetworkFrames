from PySide6.QtCore import QObject

from controllers.editor_controller import EditorController
from controllers.frame_page_controller import FramePageController
from core.frame_manager import FrameManager


class MainController(QObject):
    """
    Main controller class acts as coordinator between other controllers.
    """

    def __init__(self, window):
        super().__init__()
        self._window = window
        self._frame_manager = FrameManager()

        #controllers
        self._editor_controller = EditorController(self._window.editor_page)
        self._frame_page_controller = FramePageController(self._window.frame_page, self._frame_manager)

        self._frame_page_controller.onFrameSelected.connect(lambda _id: self._editor_controller.open(_id))