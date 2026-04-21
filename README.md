**Network Frames Editor**

A desktop application for interactive network packet experimenting - creation, modification, and endpoint delivery testing.

**Features**
* Visual editor.
* Fuzzer for packet parameter randomization.
* Network sender for sending custom frames.
* Remote receiver module (probe) to verify successful packet delivery.
* Support PCAP file import and export.
* Dynamic hexadecimal and binary data preview.

**Technologies Used**
* Scapy: Low-level packet manipulation.
* PySide6 (Qt): Graphical user interface.
* PyInstaller / Bash: Cross-platform distribution and execution.

**Getting Started**
* The application requires root/administrator privileges to interact with network interfaces.
* Linux: Execute the application using the provided run.sh script.
* Windows: Run the standalone executable file compiled via PyInstaller.
