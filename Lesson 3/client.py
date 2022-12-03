import socket
import sys
import time
import json


def create_message(account_name="DEFAULT"):
    if not isinstance(account_name, str):
        exit('Имя не строка')
    if len(account_name) > 25:
        exit(f'Слишком длинное имя {account_name}')

    message = {
        "action": "presence",
        "time": f"{time.time()}",
        "user": {
            "account_name": f"{account_name}"
        }
    }
    return json.dumps(message).encode('utf-8')


def read_response(response):
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
            sys.exit('Порт не числовое значение')
        client.connect((addr, port))
        message = create_message()
        client.send(message)
        response = client.recv(9999)
        response = read_response(response)
        print('{}\n{}'.format(*response))


if __name__ == '__main__':
    client_main()
