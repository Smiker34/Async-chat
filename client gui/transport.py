import socket
import sys
import time
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../log')


from client_log_config import logger
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.password = passwd
        self.transport = None
        self.keys = keys
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error(
                'Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            exit('Потеряно соединение с сервером!')
        self.running = True

    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                logger.info("Connection established.")
                break
            time.sleep(1)

        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            exit('Не удалось установить соединение с сервером')

        logger.info('Starting auth dialog.')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        logger.info(f'Passwd hash ready: {passwd_hash_string}')

        pubkey = self.keys.publickey().export_key().decode('ascii')

        with socket_lock:
            presense = {
                "ACTION": "PRESENCE",
                "TIME": f"{time.time()}",
                "USER": {
                    "ACCOUNT_NAME": f"{self.username}",
                    "PUBLIC_KEY": f"{pubkey}"
                }
            }
            logger.info(f"Presense message = {presense}")
            try:
                self.transport.send(json.dumps(presense).encode("utf-8"))
                ans = json.loads(self.transport.recv(9999).decode("utf-8"))
                logger.info(f'Server response = {ans}.')
                if "RESPONSE" in ans:
                    if ans["RESPONSE"] == 400:
                        exit(ans["ERROR"])
                    elif ans["RESPONSE"] == 511:
                        ans_data = ans["DATA"]
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = {"RESPONSE": 511}
                        my_ans["DATA"] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        self.process_server_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                logger.info(f'Connection error.', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')

    def process_server_ans(self, message):
        logger.info(f'Разбор сообщения от сервера: {message}')

        if RESPONSE in message:
            if message["RESPONSE"] == 200:
                return
            elif message["RESPONSE"] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message["RESPONSE"] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                logger.error(
                    f'Принят неизвестный код подтверждения {message["RESPONSE"]}')

        elif "ACTION" in message and message["ACTION"] == "MESSAGE" and SENDER in message and "DESTINATION" in message \
                and "MESSAGE_TEXT" in message and message["DESTINATION"] == self.username:
            logger.info(
                f'Получено сообщение от пользователя {message["SENDER"]}:{message["MESSAGE_TEXT"]}')
            self.new_message.emit(message)

    def key_request(self, user):
        logger.info(f'Запрос публичного ключа для {user}')
        req = {
            "ACTION": "PUBLIC_KEY_REQUEST",
            "TIME": f"{time.time()}",
            "ACCOUNT_NAME": f"{user}"
        }
        with socket_lock:
            self.transport.send(json.dumps(req).encode('utf-8'))
            ans = json.loads(self.transport.recv(9999).decode('utf-8'))
        if "RESPONSE" in ans and ans["RESPONSE"] == 511:
            return ans["DATA"]
        else:
            logger.error(f'Не удалось получить ключ собеседника{user}.')

    def create_presence(self):
        out = {
            "ACTION": "PRESENCE",
            "TIME": f"{time.time()}",
            "USER": {
                "ACCOUNT_NAME": f"{self.username}"
            }
        }
        logger.info(f'Сформировано "PRESENCE" сообщение для пользователя {self.username}')
        return out

    def process_server_ans(self, message):
        logger.info(f'Разбор сообщения от сервера: {message}')

        if "RESPONSE" in message:
            if message["RESPONSE"] == 200:
                return
            elif message["RESPONSE"] == 400:
                exit(f'{message["ERROR"]}')
            else:
                logger.info(f'Принят неизвестный код подтверждения {message["RESPONSE"]}')

        elif "ACTION" in message and message["ACTION"] == "MESSAGE" and "SENDER" in message and "DESTINATION" in message \
                and "MESSAGE_TEXT" in message and message["DESTINATION"] == self.username:
            logger.info(f'Получено сообщение от пользователя {message["SENDER"]}:{message["MESSAGE_TEXT"]}')
            self.database.save_message(message["SENDER"], 'in', message["MESSAGE_TEXT"])
            self.new_message.emit(message["SENDER"])


    def contacts_list_update(self):
        logger.info(f'Запрос контакт листа для пользователся {self.name}')
        req = {
            "ACTION": "GET_CONTACTS",
            "TIME": f"{time.time()}",
            "USER": f"{self.username}"
        }
        logger.info(f'Сформирован запрос {req}')
        with socket_lock:
            self.transport.send(json.dumps(req).encode("utf-8"))
            ans = json.loads(self.transport.recv(9999).decode("utf-8"))
        logger.info(f'Получен ответ {ans}')
        if "RESPONSE" in ans and ans["RESPONSE"] == 202:
            for contact in ans["LIST_INFO"]:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        logger.info(f'Запрос списка известных пользователей {self.username}')
        req = {
            "ACTION": "USERS_REQUEST",
            "TIME": f"{time.time()}",
            "ACCOUNT_NAME": f"{self.username}"
        }
        with socket_lock:
            self.transport.send(json.dumps(req).encode("utf-8"))
            ans = json.loads(self.transport.recv(9999).decode("utf-8"))
        if "RESPONSE" in ans and ans["RESPONSE"] == 202:
            self.database.add_users(ans["LIST_INFO"])
        else:
            logger.error('Не удалось обновить список известных пользователей.')

    def add_contact(self, contact):
        logger.info(f'Создание контакта {contact}')
        req = {
            "ACTION": "ADD_CONTACT",
            "TIME": f"{time.time()}",
            "USER": f"{self.username}",
            "ACCOUNT_NAME": f"{contact}"
        }
        with socket_lock:
            self.transport.send(json.dumps(req).encode("utf-8"))
            self.process_server_ans(json.loads(self.transport.recv(9999).decode("utf-8")))

    def remove_contact(self, contact):
        logger.info(f'Удаление контакта {contact}')
        req = {
            "ACTION": "REMOVE_CONTACT",
            "TIME": f"{time.time()}",
            "USER": f"{self.username}",
            "ACCOUNT_NAME": f"{contact}"
        }
        with socket_lock:
            self.transport.send(json.dumps(req).encode("utf-8"))
            self.process_server_ans(json.loads(self.transport.recv(9999).decode("utf-8")))

    def transport_shutdown(self):
        self.running = False
        message = {
            "ACTION": "EXIT",
            "TIME": f"{time.time()}",
            "ACCOUNT_NAME": f"{self.username}"
        }
        with socket_lock:
            try:
                self.transport.send(json.dumps(message).encode("utf-8"))
            except OSError:
                pass
        logger.info('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, to, message):
        message_dict = {
            "ACTION": "MESSAGE",
            "SENDER": f"{self.username}",
            "DESTINATION": f"{to}",
            "TIME": f"{time.time()}",
            "MESSAGE_TEXT": f"{message}"
        }
        logger.info(f'Сформирован словарь сообщения: {message_dict}')

        with socket_lock:
            self.transport.send(json.dumps(message_dict).encode("utf-8"))
            self.process_server_ans(json.loads(self.transport.recv(9999).decode("utf-8")))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        logger.info('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = json.loads(self.transport.recv(9999).decode("utf-8"))
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.info(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                else:
                    logger.info(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
