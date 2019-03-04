from webtest import TestApp
import unittest
from ticketfrei import frontend

class TestLogin(unittest.TestCase):

    def test_login_not_registered(self):
        app = TestApp(frontend.application)
        request = app.post('/login', {'email': 'foo@abc.de', 'pass': 'bar'}, expect_errors=True)
        self.assertEqual(request.status_code, 401)

class TestRegister(unittest.TestCase):

    def test_register(self):
        app = TestApp(frontend.application)
        request = app.post('/register', {'email': 'foo@abc.de', 'pass': 'bar', 'pass-repeat': 'bar', 'city': 'testcity'}, expect_errors=True)
        self.assertEqual(request.status_code, 201)

    def test_getRoot(self):
        app = TestApp(frontend.application)
        request = app.get('/')
        self.assertEqual(request.status_code, 200)


if __name__ == '__main__':
    unittest.main()
