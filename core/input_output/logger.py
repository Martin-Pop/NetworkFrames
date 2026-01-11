import logging
import sys

LOG_FORMAT = (
    "[%(asctime)s] "
    "%(levelname)-8s "
    "%(name)s.%(funcName)s:%(lineno)d | "
    "%(message)s"
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

    logging.info(f"Logger initialized. Warnings+ will be saved to {log_file}")
