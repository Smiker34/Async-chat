import threading
import select
import socket
import json
import hmac
import binascii
import os
import sys

sys.path.append('./')
sys.path.append('./log')


from server_log_config import logger
from descript import Port
from meta_classes import ServerMaker
from log_decorator import login_required


class MessageProcessor(threading.Thread):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database

        self.sock = None

        self.clients = []

        self.listen_sockets = None
        self.error_sockets = None

        self.running = True

        self.names = dict()

        super().__init__()

    def run(self):
        self.init_socket()

        while self.running:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err.errno}')
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(json.loads(client_with_message.recv(9999).decode('utf-8')), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.info(f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen(MAX_CONNECTIONS)

    def process_message(self, message):
        if message["DESTINATION"] in self.names and self.names[message["DESTINATION"]] in self.listen_sockets:
            try:
                self.names[message["DESTINATION"]].send(json.dumps(message).encode("utf-8"))
                logger.info(
                    f'Отправлено сообщение пользователю {message["DESTINATION"]} от пользователя {message["SENDER"]}.')
            except OSError:
                self.remove_client(message["DESTINATION"])
        elif message["DESTINATION"] in self.names and self.names[message["DESTINATION"]] not in self.listen_sockets:
            logger.error(
                f'Связь с клиентом {message["DESTINATION"]} была потеряна. Соединение закрыто, доставка невозможна.')
            self.remove_client(self.names[message["DESTINATION"]])
        else:
            logger.error(
                f'Пользователь {message["DESTINATION"]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    @login_required
    def process_client_message(self, message, client):
        logger.info(f'Разбор сообщения от клиента : {message}')
        if "ACTION" in message and message["ACTION"] == "PRESENCE" and "TIME" in message and "USER" in message:
            self.autorize_user(message, client)
        elif "ACTION" in message and message["ACTION"] == "MESSAGE" and "DESTINATION" in message and "TIME" in message \
                and "SENDER" in message and "MESSAGE_TEXT" in message and self.names[message["SENDER"]] == client:
            if message["DESTINATION"] in self.names:
                self.database.process_message(message["SENDER"], message["DESTINATION"])
                self.process_message(message)
                try:
                    client.send(json.dumps({"RESPONSE": 200}).encode('utf-8'))
                except OSError:
                    self.remove_client(client)
            else:
                response = {"RESPONSE": 400}
                response["ERROR"] = 'Пользователь не зарегистрирован на сервере.'
                try:
                    client.send(json.dumps(response).encode('utf-8'))
                except OSError:
                    pass
            return

        elif "ACTION" in message and message["ACTION"] == "EXIT" and "ACCOUNT_NAME" in message \
                and self.names[message["ACCOUNT_NAME"]] == client:
            self.remove_client(client)

        elif "ACTION" in message and message["ACTION"] == "GET_CONTACTS" and "USER" in message and \
                self.names[message["USER"]] == client:
            response = {"RESPONSE": 202}
            response["LIST_INFO"] = self.database.get_contacts(message["USER"])
            try:
                client.send(json.dumps(response).encode('utf-8'))
            except OSError:
                self.remove_client(client)

        elif "ACTION" in message and message["ACTION"] == "ADD_CONTACT" and "ACCOUNT_NAME" in message and "USER" in message \
                and self.names[message["USER"]] == client:
            self.database.add_contact(message["USER"], message["ACCOUNT_NAME"])
            try:
                client.send(json.dumps({"RESPONSE": 200}).encode('utf-8'))
            except OSError:
                self.remove_client(client)

        elif "ACTION" in message and message["ACTION"] == "REMOVE_CONTACT" and "ACCOUNT_NAME" in message and "USER" in message \
                and self.names[message["USER"]] == client:
            self.database.remove_contact(message["USER"], message["ACCOUNT_NAME"])
            try:
                client.send(json.dumps({"RESPONSE": 200}).encode('utf-8'))
            except OSError:
                self.remove_client(client)

        elif "ACTION" in message and message["ACTION"] == "USERS_REQUEST" and "ACCOUNT_NAME" in message \
                and self.names[message["ACCOUNT_NAME"]] == client:
            response = {"RESPONSE": 202}
            response["LIST_INFO"] = [user[0] for user in self.database.users_list()]
            try:
                client.send(json.dumps(response).encode('utf-8'))
            except OSError:
                self.remove_client(client)

        elif "ACTION" in message and message["ACTION"] == "PUBLIC_KEY_REQUEST" and "ACCOUNT_NAME" in message:
            response = {"RESPONSE": 511}
            response["DATA"] = self.database.get_pubkey(message["ACCOUNT_NAME"])
            if response["DATA"]:
                try:
                    client.send(json.dumps(response).encode('utf-8'))
                except OSError:
                    self.remove_client(client)
            else:
                response = {"RESPONSE": 400}
                response["ERROR"] = 'Нет публичного ключа для данного пользователя'
                try:
                    client.send(json.dumps(response).encode('utf-8'))
                except OSError:
                    self.remove_client(client)

        else:
            response = {"RESPONSE": 400}
            response["ERROR"] = 'Запрос некорректен.'
            try:
                client.send(json.dumps(response).encode('utf-8'))
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        logger.info(f'Start auth process for {message["USER"]}')
        if message["USER"]["ACCOUNT_NAME"] in self.names.keys():
            response = {"RESPONSE": 400}
            response["ERROR"] = 'Имя пользователя уже занято.'
            try:
                logger.info(f'Username busy, sending {response}')
                client.send(json.dumps(response).encode('utf-8'))
            except OSError:
                logger.info('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message["USER"]["ACCOUNT_NAME"]):
            response = {"RESPONSE": 400}
            response["ERROR"] = 'Пользователь не зарегистрирован.'
            try:
                logger.info(f'Unknown username, sending {response}')
                client.send(json.dumps(response).encode('utf-8'))
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            logger.info('Correct username, starting passwd check.')
            message_auth = {"RESPONSE": 511}
            random_str = binascii.hexlify(os.urandom(64))
            message_auth["DATA"] = random_str.decode('ascii')
            hash = hmac.new(self.database.get_hash(message["USER"]["ACCOUNT_NAME"]), random_str, 'MD5')
            digest = hash.digest()
            logger.info(f'Auth message = {message_auth}')
            try:
                sock.send(json.dumps(message_auth).encode('utf-8'))
                ans = json.loads(sock.recv(9999).decode("utf-8"))
            except OSError as err:
                logger.info('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans["DATA"])
            if "RESPONSE" in ans and ans["RESPONSE"] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.names[message["USER"]["ACCOUNT_NAME"]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    client.send(json.dumps({"RESPONSE": 200}).encode('utf-8'))
                except OSError:
                    self.remove_client(message["USER"]["ACCOUNT_NAME"])
                self.database.user_login(
                    message["USER"]["ACCOUNT_NAME"],
                    client_ip,
                    client_port,
                    message["USER"]["PUBLIC_KEY"])
            else:
                response = {"RESPONSE": 400}
                response["ERROR"] = 'Неверный пароль.'
                try:
                    client.send(json.dumps(response).encode('utf-8'))
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        for client in self.names:
            try:
                self.names[client].send(json.dumps({"RESPONSE": 205}))
            except OSError:
                self.remove_client(self.names[client])
