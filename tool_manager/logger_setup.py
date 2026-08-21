"""
logger_setup.py
----------------
Central logging configuration.

Every action the tool manager takes (install attempt, dependency
check, version check, failure) gets logged to logs/tool_manager.log
AND printed to the console. This satisfies the "maintain a log of
installations, updates, and errors" line from the task spec, and
makes debugging a failed run on someone else's machine much easier
than asking them to reproduce it.
"""

import logging
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "tool_manager.log"

_configured = False


def setup_logger(name: str = "tool_manager", level: int = logging.INFO) -> logging.Logger:
    """
    Configure (once) and return the shared logger.

    Safe to call multiple times across modules — logging handlers
    are only attached the first time, so re-importing this in
    several files doesn't duplicate log lines.
    """
    global _configured
    logger = logging.getLogger(name)

    if _configured:
        return logger

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    _configured = True
    return logger
