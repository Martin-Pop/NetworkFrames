from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
import logging

log = logging.getLogger(__name__)


class HexDumpWindow(QWidget):
    def __init__(self, frame, parent=None):
        super().__init__(parent)
        self.frame = frame

        self.setWindowTitle(f"Hexdump - Frame {frame.id}")
        self.setObjectName("hexdump_window")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setObjectName("hexdump_text_edit")

        self.text_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        layout.addWidget(self.text_edit)

        self._update_content()

        if hasattr(self.frame, 'infoUpdated'):
            self.frame.infoUpdated.connect(self._update_content)

    def _update_content(self):
        if hasattr(self.frame, 'scapy') and self.frame.scapy:
            try:
                raw_data = bytes(self.frame.scapy)
                html_content = self._generate_html_dump(raw_data)
                self.text_edit.setHtml(html_content)

                self._adjust_window_size()

            except Exception as e:
                self.text_edit.setPlainText(f"Error: {e}")
        else:
            self.text_edit.setPlainText("No data")

    def _adjust_window_size(self):
        doc = self.text_edit.document()
        content_width = doc.idealWidth()
        new_width = int(content_width + 60)
        current_height = self.height() if self.height() > 100 else 600

        self.resize(new_width, current_height)


    def _generate_html_dump(self, data):
        border_color = "#555"

        style = f"""
                <style>
                    body {{
                        font-family: 'Consolas', 'Courier New', monospace;
                        font-size: 12pt;
                    }}
                    table {{
                        border-collapse: collapse;
                    }}
                    th {{
                        text-align: left;
                        border-bottom: 1px solid #444;
                        padding-bottom: 5px;
                    }}
                    td {{
                        padding: 2px 10px;
                        vertical-align: top;
                    }}
                    .offset {{
                        border-right: 2px solid {border_color};
                        width: 80px;
                        text-align: right;
                    }}
                    .hex {{
                        border-right: 2px solid {border_color};
                        font-weight: bold;
                        padding-left: 15px;
                    }}
                    .ascii {{
                        padding-left: 15px;
                    }}
                </style>
                """

        html = f"{style}<body><div align='center'><table>"
        html += "<tr><th>Offset</th><th>Hex dump</th><th>ASCII</th></tr>"

        chunk_size = 16
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]

            offset_str = f"{i:04X}"

            hex_bytes = [f"{b:02X}" for b in chunk]
            while len(hex_bytes) < chunk_size:
                hex_bytes.append("  ")

            hex_str = " ".join(hex_bytes[:8]) + "  " + " ".join(hex_bytes[8:])

            ascii_chars = []
            for b in chunk:
                char = chr(b)
                if char == '<':
                    char = '&lt;'
                elif char == '>':
                    char = '&gt;'
                elif char == '&':
                    char = '&amp;'

                if 32 <= b < 127:
                    ascii_chars.append(char)
                else:
                    ascii_chars.append(".")
            ascii_str = "".join(ascii_chars)

            html += f"""
            <tr>
                <td class="offset">{offset_str}</td>
                <td class="hex">{hex_str}</td>
                <td class="ascii">{ascii_str}</td>
            </tr>
            """

        html += "</table></div></body>"
        return html

    def closeEvent(self, event):
        if hasattr(self.frame, 'infoUpdated'):
            try:
                self.frame.infoUpdated.disconnect(self._update_content)
            except:
                pass
        super().closeEvent(event)