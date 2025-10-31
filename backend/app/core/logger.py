import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from backend.app.core.config import settings


def setup_logger(name: str, log_file: str, level=None):
    log_config = settings.logging_config

    level = level or log_config["log_level"]

    log_file = log_file.format(date=datetime.now().strftime("%Y-%m-%d"))
    full_log_path = os.path.join(log_config["logs_dir"], log_file)

    os.makedirs(os.path.dirname(full_log_path), exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        full_log_path,
        maxBytes=log_config["max_log_size_bytes"],
        backupCount=log_config["backup_count"],
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger


error_logger = setup_logger(
    "error_logger", settings.logging_config["error_log_filename"]
)
request_logger = setup_logger(
    "request_logger", settings.logging_config["request_log_filename"]
)
