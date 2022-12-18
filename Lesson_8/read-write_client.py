import socket
import sys
import time
import json
import threading

sys.path.append('../log')


from client_log_config import logger
from log_decorator import *


@logging
def create_message(socket, account_name="DEFAULT"):
    if not isinstance(account_name, str):
        logger.critical('Incorrect name type')
        exit()
    elif len(account_name) > 25:
        logger.critical("Name too long")
        exit()
    else:
        logger.info("Message created")

    while True:
        msg_text = input('Input message: ')
        if msg_text == 'exit':
            break
        else:

            message = {
                "action": "msg",
                "time": f"{time.time()}",
                "user": f"{account_name}",
                "message": f"{msg_text}"
            }
            socket.send(json.dumps(message).encode('utf-8'))
            logger.info('message_sent')


@logging
def read_response(socket):
    while True:
        response = socket.recv(9999)
        if response:
            logger.info('response received')
            logger.info("Response read")
            response = json.loads(response.decode('utf-8'))
            logger.info('{} {}'.format(*[response['user'], response['message']]))


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

        receiver = threading.Thread(target=read_response, args=(client, ))
        receiver.daemon = True
        receiver.start()

        # create_message(client, 'write_user')

        user_input = threading.Thread(target=create_message, args=(client, 'write_user', ))
        user_input.daemon = True
        user_input.start()

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_input.is_alive():
                continue
            break


if __name__ == '__main__':
    client_main()
