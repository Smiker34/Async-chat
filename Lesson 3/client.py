import socket
import sys
import time
import json

sys.path.append('../log')


from client_log_config import logger
from log_decorator import *


@logging
def create_message(account_name="DEFAULT"):
    if not isinstance(account_name, str):
        logger.critical('Incorrect name type')
        exit()
    elif len(account_name) > 25:
        logger.critical("Name too long")
        exit()
    else:
        logger.info("Message created")

    message = {
        "action": "presence",
        "time": f"{time.time()}",
        "user": {
            "account_name": f"{account_name}"
        }
    }
    return json.dumps(message).encode('utf-8')


@logging
def read_response(response):
    logger.info("Response read")
    response = json.loads(response.decode('utf-8'))

    return [response['response'], response['message']]


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
        message = create_message()
        client.send(message)
        logger.info('message_sent')
        response = client.recv(9999)
        logger.info('response received')
        response = read_response(response)
        logger.info('{} {}'.format(*response))


if __name__ == '__main__':
    client_main()
