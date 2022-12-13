import socket
import time
import sys
import json
import select

sys.path.append('../log')


from server_log_config import *
from log_decorator import *


@logging
def read_requests(r_clients, all_clients):
    responses = {}
    for sock in r_clients:
        try:
            data = json.loads(sock.recv(1024).decode('utf-8'))
            message_receive_log()
            responses[sock] = data
            message_log(data)
        except:
            print('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
            all_clients.remove(sock)
        return responses


@logging
def write_responses(requests, w_clients, all_clients):
    for sock in w_clients:
        if sock in requests:
            try:
                resp = json.dumps(requests[sock]).encode('utf-8')
                for client in all_clients:
                    client.send(resp)
            except:
                print('Клиент {} {} отключился'.format(sock.fileno(), sock.getpeername()))
                sock.close()
                all_clients.remove(sock)


def server_main():
    clients = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(host_port_log())
        server.listen(5)
        server.settimeout(0.2)
        while True:
            try:
                client, addr = server.accept()
            except OSError as e:
                pass
            else:
                clients.append(client)
            finally:
                wait = 10
                r = []
                w = []
                try:
                    r, w, e = select.select(clients, clients, [], wait)
                except:
                    pass
                requests = read_requests(r, clients)
                if requests:
                    write_responses(requests, w, clients)


if __name__ == '__main__':
    server_main()
