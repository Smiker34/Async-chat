import sys
sys.path.append('../log')


from server_log_config import logger


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(
                f'Неподходящий порт {value}.')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
