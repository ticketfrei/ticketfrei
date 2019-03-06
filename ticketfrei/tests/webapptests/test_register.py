from webtest import TestApp
import unittest
import frontend

app = TestApp(frontend.application)

class TestRegister(unittest.TestCase):

    def test_register(self):
        request = app.post('/register', {'email': 'foo@abc.de', 'pass': 'bar', 'pass-repeat': 'bar', 'city': 'testcity'}, expect_errors=True)
        self.assertEqual(200, request.status_code)

    def test_getRoot(self):
        request = app.get('/')
        self.assertEqual(200, request.status_code)

