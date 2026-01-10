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

import os, logging, sys
from PySide6.QtWidgets import QApplication
from controllers.main_controller import MainController
from gui.main_window import MainWindow
from core.logger import setup_logger

def main():

    setup_logger(logging.DEBUG)
    log = logging.getLogger(__name__)

    app = QApplication(sys.argv)
    log.debug("Application started")
    style_file_path = os.path.join(os.path.dirname(__file__), "gui/styles.qss")

    try:
        with open(style_file_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        log.error(f"Err '{style_file_path}'.")

    window = MainWindow()

    main_controller = MainController(window)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()



