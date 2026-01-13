import logging
import sys
import traceback
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import QObject, Signal

LOG_FORMAT = (
    "[%(asctime)s] "
    "%(levelname)-8s "
    "%(name)s.%(funcName)s:%(lineno)d | "
    "%(message)s"
)

class QtLogErrorHandler(logging.Handler, QObject):
    """
    Custom logging handler that emits a signal when an error occurs.
    Signal is connected to a function that displays the error in a message box.
    """

    show_error_signal = Signal(str, str, str) # uses signal so its thread safe

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.show_error_signal.connect(self._show_message_box)

    def emit(self, record):
        """
        Handles log records, only if its error+
        :param record: log record
        :return:
        """
        if record.levelno >= logging.ERROR:
            msg_title = "Error"
            msg_body = record.getMessage()

            msg_detail = ""
            if record.exc_info:
                msg_detail = "".join(traceback.format_exception(*record.exc_info))

            self.show_error_signal.emit(msg_title, msg_body, msg_detail)

    def _show_message_box(self, title, body, detail):
        """
        Shows message box with error. Must run in main thread
        :param title: message title
        :param body: message body
        :param detail: message details
        """

        active_window = QApplication.activeWindow()

        msg_box = QMessageBox(active_window)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(f"<b>{body}</b>")

        if detail:
            msg_box.setInformativeText("An unexpected error occurred. See details for more info.")
            msg_box.setDetailedText(detail)

        msg_box.exec()

def _global_exception_hook(exc_type, exc_value, exc_traceback):
    """
    Sets up global exception hook to handle all exceptions except KeyboardInterrupt
    :param exc_type: exception type
    :param exc_value: exception value
    :param exc_traceback: exception traceback
    :return: early if its KeyboardInterrupt
    """

    #ignore keyboard interrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical(
        "Uncaught Exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def setup_logger(level=logging.DEBUG, log_file="app.log"):
    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        return # no dupes from calling again

    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.WARNING)

    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    qt_handler = QtLogErrorHandler()
    qt_handler.setLevel(logging.ERROR)
    qt_handler.setFormatter(logging.Formatter('%(message)s'))

    root.addHandler(qt_handler)

    sys.excepthook = _global_exception_hook

    logging.info(f"Logger initialized. Warnings+ will be saved to {log_file}")
