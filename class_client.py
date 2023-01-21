import time
import dis
import sys
import json
import socket
import argparse
import logging
import threading


sys.path.append('./log')


from client_log_config import logger
from log_decorator import *
from meta_classes import ClientMaker
from client_db import ClientDatabase

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def create_exit_message(self):
        return {
            "ACTION": "EXIT",
            "TIME": f"{time.time()}",
            "ACCOUNT_NAME": f"{self.account_name}"
        }

    def create_message(self):
        to = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')

        with database_lock:
            if not self.database.check_user(to):
                logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {to}')
                return

        message_dict = {
            "ACTION": "MESSAGE",
            "SENDER": f"{self.account_name}",
            "DESTINATION": "to",
            "TIME": f"{time.time()}",
            "MESSAGE_TEXT": f"{message}"
        }
        logger.info(f'Сформирован словарь сообщения: {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name, to, message)
        with sock_lock:
            try:
                self.sock.send(json.dumps(message_dict).encode("utf-8"))
                logger.info(f'Отправлено сообщение для пользователя {to}')
            except:
                logger.critical('Потеряно соединение с сервером.')
                exit(1)

    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()

            elif command == 'help':
                self.print_help()

            elif command == 'exit':
                with sock_lock:
                    try:
                        self.sock.send(json.dumps(self.create_exit_message()).encode("utf-8"))
                    except:
                        pass
                    print('Завершение соединения.')
                    logger.info('Завершение работы по команде пользователя.')
                    time.sleep(0.5)
                    break

            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()

            elif command == 'server':
                ans = input('Вы можете отправить запрос на добавление/удаление конткта на стороне сервера.\n'
                            'add - добавить, del - удалить: ')
                if ans == 'add':
                    name = input('Введите имя пользователя: ')
                    self.add_contact(name)
                elif ans == 'del':
                    name = input('Введите имя пользователя: ')
                    self.remove_contact(name)
                else:
                    print('Некорректная команда. Возвращение...')
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def add_contact(self, contact):
        logger.info(f'Создание контакта {contact}')
        req = {
            "ACTION": "ADD_CONTACT",
            "TIME": f"{time.time()}",
            "USER": f"{self.account_name}",
            "ACCOUNT_NAME": f"{contact}"
        }
        self.sock.send(json.dumps(req).encode("utf-8"))
        ans = json.loads(self.sock.recv(9999).decode("utf-8"))
        if "RESPONSE" in ans and ans["RESPONSE"] == 200:
            pass
        else:
            print('Ошибка создания контакта')
            return
        print('Удачное создание контакта.')

    def remove_contact(self, contact):
        logger.info(f'Создание контакта {contact}')
        req = {
            "ACTION": "REMOVE_CONTACT",
            "TIME": f"{time.time()}",
            "USER": f"{self.account_name}",
            "ACCOUNT_NAME": f"{contact}"
        }
        self.sock.send(json.dumps(req).encode("utf-8"))
        ans = json.loads(self.sock.recv(9999).decode("utf-8"))
        if "RESPONSE" in ans and ans["RESPONSE"] == 200:
            pass
        else:
            print('Ошибка удаления клиента')
            return
        print('Удачное удаление')

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('server - для отправки зпросов серверу')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock, self.account_name, edit)
                    except ServerError:
                        logger.error('Не удалось отправить информацию на сервер.')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    def run(self):
        while True:
            with sock_lock:
                try:
                    message = json.loads(self.sock.recv(9999).decode('utf-8'))
                    if "ACTION" in message and message["ACTION"] == "MESSAGE" and "SENDER" in message\
                            and "DESTINATION" in message and "MESSAGE_TEXT" in message\
                            and message["DESTINATION"] == self.account_name:
                        print(f'\nПолучено сообщение от пользователя {message["SENDER"]}:\n{message["MESSAGE_TEXT"]}')
                        logger.info(f'Получено сообщение от пользователя {message["SENDER"]}:\n{message["MESSAGE_TEXT"]}')
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')
                except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break
                except Exception:
                    logger.error(f'Не удалось декодировать полученное сообщение.')
                    exit(1)


@logging
def create_presence(account_name):
    out = {
        "ACTION": "PRESENCE",
        "TIME": f"{time.time()}",
        "USER": {
            "ACCOUNT_NAME": f"{account_name}"
        }
    }
    logger.info(f'Сформировано "PRESENCE" сообщение для пользователя {account_name}')
    return json.dumps(out).encode("utf-8")


@logging
def process_response_ans(message):
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    message = json.loads(message.decode("utf-8"))
    if "RESPONSE" in message:
        if message["RESPONSE"] == "200":
            return '200 : OK'
        elif message["RESPONSE"] == "400":
            exit(f'400 : {message["ERROR"]}')
    exit('Некорректный ответ')


@logging
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('addr', default='localhost', nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Неподходящий номер порта: {server_port}. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name


def contacts_list_request(sock, name):
    logger.info(f'Запрос контакт листа для пользователся {name}')
    req = {
        "ACTION": "GET_CONTACTS",
        "TIME": F"{time.time()}",
        "USER": f"{name}"
    }
    logger.info(f'Сформирован запрос {req}')
    sock.send(json.dumps(req).encode("utf-8"))
    ans = json.loads(sock.recv(9999).decode("utf-8"))
    logger.info(f'Получен ответ {ans}')
    if "RESPONSE" in ans and ans["RESPONSE"] == 202:
        return ans["LIST_INFO"]


def user_list_request(sock, username):
    logger.info(f'Запрос списка известных пользователей {username}')
    req = {
        "ACTION": "USERS_REQUEST",
        "TIME": f"{time.time()}",
        "ACCOUNT_NAME": f"{username}"
    }
    sock.send(json.dumps(req).encode("utf-8"))
    ans = json.loads(sock.recv(9999).decode("utf-8"))
    if "RESPONSE" in ans and ans["RESPONSE"] == 202:
        return ans["LIST_INFO"]


def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except:
        logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except:
        logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    print('Консольный месседжер. Клиентский модуль.')
    server_address, server_port, client_name = arg_parser()

    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        transport.send(create_presence(client_name))
        answer = process_response_ans(transport.recv(9999))
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except Exception:
        logger.error('Неудалось соединиться с сервером')
        exit(1)
    else:
        database = ClientDatabase(client_name)
        database_load(transport, database, client_name)

        module_reciver = ClientReader(client_name, transport)
        module_reciver.daemon = True
        module_reciver.start()

        module_sender = ClientSender(client_name, transport)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if module_reciver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
