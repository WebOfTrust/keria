import unittest
from falcon import falcon
from falcon.testing import helpers
from falcon.http_status import HTTPStatus
from keria.core.httping import HandleCORS

class HandleCORSTest(unittest.TestCase):
    def setUp(self):
        self.cors_handler = HandleCORS()

    def test_process_request(self):
        req = helpers.create_environ(method='GET')
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        self.assertEqual(resp.get_header('Access-Control-Allow-Origin'), '*')
        self.assertEqual(resp.get_header('Access-Control-Allow-Methods'), '*')
        self.assertEqual(resp.get_header('Access-Control-Allow-Headers'), '*')
        self.assertEqual(resp.get_header('Access-Control-Max-Age'), '1728000')

    def test_process_request_options_method(self):
        req = helpers.create_environ(method='OPTIONS')
        resp = falcon.Response()

        with self.assertRaises(HTTPStatus) as cm:
            self.cors_handler.process_request(req, resp)

        self.assertEqual(cm.exception.status, falcon.HTTP_200)
