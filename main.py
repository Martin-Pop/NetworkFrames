from protocols.protocol_builder import PacketBuilder
from utils.json_loader import load_json_from_file
builder = PacketBuilder(load_json_from_file('protocol_map.json'))
print(builder.get_possible_lower_protocols('Ether'))

builder.wrappers["Ether"].set_field_value("src", "00:00:DE:AD:BE:EF")
builder.wrappers["Ether"].set_field_value("type", 2054)

builder.wrappers["IP"].set_field_value("src", "192.168.1.100")
builder.wrappers["IP"].set_field_value("dst", "172.217.168.35")


final_packet = builder.build_packet(["Ether", 'IP'])

final_packet.show()




