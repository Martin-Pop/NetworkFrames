from protocols.protocol_builder import PacketBuilder
from utils.json_loader import load_json_from_file


class EditorController:

    def __init__(self, editor_page):
        self.editor_page = editor_page
        self.protocol_stack_widget = self.editor_page.protocol_stack_widget
        # self.protocol_stack_widget.protocolSelected

        self.protocol_stack_editor_widget = self.protocol_stack_widget.protocol_stack_editor_widget

        self.protocol_stack = []
        self.saved_edited_stack = [(None,None)]
        self.edited_stack = [(None,None)]

        self.builder = PacketBuilder(load_json_from_file('protocol_map.json'))

        self.protocol_stack_editor_widget.rebuild(self.edited_stack)
        self.protocol_stack_editor_widget.protocolStackUpdated.connect(self._protocol_stack_updated)
        self.protocol_stack_editor_widget.finished.connect(self._stack_editor_closed)

    def _stack_editor_closed(self, code):
        if code == 1:
            self.saved_edited_stack = self.edited_stack.copy()

            names = []
            for part in self.edited_stack:
                if part[0] is not None:
                    names.append(part[0])

            self.protocol_stack = names
            self.protocol_stack_widget.update_buttons(names)
        else:
            self.edited_stack = self.saved_edited_stack.copy()
            self.protocol_stack_editor_widget.rebuild(self.edited_stack)


    def _protocol_stack_updated(self, t):
        index, incoming_protocol_name = t

        def get_safe_proto_name(idx):
            if 0 <= idx < len(self.edited_stack):
                item = self.edited_stack[idx]
                if item and isinstance(item[0], str):
                    return item[0]
            return None

        upper_protocol = get_safe_proto_name(index + 1)
        lower_protocol = get_safe_proto_name(index - 1)

        if incoming_protocol_name is None:

            current_proto = self.edited_stack[index][0]
            options = self.builder.get_commutable_protocols(
                upper_protocol,
                lower_protocol
            )

            self.edited_stack[index] = (current_proto, options)

        else:
            old_options = self.edited_stack[index][1]
            self.edited_stack[index] = (incoming_protocol_name, old_options)

            possible_upper = self.builder.get_possible_upper_protocols(incoming_protocol_name)
            possible_lower = self.builder.get_possible_lower_protocols(incoming_protocol_name)

            #print('index is', index,'upper_neighbor is', upper_protocol, 'lower_neighbor is', lower_protocol, 'possible_upper', possible_upper, 'possible_lower', possible_lower)

            if upper_protocol and possible_upper:
                self.edited_stack[index+1] = (upper_protocol, possible_upper)

            if lower_protocol and possible_lower:
                self.edited_stack[index-1] = (lower_protocol, possible_lower)

            if not possible_upper and index + 1 == len(self.edited_stack) - 1:
                del self.edited_stack[index + 1]

            if not possible_lower and index - 1 == 0:
                del self.edited_stack[index - 1]

            if not upper_protocol and possible_upper:
                try:
                    self.edited_stack[index+1] = (None, None)
                except IndexError:
                    self.edited_stack.append((None, None))

            if not lower_protocol and possible_lower:
                if index-1 >= 0:
                    self.edited_stack[index-1] = (None, None)
                else:
                    self.edited_stack.insert(0,(None, None))

        # print(self.edited_stack)
        self.protocol_stack_editor_widget.rebuild(self.edited_stack)