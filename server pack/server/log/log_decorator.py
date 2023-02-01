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


def login_required(func):

    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg["ACTION"] == "PRESENCE":
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
