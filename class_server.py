import socket
import sys
import argparse
import json
import logging
import select
import time
import threading
import os
import configparser


sys.path.append('./log')


from server_log_config import logger
from log_decorator import *
from descript import Port
from meta_classes import ServerMaker
from server_db import Storage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem


new_connection = False
conflag_lock = threading.Lock()

@logging
def arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port
        self.database = database
        self.clients = []
        self.messages = []
        self.names = []
        super().__init__()

    def init_socket(self):
        logger.info(f'Запущен сервер, порт для подключений: {self.port} ,'
                    f' адрес с которого принимаются подключения: {self.addr}.')
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(2)
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
        global new_connection
        logger.info(f'Разбор сообщения от клиента : {message}')
        message = json.loads(message.decode("utf-8"))
        if "ACTION" in message and message["ACTION"] == "PRESENCE" and "TIME" in message and "USER" in message:
            if message["USER"]["ACCOUNT_NAME"] not in self.names:
                self.names.append(message["USER"]["ACCOUNT_NAME"])
                client_ip, client_port = client.getpeername()
                self.database.user_login(message["USER"]["ACCOUNT_NAME"], client_ip, client_port)
                client.send(json.dumps({"RESPONSE": "200"}).encode("utf-8"))
                with conflag_lock:
                    new_connection = True
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
            with conflag_lock:
                new_connection = True
            return

        elif "ACTION" in message and message["ACTION"] == "GET_CONTACTS" and "USER" in message and \
                self.names[message["USER"]] == client:
            client.send(json.dumps({"RESPONSE": "202",
                                    "LIST_INFO": f"{self.database.get_contacts(message[USER])}"}).encode("utf-8"))

        elif "ACTION" in message and message["ACTION"] == "ADD_CONTACT" and "ACCOUNT_NAME" in message \
                and "USER" in message and self.names[message["USER"]] == client:
            self.database.add_contact(message[{"USER"}], message["ACCOUNT_NAME"])
            client.send(json.dumps({"RESPONSE": "200"}).encode("utf-8"))

        elif "ACTION" in message and message["ACTION"] == "REMOVE_CONTACT" and "ACCOUNT_NAME" in message \
                and "USER" in message and self.names[message["USER"]] == client:
            self.database.remove_contact(message["USER"], message["ACCOUNT_NAME"])
            client.send(json.dumps({"RESPONSE": "200"}).encode("utf-8"))

        elif "ACTION" in message and message["ACTION"] == "USERS_REQUEST" and "ACCOUNT_NAME" in message \
                and self.names[message["ACCOUNT_NAME"]] == client:
            client.send(json.dumps({"RESPONSE": "202",
                                    "LIST_INFO": f"{[user[0] for user in self.database.users_list()]}"}).encode("utf-8"))

        else:
            response = {"RESPONSE": "400"}
            response["ERROR"] = 'Запрос некорректен.'
            client.send(json.dumps(response).encode("utf-8"))
            return


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = Storage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
