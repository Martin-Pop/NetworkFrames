from PySide6.QtCore import Signal, QObject
import logging
import json
import os

from utils.files import get_resource_path

log = logging.getLogger(__name__)


class EditorController(QObject):
    editorClosed = Signal()

    def __init__(self, editor_page, frame_manager, protocol_stack):
        super().__init__()

        descriptions_path = get_resource_path("field_descriptions.json")
        self._descriptions = self._load_descriptions(descriptions_path)

        self._editor_page = editor_page
        self._frame_manager = frame_manager
        self._protocol_stack = protocol_stack

        self._current_id = None

        # protocol stack
        self._editor_page.layerAdded.connect(self._on_layer_added)
        self._editor_page.layerRemoved.connect(self._on_layer_removed)
        self._editor_page.layerUpdated.connect(self._on_layer_updated)

        self._editor_page.stackEditorExit.connect(self._on_protocol_stack_editor_exit)
        self._editor_page.saveActivated.connect(self._save_editor)
        self._editor_page.exitActivated.connect(self._close_editor)
        self._editor_page.infoRequested.connect(self._on_info_requested)

    def _load_descriptions(self, filename):
        """
        Loads field descriptions from a JSON file.
        :param filename: json file with field descriptions
        :return: dictionary of field descriptions
        """
        if not os.path.exists(filename):
            log.warning(f"Description file {filename} not found.")
            return {}

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to load descriptions: {e}")
            return {}

    def _on_info_requested(self, layer, field, text):
        """
        Combines technical info from View with descriptive info from JSON.
        :param layer: layer to associate info to
        :param field: field from the layer
        :param text: text to add at the end
        """

        layer_data = self._descriptions.get(layer, {})
        field_data = layer_data.get(field, {})

        verbose_name = field_data.get('verbose_name')
        description = field_data.get('description')

        # title
        final_text = ""
        if verbose_name:
            final_text += f"<h3 style='margin:0; padding:0; color:#2c3e50;'>" \
                          f"{verbose_name} " \
                          f"<span style='color:gray; font-weight:normal;'>({field})</span>" \
                          f"</h3>"
        else:
            final_text += f"<h3 style='margin:0; padding:0;'>{field}</h3>"

        if description:
            final_text += f"{description}"
        else:
            final_text += "<i>No description available.</i>"

        # details
        final_text += "<hr>"
        final_text += text

        self._editor_page.update_info_panel(final_text)

    def _save_editor(self):
        """
        Save the current frame in editor.
        """
        data = self._editor_page.get_editor_data()
        frame = self._frame_manager.get_frame(self._current_id)
        if not frame:
            return

        frame.reconstruct_scapy(data)
        log.info("Frame saved")

    def _close_editor(self):
        """
        Close the editor, calls editorClosed signal so main controller can switch between the main windows / pages.
        """
        self._editor_page.switch(False)
        self.editorClosed.emit()

    def _refresh_stack_ui(self):
        stack = self._protocol_stack.edited_protocol_stack
        can_top = (not stack or stack[-1].current is not None) and bool(self._protocol_stack.get_options_for_insert(len(stack)))
        can_bottom = (not stack or stack[0].current is not None) and bool(self._protocol_stack.get_options_for_insert(0))
        self._editor_page.update_stack_editor(stack, can_top, can_bottom)

    def _on_layer_added(self, index):
        self._protocol_stack.add_empty_node(index)
        self._refresh_stack_ui()

    def _on_layer_removed(self, index):
        self._protocol_stack.remove_node(index)
        self._refresh_stack_ui()

    def _on_layer_updated(self, index, protocol_name):
        self._protocol_stack.update_node(index, protocol_name)
        self._refresh_stack_ui()

    def _on_protocol_stack_editor_exit(self, code):
        """
        Called when protocol stack editor is closed. Updates the protocol stack and then editor page.
        :param code: exit code, 1 = save, 0 = cancel.
        """
        if code == 1:
            self._protocol_stack.save()
            frame = self._frame_manager.get_frame(self._current_id)
            frame.sync_layers(self._protocol_stack.protocol_stack)
            self._editor_page.update_page(self._protocol_stack.protocol_stack, frame.prepare_layers())
        else:
            self._protocol_stack.revert()
            self._refresh_stack_ui()

    def open(self, _id):
        """
        Open an editor. First it clears protocol stack and editor. Then updates them with new frame.
        :param _id:
        """
        if self._current_id:
            self._editor_page.clear_page()
            self._protocol_stack.clear()

        frame = self._frame_manager.get_frame(_id)
        layers = frame.prepare_layers()
        cls_names = [layer.__class__.__name__ for layer in layers]

        self._protocol_stack.load(cls_names)
        self._editor_page.load_page(_id, layers, cls_names)
        self._current_id = _id

        self._refresh_stack_ui()
        self._editor_page.switch(True)

    def close_editor_if_frame_was_deleted(self, ids):
        """
        Closes editor if current frame was deleted.
        :param ids: ids that were deleted
        """
        if self._current_id in ids:
            self._close_editor()