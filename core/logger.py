# logger.py
import logging
import sys

LOG_FORMAT = (
    "[%(asctime)s] "
    "%(levelname)-8s "
    "%(name)s.%(funcName)s:%(lineno)d | "
    "%(message)s"
)

def setup_logger(level=logging.DEBUG):
    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        return  # no dupes from calling again

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        LOG_FORMAT,
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)

    root.addHandler(handler)
