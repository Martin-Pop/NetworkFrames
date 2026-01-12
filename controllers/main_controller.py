from PySide6.QtCore import QObject, Qt, Signal

from controllers.editor_controller import EditorController
from controllers.frame_page_controller import FramePageController
from controllers.sender_controller import SenderController
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

        #editor controller
        self._editor_controller = EditorController(self._window.editor_page, self._frame_manager,self._builder, self._protocol_stack)
        self._editor_controller.editorClosed.connect(self._on_editor_close)

        # frames
        self._frame_page_controller = FramePageController(self._window.frame_page, self._frame_manager)
        self._frame_page_controller.onFrameSelected.connect(self._on_editor_open)
        self._frame_page_controller.sendRequest.connect(self._on_send_frames_request)

        # sender
        self._sender_controller = SenderController(self._window.sender_page, self._frame_manager)
        self._sender_controller.senderClosed.connect(self._on_sender_closed)

    def _on_editor_open(self, _id):
        """
        Opens editor
        :param _id: id of frame to edit
        """
        self._editor_controller.open(_id)
        self._window.switch_to('editor')

    def _on_editor_close(self):
        """
        Closes editor by switching to frames page
        :return:
        """
        self._window.switch_to('frames')

    def _on_send_frames_request(self, ids):
        """
        Opens sender
        """
        self._sender_controller.load_frames(ids)
        self._window.switch_to('sender')

    def _on_sender_closed(self):
        """
        Closes sender by switching to frames page
        :return:
        """
        self._window.switch_to('frames')