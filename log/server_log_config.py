import logging
import sys
from datetime import datetime

log = logging.getLogger('server')

log.setLevel(logging.INFO)
file_handler = logging.FileHandler("../log/{:%Y-%m-%d} server logs.txt".format(datetime.now()))
log_format = logging.Formatter("%(levelname)-10s %(asctime)s %(message)s")
file_handler.setFormatter(log_format)
log.addHandler(file_handler)


def message_receive_log():
    log.info('message received')


def message_log(message):
    log.info(f'{message}')


def response_log(response):
    log.info(f"{response}")


def response_sent_log():
    log.info('response_sent')


def host_port_log():
    try:
        addr = sys.argv[1]
    except IndexError:
        addr = 'localhost'
    try:
        port = int(sys.argv[2])
    except IndexError:
        port = 7777
    except ValueError:
        log.critical("Incorrect port")
        exit()
    log.info(f'host: {addr}, port: {port}')
    return (addr, port)
