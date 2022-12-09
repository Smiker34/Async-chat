import socket
import time
import sys
import json

sys.path.append('../log')


from server_log_config import *
from log_decorator import *

@logging
def message_response(message):
    message = json.loads(message.decode('utf-8'))
    message_log(message)
    if (message['action']) and (message['time']):
        response = {
            "response": "200",
            "time": f"{time.time()}",
            "message": "OK"
        }
        response_log(response)
        return json.dumps(response).encode('utf-8')
    else:
        response = {
            "response": "400",
            "time": f"{time.ctime()}",
            "message": "Incorrect data"
        }
        response_log(response)
        return json.dumps(response).encode('utf-8')


def server_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(host_port_log())
        server.listen(1)
        while True:
            client, addr = server.accept()
            message = client.recv(9999)
            message_receive_log()
            response = message_response(message)
            client.send(response)
            response_sent_log()
            break


if __name__ == '__main__':
    server_main()
