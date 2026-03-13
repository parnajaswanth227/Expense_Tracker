"""
logger.py — central structured logging.
All modules call get_logger(__name__).
"""

import logging
import sys

_FORMAT   = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "expense_tracker") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE_FMT))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
