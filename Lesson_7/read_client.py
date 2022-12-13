import socket
import sys
import time
import json

sys.path.append('../log')


from client_log_config import *


def read_response(response):
    response_read_log()
    response = json.loads(response.decode('utf-8'))

    return [response['user'], response['message']]


def client_main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect(host_port_log())
        while True:
            response = client.recv(9999)
            response_receive_log()
            response = read_response(response)
            response_log(response)


if __name__ == '__main__':
    client_main()
