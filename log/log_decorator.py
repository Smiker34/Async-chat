from server_log_config import log
from functools import wraps
import inspect


def logging(func):
    @wraps(func)
    def create_log(*args, **kwargs):
        result = func(*args, **kwargs)
        log.info(f'Function {func.__name__} was called from {inspect.stack()[1][3]}')
        log.info(f'Function {func.__name__}({args}, {kwargs}), return {result}')
        return result
    return create_log
