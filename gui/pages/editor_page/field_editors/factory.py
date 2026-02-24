from scapy.fields import *
from .number_row import NumberRow
from .enum_row import EnumRow
from .flags_row import FlagsRow
from .packet_list_row import PacketListRow
from .string_row import StringRow
from .readonly_row import ReadOnlyRow

class FieldRowFactory:
    @staticmethod
    def create_row(field_name_text, cls_name, field_desc, current_val):
        val = current_val.val if isinstance(current_val, RawVal) else current_val
        f = field_desc.fld if isinstance(field_desc, Emph) else field_desc

        if isinstance(f, PacketListField):
            return PacketListRow(field_name_text, cls_name, field_desc, val)

        if isinstance(val, list):
            return ReadOnlyRow(field_name_text, cls_name, field_desc, val)

        if isinstance(val, list):
            return ReadOnlyRow(field_name_text, cls_name, field_desc, val)

        if isinstance(f, (EnumField, MultiEnumField)):
            return EnumRow(field_name_text, cls_name, field_desc, val)

        if isinstance(f, FlagsField):
            return FlagsRow(field_name_text, cls_name, field_desc, val)

        if isinstance(f, (IntField, ShortField, ByteField, LongField, BitField)):
            return NumberRow(field_name_text, cls_name, field_desc, val)

        if isinstance(f, (IPField, MACField, StrField, IP6Field, SourceIP6Field, DestIP6Field)):
            return StringRow(field_name_text, cls_name, field_desc, val)

        return StringRow(field_name_text, cls_name, field_desc, val)