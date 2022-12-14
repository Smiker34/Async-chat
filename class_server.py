import socket
import sys
import argparse
import json
import logging
import select
import time

sys.path.append('./log')


from server_log_config import logger
from log_decorator import *
from descript import Port
from meta_classes import ServerMaker
from server_db import Storage


@logging
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='localhost', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.clients = []
        self.messages = []
        self.names = []

    def init_socket(self):
        logger.info(f'Запущен сервер, порт для подключений: {self.port} ,'
                    f' адрес с которого принимаются подключения: {self.addr}.')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(client_with_message.recv(9999), client_with_message)
                    except:
                        logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients.remove(client_with_message)

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except:
                    logger.info(f'Связь с клиентом с именем {message[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[message[DESTINATION]])
                    del self.names[message[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            self.names[message[DESTINATION]].send(json.dump(message).encode("utf-8"))
            logger.info(f'Отправлено сообщение пользователю {message[DESTINATION]} от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    def process_client_message(self, message, client):
        logger.info(f'Разбор сообщения от клиента : {message}')
        message = json.loads(message.decode("utf-8"))
        if "ACTION" in message and message["ACTION"] == "PRESENCE" and "TIME" in message and "USER" in message:
            if message["USER"]["ACCOUNT_NAME"] not in self.names:
                self.names.append(message["USER"]["ACCOUNT_NAME"])
                client_ip, client_port = client.getpeername()
                self.database.user_login(message["USER"]["ACCOUNT_NAME"], client_ip, client_port)
                client.send(json.dumps({"RESPONSE": "200"}).encode("utf-8"))
            else:
                response = {"RESPONSE": "400"}
                response["ERROR"] = 'Имя пользователя уже занято.'
                client.send(json.dumps(response).encode("utf-8"))
                self.clients.remove(client)
                client.close()
            return
        elif "ACTION" in message and message["ACTION"] == "MESSAGE" and "DESTINATION" in message and "TIME" in message \
                and "SENDER" in message and "MESSAGE_TEXT" in message:
            self.messages.append(message)
            return
        elif "ACTION" in message and message["ACTION"] == "EXIT" and "ACCOUNT_NAME" in message:
            self.database.user_logout(message["ACCOUNT_NAME"])
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names["ACCOUNT_NAME"].close()
            del self.names["ACCOUNT_NAME"]
            return
        else:
            response = {"RESPONSE": "400"}
            response["ERROR"] = 'Запрос некорректен.'
            client.send(json.dumps(response).encode("utf-8"))
            return


def main():
    listen_address, listen_port = arg_parser()
    database = Storage()
    server = Server(listen_address, listen_port, database)
    server.main_loop()


if __name__ == '__main__':
    main()
