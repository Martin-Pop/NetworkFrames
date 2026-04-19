import struct, socket
from PySide6.QtWidgets import QLineEdit
from scapy.fields import MACField, IPField
from .base_row import BaseFieldRow
import logging

log = logging.getLogger(__name__)


class StringRow(BaseFieldRow):
    def setup_editor(self):
        self.editor_widget = QLineEdit()

        txt = ""
        if self.current_val is not None:
            try:
                human_val = self.field_desc.i2h(None, self.current_val)

                if isinstance(human_val, bytes):
                    txt = human_val.hex().upper()
                else:
                    txt = str(human_val)
            except Exception as e:
                log.debug(f"i2h failed for {self.field_desc.name}: {e}")
                txt = str(self.current_val)

        try:
            hint = self.field_desc.i2repr(None, self.current_val)
            self.editor_widget.setPlaceholderText(hint)
        except Exception:
            pass

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
                    self._update_displays_from_int(int(clean_mac, 16) if clean_mac else 0)
                    return

            if isinstance(f, IPField):
                packed = socket.inet_aton(text)
                val_int = struct.unpack("!I", packed)[0]
                self._update_displays_from_int(val_int)
                return

            b = text.encode('utf-8', errors='ignore') if isinstance(text, str) else bytes(text)

            if isinstance(self.current_val, bytes):
                try:
                    clean_hex = text.replace(":", "").replace(" ", "").replace("-", "")
                    b = bytes.fromhex(clean_hex)
                except ValueError:
                    pass

            h = b.hex().upper()
            self.hex_display.setText(" ".join([h[i:i + 2] for i in range(0, len(h), 2)]))

            if len(b) <= 8 and len(b) > 0:
                int_val = int.from_bytes(b, byteorder='big')
                total_bits = len(b) * 8
                raw_bin = f"{int_val:0{total_bits}b}"
                bin_chunks = [raw_bin[i:i + 8] for i in range(0, len(raw_bin), 8)]
                self.bin_display.setText(" ".join(bin_chunks))
            elif len(b) == 0:
                self.bin_display.setText("")
            else:
                self.bin_display.setText("(Too long)")

        except Exception:
            self.hex_display.setText("-")
            self.bin_display.setText("-")

    def get_value(self):
        text = self.editor_widget.text().strip()

        if isinstance(self.current_val, bytes):
            try:
                clean_hex = text.replace(":", "").replace(" ", "").replace("-", "")
                return bytes.fromhex(clean_hex)
            except ValueError:
                pass

        try:
            return self.field_desc.any2i(None, text)
        except Exception as e:
            log.debug(f"any2i failed for {self.field_desc.name}: {e}")
            return text