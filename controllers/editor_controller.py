from PySide6.QtCore import Signal, QObject
from scapy.compat import raw

class EditorController(QObject):

    editorClosed = Signal()

    def __init__(self, editor_page, frame_manager, protocol_stack):
        super().__init__()

        self._editor_page = editor_page
        self._frame_manager = frame_manager
        self._protocol_stack = protocol_stack

        self._current_id = None

        # protocol stack
        # self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)
        self._editor_page.stackUpdated.connect(self._protocol_stack_editor_updated)
        self._editor_page.stackEditorExit.connect(self._on_protocol_stack_editor_exit)
        self._editor_page.saveActivated.connect(self._save_editor)
        self._editor_page.exitActivated.connect(self._close_editor)

    def _save_editor(self):
        """
        Save the current frame in editor.
        """
        data = self._editor_page.get_editor_data()
        frame = self._frame_manager.get_frame(self._current_id)
        frame.reconstruct_scapy(data)
        raw(frame.scapy)
        print(frame.scapy.show())

    def _close_editor(self):
        """
        Close the editor, calls editorClosed signal so main controller can switch between the main windows / pages.
        """
        self._editor_page.switch(False)
        self.editorClosed.emit()

    def _protocol_stack_editor_updated(self, t):
        """
        Called when protocol stack editor is updated. Updates the stack, based on 't', then updates the protocol stack editor with new stack.
        Necessary to get handle logic for protocols / layers stacking.
        :param t: (index - index to update, incoming_protocol_name - name of the incoming protocol or None)
        """
        self._protocol_stack.update(t)
        self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)

    def _on_protocol_stack_editor_exit(self, code):
        """
        Called when protocol stack editor is closed. Updates the protocol stack and then editor page.
        :param code: exit code, 1 = save, 0 = cancel.
        """
        if code == 1:
            self._protocol_stack.save()
            frame = self._frame_manager.get_frame(self._current_id)
            frame.sync_layers(self._protocol_stack.protocol_stack)
            # self._editor_page.update_page(self._protocol_stack.protocol_stack, frame.prepare_data_for_editor())
            self._editor_page.update_page(self._protocol_stack.protocol_stack, frame.prepare_layers())
        else:
            self._protocol_stack.revert()
            self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)

    def open(self, _id):
        """
        Open an editor. First it clears protocol stack and editor. Then updates them with new frame.
        :param _id:
        :return:
        """
        if self._current_id:
            #save?
            self._editor_page.clear_page()
            self._protocol_stack.clear()

        frame = self._frame_manager.get_frame(_id)

        layers = frame.prepare_layers()
        cls_names = [layer.__class__.__name__ for layer in layers]

        self._protocol_stack.load(cls_names)
        self._editor_page.load_page(_id, layers, cls_names)
        self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)
        # self._protocol_stack.save()
        self._current_id = _id

        self._editor_page.switch(True)