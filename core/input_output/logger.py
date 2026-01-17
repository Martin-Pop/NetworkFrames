import logging
import sys
import traceback
from PySide6.QtWidgets import QMessageBox, QApplication, QStyle
from PySide6.QtCore import QObject, Signal, QTimer


LOG_FORMAT = (
    "[%(asctime)s] "
    "%(levelname)-8s "
    "%(name)s.%(funcName)s:%(lineno)d | "
    "%(message)s"
)

AUTO_CLOSE_TIMER = 2500 #ms
_qt_log_handler_instance = None

class QtLogHandler(logging.Handler, QObject):
    """
    Custom logging handler that emits a signal when an event occurs.
    Signal is connected to a function that displays the info in a message box.
    """

    show_error_signal = Signal(str, str, str)  # uses signal so its thread safe
    show_notification_signal = Signal(int, str, str)  # level, title, body

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.show_error_signal.connect(self._show_error_box)
        self.show_notification_signal.connect(self._show_notification_box)

        self._main_window_ref = None

    def set_main_window(self, window):
        """
        Registers the main window instance to ensure popups always have a parent.
        :param window: window to register
        """
        self._main_window_ref = window

    def _get_parent(self):
        """
        Returns the best available parent widget.
        Priority: 1. Registered Main Window, 2. Active Window, 3. None
        """
        if self._main_window_ref:
            return self._main_window_ref
        return QApplication.activeWindow()

    def emit(self, record):
        """
        Handles log records.
        ERROR+ -> Detailed Error Box
        WARNING -> Warning Box (Manual close)
        INFO -> Info Box (Auto close)
        :param record: log record
        :return:
        """
        # error
        if record.levelno >= logging.ERROR:
            msg_title = "Error"
            msg_body = record.getMessage()

            msg_detail = ""
            if record.exc_info:
                msg_detail = "".join(traceback.format_exception(*record.exc_info))

            self.show_error_signal.emit(msg_title, msg_body, msg_detail)

        # info and warning
        elif record.levelno >= logging.INFO:
            msg_body = record.getMessage()
            msg_title = record.levelname.capitalize()

            self.show_notification_signal.emit(record.levelno, msg_title, msg_body)

    def _show_error_box(self, title, body, detail):
        """
        Shows message box with error. Must run in main thread
        :param title: message title
        :param body: message body
        :param detail: message details
        """

        parent = self._get_parent()
        if not parent:
            return

        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(f"<b>{body}</b>")

        if detail:
            msg_box.setInformativeText("An unexpected error occurred. See details for more info.")
            msg_box.setDetailedText(detail)

        msg_box.exec()

    def _show_notification_box(self, level, title, body):
        """
        Shows notification. auto close for INFO.
        :param level: log leve
        :param title: notification title
        :param body: notification body (text)
        :return:
        """
        parent = self._get_parent()
        if not parent:
           return

        style = QApplication.style()

        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(body)

        if level == logging.WARNING:
           icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
           msg_box.setIconPixmap(icon.pixmap(32, 32))
        else:
           icon = style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
           msg_box.setIconPixmap(icon.pixmap(32, 32))
           QTimer.singleShot(AUTO_CLOSE_TIMER, msg_box.accept)

        msg_box.exec()


def _global_exception_hook(exc_type, exc_value, exc_traceback):
    """
    Sets up global exception hook to handle all exceptions except KeyboardInterrupt
    :param exc_type: exception type
    :param exc_value: exception value
    :param exc_traceback: exception traceback
    :return: early if its KeyboardInterrupt
    """

    # ignore keyboard interrupt
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical(
        "Uncaught Exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


def setup_logger(level=logging.DEBUG, log_file="app.log"):
    global _qt_log_handler_instance

    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        return  # no dupes from calling again

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

    qt_handler = QtLogHandler()
    qt_handler.setLevel(logging.INFO)
    qt_handler.setFormatter(logging.Formatter('%(message)s'))

    root.addHandler(qt_handler)

    _qt_log_handler_instance = qt_handler
    sys.excepthook = _global_exception_hook

    logging.info(f"Logger initialized. Warnings+ will be saved to {log_file}")

def register_main_window_logger(window):
    if _qt_log_handler_instance:
        _qt_log_handler_instance.set_main_window(window)