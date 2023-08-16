# Copyright(C) 2023 Anders Logg
# Licensed under the MIT License

# Configure logging
import logging

format = "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
logging.basicConfig(format=format)
logger = logging.getLogger("dtcc_viewer")

# Expose logging functions
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical


def set_log_level(level):
    "Set log level"
    logger.setLevel(level)
