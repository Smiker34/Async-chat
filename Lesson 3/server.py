import socket
import time
import sys
import json


def message_response(message):
    message = json.loads(message.decode('utf-8'))
    if (message['action']) and (message['time']):
        response = {
            "response": "200",
            "time": f"{time.time()}",
            "message": "OK"
        }
        return json.dumps(response).encode('utf-8')
    else:
        response = {
            "response": "400",
            "time": f"{time.ctime()}",
            "message": "Incorrect data"
        }
        return json.dumps(response).encode('utf-8')


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
        sys.exit('Порт не числовое значение')

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((addr, port))
    server.listen(1)
    while True:
        client, addr = server.accept()
        message = client.recv(9999)
        print(message)
        response = message_response(message)
        client.send(response)
