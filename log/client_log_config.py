import logging
import sys

log = logging.getLogger('client')

log.setLevel(logging.INFO)
file_handler = logging.FileHandler("../log/client logs.log")
log_format = logging.Formatter("%(levelname)-10s %(asctime)s %(message)s")
file_handler.setFormatter(log_format)
log.addHandler(file_handler)


def message_created_logging(account_name):
    if not isinstance(account_name, str):
        log.critical('Incorrect name type')
        exit()
    elif len(account_name) > 25:
        log.critical("Name too long")
        exit()
    else:
        log.info("Message created")


def message_sent_log():
    log.info('message_sent')


def response_receive_log():
    log.info('response received')


def response_read_log():
    log.info("Response read")


def response_log(response):
    log.info('{} {}'.format(*response))


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
