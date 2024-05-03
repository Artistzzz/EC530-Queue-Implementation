import json
import unittest
import requests
from app import app  

'''
The test is for checking:
Authentication: Ensures that users can log in with valid credentials and are denied access with incorrect ones.
Message Queuing: Confirms that sensor data is received and appropriately queued for processing, indicating the API handles and queues incoming data as expected.
'''

'''
Expected test results:
test_login_success:
Status Code: 200 OK
Content: Includes an access_token.
test_login_failure:
Status Code: 401 Unauthorized
Content: Error message like "Bad username or password."
test_sensor_data_queue:
Status Code: 202 Accepted
Content: Message "Data queued for processing."
'''

class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_login_success(self):
        # Test the login functionality
        response = self.app.post('/login', json={'username': 'admin', 'password': 'secret'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', json.loads(response.data))

    def test_login_failure(self):
        # Test login failure
        response = self.app.post('/login', json={'username': 'wrong', 'password': 'user'})
        self.assertEqual(response.status_code, 401)

    def test_sensor_data_queue(self):
        # Assuming that RabbitMQ setup and Flask app are configured to handle this correctly
        sensor_data = {
            'temperature': 22.5,
            'humidity': 55
        }
        response = self.app.post('/sensor-data', json=sensor_data)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(json.loads(response.data)['message'], 'Data queued for processing')

if __name__ == '__main__':
    unittest.main()