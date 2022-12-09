import logging
from functools import wraps
import inspect


def log(func):
    @wraps(func)
    def create_log(*args, **kwargs):
        result = func(*args, **kwargs)

        logs = logging.getLogger('def')
        logs.setLevel(logging.INFO)
        file_handler = logging.FileHandler("../log/def logs.log")
        log_format = logging.Formatter("%(asctime)s %(message)s")
        file_handler.setFormatter(log_format)
        logs.addHandler(file_handler)

        logs.info(f'Function {func.__name__} was called from {inspect.stack()[1][3]}')
        logs.info(f'Function {func.__name__}({args}, {kwargs}), return {result}')
        return result
    return create_log
