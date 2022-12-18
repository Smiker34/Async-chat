import socket
import sys
import time
import json

sys.path.append('../log')


from client_log_config import logger
from log_decorator import *


@logging
def create_message(msg, account_name="DEFAULT"):
    if not isinstance(account_name, str):
        logger.critical('Incorrect name type')
        exit()
    elif len(account_name) > 25:
        logger.critical("Name too long")
        exit()
    else:
        logger.info("Message created")

    message = {
        "action": "msg",
        "time": f"{time.time()}",
        "user": f"{account_name}",
        "message": f"{msg}"
    }
    return json.dumps(message).encode('utf-8')


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
            msg_text = input('Input message: ')
            if msg_text == 'exit':
                break
            else:
                message = create_message(msg_text, 'write_client')
                client.send(message)
                logger.info('message_sent')


if __name__ == '__main__':
    client_main()
