import logging
from datetime import datetime

def get_logger(name="RPS_Server"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    filename = f"logs_{datetime.now().strftime('%Y_%m_%d')}.log"
    file_handler = logging.FileHandler(filename, encoding="utf-8")
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)

    return logger
