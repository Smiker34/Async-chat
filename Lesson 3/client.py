import socket
import sys
import time
import json

sys.path.append('../log')


from client_log_config import *
from log_decorator import *


@logging
def create_message(account_name="DEFAULT"):
    message_created_logging(account_name)

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
    response_read_log()
    response = json.loads(response.decode('utf-8'))

    return [response['response'], response['message']]


def client_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(host_port_log())
        message = create_message()
        client.send(message)
        message_sent_log()
        response = client.recv(9999)
        response_receive_log()
        response = read_response(response)
        response_log(response)


if __name__ == '__main__':
    client_main()
