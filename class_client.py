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


class ClientSender(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
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
        message_dict = {
            "ACTION": "MESSAGE",
            "SENDER": f"{self.account_name}",
            "DESTINATION": "to",
            "TIME": f"{time.time()}",
            "MESSAGE_TEXT": f"{message}"
        }
        logger.info(f'Сформирован словарь сообщения: {message_dict}')
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
                try:
                    self.sock.send(json.dumps(self.create_exit_message()).encode("utf-8"))
                except:
                    pass
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


class ClientReader(threading.Thread, metaclass=ClientMaker):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        while True:
            try:
                message = json.loads(self.sock.recv(9999).decode('utf-8'))
                if "ACTION" in message and message["ACTION"] == "MESSAGE" and "SENDER" in message and "DESTINATION" in message \
                        and "MESSAGE_TEXT" in message and message["DESTINATION"] == self.account_name:
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
    parser.add_argument('addr', default='localhost', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
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
