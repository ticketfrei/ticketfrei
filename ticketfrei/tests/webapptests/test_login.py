from webtest import TestApp
import unittest
import frontend

app = TestApp(frontend.application)

class TestLogin(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_login_not_registered(self):
        request = app.post('/login', {'email': '', 'pass': ''}, expect_errors=True)
        self.assertEqual(401, request.status_code)

    def test_login_registered(self):
        request = app.post('/register', {'email': 'foo@abc.de', 'pass': 'bar', 'pass-repeat': 'bar', 'city': 'testcity'}, expect_errors=True)
        request = app.post('/login', {'email': 'foor@abc.de', 'pass': 'bar'}, expect_errors=False)
        self.assertEqual(200, request.status_code)

