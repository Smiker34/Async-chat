import socket
import time
import sys
import json

sys.path.append('../log')


from server_log_config import logger
from log_decorator import *


@logging
def message_response(message):
    message = json.loads(message.decode('utf-8'))
    logger.info(f'{message}')
    if (message['action']) and (message['time']):
        response = {
            "response": "200",
            "time": f"{time.time()}",
            "message": "OK"
        }
        logger.info(f"{response}")
        return json.dumps(response).encode('utf-8')
    else:
        response = {
            "response": "400",
            "time": f"{time.ctime()}",
            "message": "Incorrect data"
        }
        logger.info(f"{response}")
        return json.dumps(response).encode('utf-8')


def server_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
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
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((addr, port))
        server.listen(1)
        while True:
            client, addr = server.accept()
            message = client.recv(9999)
            logger.info('message received')
            response = message_response(message)
            client.send(response)
            logger.info('response_sent')
            break


if __name__ == '__main__':
    server_main()
