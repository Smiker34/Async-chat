import unittest
import time
import sys
import threading

sys.path.append('../Lesson 3')

from client import *
from server import *


class TestClient(unittest.TestCase):
    def test_message_response(self):
        message = b'{"action": "presence", "time": "1669985757.9891014", "user": {"account_name": "DEFAULT"}}'

        response = message_response(message)

        self.assertIsInstance(response, bytes)
        self.assertIn(b'response', response)
        self.assertIn(b'message', response)

    def test_server_main(self):
        server = threading.Thread(target=server_main)
        server.daemon = True
        server.start()
        client_main()


if __name__ == '__main__':
    unittest.main()
