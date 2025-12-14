

class FramePageController:
    def __init__(self, frame_page):
        self._frame_page = frame_page
        self._frame_page.frame_list_panel.addNewFrame.connect(self._on_new_frame_added)

    def _on_new_frame_added(self, file_path):
        if file_path:
            print('loading from pcap ' + file_path)
        else:
            print('creating new empty frame')



