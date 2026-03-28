import logging, sys, os

if sys.stdin is None:
    sys.stdin = open(os.devnull, "r")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from PySide6.QtWidgets import QApplication
from controllers.main_controller import MainController
from gui.main_window import MainWindow
from utils.logger import setup_logger, register_main_window_logger
from gui.styles.style_loader import apply_stylesheet

def main():

    setup_logger(logging.DEBUG)
    log = logging.getLogger(__name__)

    app = QApplication(sys.argv)
    log.debug("Application started")

    try:
        apply_stylesheet(app)
    except Exception as e:
        log.error(e)

    window = MainWindow()
    register_main_window_logger(window)

    main_controller = MainController(window)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()



