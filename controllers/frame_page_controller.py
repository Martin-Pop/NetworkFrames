from utils.pcap import read_pcap


class FramePageController:
    def __init__(self, frame_page, frame_manager):
        self._frame_page = frame_page
        self._frame_manager = frame_manager
        self._frame_page.frame_list_panel.addNewFrame.connect(self._on_new_frame_added)
        self._frame_page.frame_list_panel.frameSelected.connect(self._on_frame_selected)

    def _on_new_frame_added(self, file_path):
        if file_path:
            for packet in read_pcap(file_path):
                new_frame = self._frame_manager.add(packet)
                self._frame_page.frame_list_panel.add_frame(new_frame.info)
        else:
            new_frame = self._frame_manager.add(None)
            self._frame_page.frame_list_panel.add_frame(new_frame.info)

    def _on_frame_selected(self, id):
        print('frame selected: ' + str(id))



