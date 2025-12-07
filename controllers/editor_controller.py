from protocols.protocol_builder import PacketBuilder
from utils.json_loader import load_json_from_file


class EditorController:

    def __init__(self, editor_page):
        self.editor_page = editor_page
        self.protocol_stack_widget = self.editor_page.protocol_stack_widget
        self.protocol_stack_editor_widget = self.protocol_stack_widget.protocol_stack_editor_widget

        self.protocol_stack = [(None,None)]
        self.edited_stack = [(None,None)]
        self.builder = PacketBuilder(load_json_from_file('protocol_map.json'))
        # print(builder.get_possible_lower_protocols('Ether'))

        self.protocol_stack_editor_widget.rebuild(self.edited_stack)
        self.protocol_stack_editor_widget.protocolStackUpdated.connect(self._protocol_stack_updated)

    def _protocol_stack_updated(self, t):

        index, incoming_protocol_name = t

        def get_safe_proto_name(idx):
            if 0 <= idx < len(self.edited_stack):
                item = self.edited_stack[idx]
                if item and isinstance(item[0], str):
                    return item[0]
            return None


        upper_neighbor = get_safe_proto_name(index + 1)
        lower_neighbor = get_safe_proto_name(index - 1)

        # button clicked adding new options
        if incoming_protocol_name is None:

            current_proto = self.edited_stack[index][0]
            options = self.builder.get_commutable_protocols(
                upper_neighbor,
                lower_neighbor
            )

            self.edited_stack[index] = (current_proto, options)

            print(f"Index {index}: Options calculated based on Low:{lower_neighbor} & Up:{upper_neighbor} -> {options}")

        else:

            old_options = self.edited_stack[index][1]
            self.edited_stack[index] = (incoming_protocol_name, old_options)

            print(f"Index {index}: Selected {incoming_protocol_name}")

            possible_upper = self.builder.get_possible_upper_protocols(incoming_protocol_name)
            possible_lower = self.builder.get_possible_lower_protocols(incoming_protocol_name)

            if upper_neighbor:
                self.edited_stack[index+1] = (upper_neighbor, possible_upper)
                print('updated upper_neighbor options')

            if lower_neighbor:
                self.edited_stack[index-1] = (lower_neighbor, possible_lower)
                print('updated lower_neighbor options')

            # try to add above
            if index == len(self.edited_stack) - 1 and possible_upper:
                self.edited_stack.append((None, None))
                print("  -> Added extension button ABOVE")

            # try to add bellow
            if index == 0 and possible_lower:
                self.edited_stack.insert(0, (None, None))
                print("  -> Added extension button BELOW")




        self.protocol_stack_editor_widget.rebuild(self.edited_stack)
