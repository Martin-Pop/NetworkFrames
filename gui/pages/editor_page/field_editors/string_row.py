import struct, socket
from PySide6.QtWidgets import QLineEdit
from scapy.fields import MACField, IPField, IP6Field, SourceIP6Field, DestIP6Field
from .base_row import BaseFieldRow


class StringRow(BaseFieldRow):
    def setup_editor(self):
        self.editor_widget = QLineEdit()
        txt = ""
        if self.current_val is not None:
            if isinstance(self.current_val, bytes):
                try:
                    txt = self.current_val.decode('utf-8')
                except UnicodeDecodeError:
                    txt = self.current_val.decode('utf-8', errors='replace')
            else:
                txt = str(self.current_val)

        self.editor_widget.setText(txt)
        self.editor_widget.textChanged.connect(self._on_text_changed)

        self.mid_layout.insertWidget(0, self.editor_widget)
        self._on_text_changed(txt)

    def _on_text_changed(self, text):
        f = self.field_desc
        try:
            if isinstance(f, MACField):
                clean_mac = text.replace(":", "").replace("-", "").replace(".", "")
                if len(clean_mac) <= 12:
                    self._update_displays_from_int(int(clean_mac, 16))
                    return

            if isinstance(f, IPField):
                packed = socket.inet_aton(text)
                val_int = struct.unpack("!I", packed)[0]
                self._update_displays_from_int(val_int)
                return

            if isinstance(f, (IP6Field, SourceIP6Field, DestIP6Field)):
                packed = socket.inet_pton(socket.AF_INET6, text)
                val_int = int.from_bytes(packed, byteorder='big')
                self._update_displays_from_int(val_int)
                return

            b = text.encode('utf-8', errors='ignore') if isinstance(text, str) else bytes(text)
            h = b.hex().upper()
            self.hex_display.setText(" ".join([h[i:i + 2] for i in range(0, len(h), 2)]))

            if len(b) <= 8:
                int_val = int.from_bytes(b, byteorder='big')
                total_bits = len(b) * 8
                raw_bin = f"{int_val:0{total_bits}b}"
                bin_chunks = [raw_bin[i:i + 8] for i in range(0, len(raw_bin), 8)]
                self.bin_display.setText(" ".join(bin_chunks))
            else:
                self.bin_display.setText("(Too long)")

        except Exception:
            self.hex_display.setText("-")
            self.bin_display.setText("-")

    def get_value(self):
        return self.editor_widget.text()