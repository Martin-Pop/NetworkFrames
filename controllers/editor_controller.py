
class EditorController:

    def __init__(self, editor_page, frame_manager, protocol_stack):

        self._editor_page = editor_page
        self._frame_manager = frame_manager
        self._protocol_stack = protocol_stack

        self._current_id = None


        # protocol stack
        self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)
        # self._stack_widget = editor_page.protocol_stack_widget
        # self._stack_widget.editor_widget.rebuild(self._stack.edited_protocol_stack)
        #
        # # protocol editor
        # self._protocol_editor = editor_page.editor_widget
        #
        # self._stack_widget.editor_widget.stackUpdated.connect(self._protocol_stack_updated) #do signal chaining instead of direct connect?
        # self._stack_widget.editor_widget.finished.connect(self._on_editor_exit)
        self._editor_page.stackUpdated.connect(self._protocol_stack_updated)
        self._editor_page.stackEditorExit.connect(self._on_protocol_editor_exit)

    def _protocol_stack_updated(self, t):
        self._protocol_stack.update(t)
        self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)

    def _on_protocol_editor_exit(self, code):
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

        if self._current_id:
            #save?
            self._editor_page.clear_page()
            self._protocol_stack.clear()

        frame = self._frame_manager.get_frame(_id)

        # print(_id, frame)
        # data = frame.prepare_data_for_editor()
        # print(data)
        # layers = [protocol["class_name"] for protocol in data]

        layers = frame.prepare_layers()
        cls_names = [layer.__class__.__name__ for layer in layers]

        # self._protocol_stack.load(layers)
        # self._editor_page.load_page(_id, data)
        self._protocol_stack.load(cls_names)
        self._editor_page.load_page(_id, layers, cls_names)
        self._editor_page.update_stack_editor(self._protocol_stack.edited_protocol_stack)
        self._protocol_stack.save()
        self._current_id = _id