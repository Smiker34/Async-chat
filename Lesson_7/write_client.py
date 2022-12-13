import socket
import sys
import time
import json

sys.path.append('../log')


from client_log_config import *
from log_decorator import *


@logging
def create_message(msg, account_name="DEFAULT"):
    message_created_logging(account_name)

    message = {
        "action": "msg",
        "time": f"{time.time()}",
        "user": f"{account_name}",
        "message": f"{msg}"
    }
    return json.dumps(message).encode('utf-8')


def client_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(host_port_log())
        while True:
            msg_text = input('Input message: ')
            if msg_text == 'exit':
                break
            else:
                message = create_message(msg_text, 'write_client')
                client.send(message)
                message_sent_log()


if __name__ == '__main__':
    client_main()
