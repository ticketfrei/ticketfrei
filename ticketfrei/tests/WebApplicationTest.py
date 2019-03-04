from webtest import TestApp
import unittest
import frontend

class TestLogin(unittest.TestCase):

    def test_login_not_registered(self):
        app = TestApp(frontend.application)
        request = app.post('/login', {'email': '', 'pass': ''}, expect_errors=True)
        self.assertEqual(401, request.status_code)

class TestRegister(unittest.TestCase):

    def test_register(self):
        app = TestApp(frontend.application)
        request = app.post('/register', {'email': 'foo@abc.de', 'pass': 'bar', 'pass-repeat': 'bar', 'city': 'testcity'}, expect_errors=True)
        self.assertEqual(200, request.status_code)

    def test_getRoot(self):
        app = TestApp(frontend.application)
        request = app.get('/')
        self.assertEqual(200, request.status_code)


if __name__ == '__main__':
    unittest.main()
