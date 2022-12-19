import socket
import sys
import time
import json

sys.path.append('../log')


from client_log_config import logger
from log_decorator import *


@logging
def read_response(response):
    logger.info("Response read")
    response = json.loads(response.decode('utf-8'))

    return [response['user'], response['message']]


def client_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            addr = sys.argv[1]
        except IndexError:
            addr = 'localhost'
        try:
            port = int(sys.argv[2])
        except IndexError:
            port = 7777
        except ValueError:
            logger.critical("Incorrect port")
            exit()
        logger.info(f'host: {addr}, port: {port}')
        client.connect((addr, port))
        while True:
            response = client.recv(9999)
            logger.info('response received')
            response = read_response(response)
            logger.info('{} {}'.format(*response))


if __name__ == '__main__':
    client_main()
