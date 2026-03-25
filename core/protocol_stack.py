from dataclasses import dataclass
import logging

log = logging.getLogger(__name__)

@dataclass
class ProtocolNode:
    current: str | None
    options: list[str] | None

class ProtocolStack:

    def __init__(self, builder):
        self._builder = builder

        self._protocol_stack = []
        self._edited_protocol_stack = []
        self._backup_edited_protocol_stack = []

    @property
    def protocol_stack(self):
        return self._protocol_stack

    @property
    def edited_protocol_stack(self):
        return self._edited_protocol_stack

    def clear(self):
        self._protocol_stack = []
        self._edited_protocol_stack = []
        self._backup_edited_protocol_stack = []

    def load(self, layers):
        self._edited_protocol_stack = [ProtocolNode(layer, [layer]) for layer in layers]
        self.save()

    def save(self):
        self._backup_edited_protocol_stack = self._edited_protocol_stack.copy()
        self._protocol_stack = [node.current for node in self._edited_protocol_stack if node.current is not None]

    def revert(self):
        self._edited_protocol_stack = self._backup_edited_protocol_stack.copy()

    def get_options_for_insert(self, index):
        upper_protocol = self._edited_protocol_stack[index].current if index < len(self._edited_protocol_stack) else None
        lower_protocol = self._edited_protocol_stack[index - 1].current if index > 0 else None
        return self._builder.get_commutable_protocols(upper_protocol, lower_protocol)

    def add_empty_node(self, index):
        options = self.get_options_for_insert(index)
        self._edited_protocol_stack.insert(index, ProtocolNode(None, options))

    def update_node(self, index, protocol_name):
        if 0 <= index < len(self._edited_protocol_stack):
            self._edited_protocol_stack[index].current = protocol_name if protocol_name else None

    def remove_node(self, index):
        if 0 <= index < len(self._edited_protocol_stack):
            self._edited_protocol_stack.pop(index)