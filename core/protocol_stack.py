class ProtocolStack:

    def __init__(self, builder):
        self._builder = builder

        self._protocol_stack = []
        self._edited_protocol_stack = [(None,None)]
        self._backup_edited_protocol_stack = [(None,None)]

    @property
    def protocol_stack(self):
        return self._protocol_stack

    @property
    def edited_protocol_stack(self):
        return self._edited_protocol_stack

    def backup(self):
        self._backup_edited_protocol_stack = self._edited_protocol_stack.copy()

    def save(self):
        self.backup()

        names = []
        for part in self._edited_protocol_stack:
            if part[0] is not None:
                names.append(part[0])

        self._protocol_stack = names

    def revert(self):
        self._edited_protocol_stack = self._backup_edited_protocol_stack.copy()

    def update_stack(self, t):
        index, incoming_protocol_name = t

        def get_safe_proto_name(idx):
            if 0 <= idx < len(self._edited_protocol_stack):
                item = self._edited_protocol_stack[idx]
                if item and isinstance(item[0], str):
                    return item[0]
            return None

        upper_protocol = get_safe_proto_name(index + 1)
        lower_protocol = get_safe_proto_name(index - 1)

        if incoming_protocol_name is None:

            current_proto = self._edited_protocol_stack[index][0]
            options = self._builder.get_commutable_protocols(
                upper_protocol,
                lower_protocol
            )

            self._edited_protocol_stack[index] = (current_proto, options)

        else:
            old_options = self._edited_protocol_stack[index][1]
            self._edited_protocol_stack[index] = (incoming_protocol_name, old_options)

            possible_upper = self._builder.get_possible_upper_protocols(incoming_protocol_name)
            possible_lower = self._builder.get_possible_lower_protocols(incoming_protocol_name)

            # print('index is', index,'upper_neighbor is', upper_protocol, 'lower_neighbor is', lower_protocol, 'possible_upper', possible_upper, 'possible_lower', possible_lower)

            if upper_protocol and possible_upper:
                self._edited_protocol_stack[index + 1] = (upper_protocol, possible_upper)

            if lower_protocol and possible_lower:
                self._edited_protocol_stack[index - 1] = (lower_protocol, possible_lower)

            if not possible_upper and index + 1 == len(self._edited_protocol_stack) - 1:
                del self._edited_protocol_stack[index + 1]

            if not possible_lower and index - 1 == 0:
                del self._edited_protocol_stack[index - 1]

            if not upper_protocol and possible_upper:
                try:
                    self._edited_protocol_stack[index + 1] = (None, None)
                except IndexError:
                    self._edited_protocol_stack.append((None, None))

            if not lower_protocol and possible_lower:
                if index - 1 >= 0:
                    self._edited_protocol_stack[index - 1] = (None, None)
                else:
                    self._edited_protocol_stack.insert(0, (None, None))