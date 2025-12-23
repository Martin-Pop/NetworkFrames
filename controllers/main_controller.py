from PySide6.QtCore import QObject, Qt, Signal

from controllers.editor_controller import EditorController
from controllers.frame_page_controller import FramePageController
from core.frame_manager import FrameManager
from core.protocol_stack import ProtocolStack
from protocols.protocol_builder import PacketBuilder
from utils.json_loader import load_json_from_file


class MainController(QObject):
    """
    Main controller class acts as coordinator between other controllers.
    """

    def __init__(self, window):
        super().__init__()
        self._window = window

        self._builder = PacketBuilder(load_json_from_file('protocol_map.json'))

        self._frame_manager = FrameManager()
        self._protocol_stack = ProtocolStack(self._builder)

        #controllers
        self._editor_controller = EditorController(self._window.editor_page, self._frame_manager, self._protocol_stack)
        self._frame_page_controller = FramePageController(self._window.frame_page, self._frame_manager)


        self._frame_page_controller.onFrameSelected.connect(self._on_editor_open)
        self._editor_controller.editorClosed.connect(self._on_editor_close)


    def _on_editor_open(self, _id):
        self._editor_controller.open(_id)
        self._window.switch_to_index(1)

    def _on_editor_close(self):
        self._window.switch_to_index(0)