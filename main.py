# from protocols.protocol_builder import PacketBuilder
# from utils.json_loader import load_json_from_file
# builder = PacketBuilder(load_json_from_file('protocol_map.json'))
# print(builder.get_possible_lower_protocols('Ether'))
#
# builder.wrappers["Ether"].set_field_value("src", "00:00:DE:AD:BE:EF")
# builder.wrappers["Ether"].set_field_value("type", 2054)
#
# builder.wrappers["IP"].set_field_value("src", "192.168.1.100")
# builder.wrappers["IP"].set_field_value("dst", "172.217.168.35")
#
#
# final_packet = builder.build_packet(["Ether", 'IP'])
#
# final_packet.show()

import sys
from PySide6.QtWidgets import QApplication

from controllers.editor_controller import EditorController
from controllers.frame_page_controller import FramePageController
from gui.main_window import MainWindow
import os

def main():
    app = QApplication(sys.argv)
    style_file_path = os.path.join(os.path.dirname(__file__), "gui/styles.qss")

    try:
        with open(style_file_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Err '{style_file_path}'.")

    window = MainWindow()

    #editor_controller = EditorController(window.editor_page)
    frame_page_controller = FramePageController(window.frame_page)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()



