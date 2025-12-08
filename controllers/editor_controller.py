from protocols.protocol_builder import PacketBuilder
from utils.json_loader import load_json_from_file
from core.protocol_stack import ProtocolStack


class EditorController:

    def __init__(self, editor_page):

        self._editor_page = editor_page
        self._builder = PacketBuilder(load_json_from_file('protocol_map.json'))

        # protocol stack
        self._stack = ProtocolStack(self._builder)
        self._stack_widget = editor_page.protocol_stack_widget
        self._stack_widget.editor.rebuild(self._stack.edited_protocol_stack)

        self._stack_widget.editor.stackUpdated.connect(self._protocol_stack_updated)
        self._stack_widget.editor.finished.connect(self._on_editor_exit)


    def _protocol_stack_updated(self, t):
        self._stack.update_stack(t)
        self._stack_widget.editor.rebuild(self._stack.edited_protocol_stack)

    def _on_editor_exit(self, code):
        print('code is',code)
        if code == 1:
            self._stack.save()
            self._stack_widget.update_buttons(self._stack.protocol_stack)
        else:
            self._stack.revert()
            self._stack_widget.editor.rebuild(self._stack.edited_protocol_stack)
