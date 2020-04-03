import logging
from time import sleep

from experimentor.core.publisher import start_publisher
from experimentor.lib.log import get_logger, log_to_screen

if __name__ == '__main__':
    logger = get_logger(level=logging.DEBUG)
    handler = log_to_screen(logger, level=logging.INFO)

    start_publisher()
    logger.info('Going to sleep')
    sleep(5)
