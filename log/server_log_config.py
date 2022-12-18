import logging
import sys
import logging.handlers

logger = logging.getLogger('server')

logger.setLevel(logging.INFO)

file_handler = logging.handlers.TimedRotatingFileHandler("../log/server logs.log", encoding='utf8', interval=1, when='D')

log_format = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

file_handler.setFormatter(log_format)
logger.addHandler(file_handler)


if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладочная информация')
    logger.info('Информационное сообщение')
