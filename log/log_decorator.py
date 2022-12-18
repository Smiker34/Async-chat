from server_log_config import logger
from client_log_config import logger
from functools import wraps
import sys
import inspect
import logging


if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def logging(func):
    @wraps(func)
    def create_log(*args, **kwargs):
        result = func(*args, **kwargs)
        logger.info(f'Function {func.__name__} was called from {inspect.stack()[1][3]}')
        logger.info(f'Function {func.__name__}({args}, {kwargs}), return {result}')
        return result
    return create_log
