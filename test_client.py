import unittest
import time
import threading


from client import *
from server import *


class TestClient(unittest.TestCase):
    def test_create_message(self):
        created_message = create_message()

        self.assertIsInstance(created_message, bytes)
        self.assertIn(b'action', created_message)
        self.assertIn(b'time', created_message)
        self.assertIn(b'user', created_message)

    def test_create_message_with_account_name(self):
        created_message = create_message('Username')

        self.assertIn(b'Username', created_message)

    def test_read_response(self):
        response = {
            "response": "200",
            "time": f"{time.time()}",
            "message": "OK"
        }

        encoded_response = json.dumps(response).encode('utf-8')

        decoded_response = read_response(encoded_response)

        self.assertEqual(decoded_response, [response['response'], response['message']])

    def test_client_main(self):
        server = threading.Thread(target=server_main)
        server.daemon = True
        server.start()
        client_main()


if __name__ == '__main__':
    unittest.main()
