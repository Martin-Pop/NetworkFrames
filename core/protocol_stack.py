from dataclasses import dataclass

@dataclass
class ProtocolNode:
    current: str | None
    options: list[str] | None

class ProtocolStack:

    def __init__(self, builder):
        self._builder = builder

        self._protocol_stack = []
        self._edited_protocol_stack = [ProtocolNode(None,None)]
        self._backup_edited_protocol_stack = [ProtocolNode(None,None)]

    @property
    def protocol_stack(self):
        return self._protocol_stack

    @property
    def edited_protocol_stack(self):
        return self._edited_protocol_stack

    def clear(self):
        self._protocol_stack = []
        self._edited_protocol_stack = [ProtocolNode(None,None)]
        self._backup_edited_protocol_stack = [ProtocolNode(None,None)]

    def load(self, layers):
        for index, layer in enumerate(layers):
            self.update((index, layer))

        self.save()

    def backup(self):
        self._backup_edited_protocol_stack = self._edited_protocol_stack.copy()

    def save(self):
        self.backup()

        names = []
        for node in self._edited_protocol_stack:
            if node.current is not None:
                names.append(node.current)

        self._protocol_stack = names

    def revert(self):
        self._edited_protocol_stack = self._backup_edited_protocol_stack.copy()

    def update(self, t):
        index, incoming_protocol_name = t

        def get_safe_proto_name(idx):
            if 0 <= idx < len(self._edited_protocol_stack):
                item = self._edited_protocol_stack[idx]
                if item.current is not None:
                    return item.current
            return None

        upper_protocol = get_safe_proto_name(index + 1)
        lower_protocol = get_safe_proto_name(index - 1)

        if incoming_protocol_name is None:

            current_proto = self._edited_protocol_stack[index].current
            options = self._builder.get_commutable_protocols(
                upper_protocol,
                lower_protocol
            )

            self._edited_protocol_stack[index] = ProtocolNode(current_proto, options)

        else:

            if not self._builder.is_supported(incoming_protocol_name):
                print('UNSUPPORTED PROTOCOL NAME', incoming_protocol_name)
                if 0 <= index < len(self._edited_protocol_stack):
                    self._edited_protocol_stack[index] = ProtocolNode(incoming_protocol_name, [incoming_protocol_name])
                else:
                    self._edited_protocol_stack.append(ProtocolNode(incoming_protocol_name, [incoming_protocol_name]))
                return

            old_options = self._edited_protocol_stack[index].options
            if old_options is None: #when loading from file
                old_options = [incoming_protocol_name]
            self._edited_protocol_stack[index] = ProtocolNode(incoming_protocol_name, old_options)

            possible_upper = self._builder.get_possible_upper_protocols(incoming_protocol_name)
            possible_lower = self._builder.get_possible_lower_protocols(incoming_protocol_name)

            print('index is', index,'upper_neighbor is', upper_protocol, 'lower_neighbor is', lower_protocol, 'possible_upper', possible_upper, 'possible_lower', possible_lower)

            if upper_protocol and possible_upper:
                self._edited_protocol_stack[index + 1] = ProtocolNode(upper_protocol, possible_upper)

            if lower_protocol and possible_lower:
                self._edited_protocol_stack[index - 1] = ProtocolNode(lower_protocol, possible_lower)

            if not possible_upper and index + 1 == len(self._edited_protocol_stack) - 1:
                del self._edited_protocol_stack[index + 1]

            if not possible_lower and index - 1 == 0:
                del self._edited_protocol_stack[index - 1]

            if not upper_protocol and possible_upper:
                try:
                    self._edited_protocol_stack[index + 1] = ProtocolNode(None, None)
                except IndexError:
                    self._edited_protocol_stack.append(ProtocolNode(None, None))

            if not lower_protocol and possible_lower:
                if index - 1 >= 0:
                    self._edited_protocol_stack[index - 1] = ProtocolNode(None, None)
                else:
                    self._edited_protocol_stack.insert(0, ProtocolNode(None, None))