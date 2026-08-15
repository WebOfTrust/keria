import unittest
from unittest import mock

from falcon import falcon
from falcon.testing import helpers
from falcon.http_status import HTTPStatus
from keria.core import httping
from keria.core.httping import HandleCORS


class HandleCORSTest(unittest.TestCase):
    def setUp(self):
        self.cors_handler = HandleCORS()

    def test_process_request(self):
        req = helpers.create_req(method="GET")
        resp = falcon.Response()

        self.cors_handler.process_request(req, resp)

        self.assertEqual(resp.get_header("Access-Control-Allow-Origin"), "*")
        self.assertEqual(resp.get_header("Access-Control-Allow-Methods"), "*")
        self.assertEqual(resp.get_header("Access-Control-Allow-Headers"), "*")
        self.assertEqual(resp.get_header("Access-Control-Max-Age"), "1728000")

    def test_process_request_options_method(self):
        req = helpers.create_req(method="OPTIONS")
        resp = falcon.Response()

        with self.assertRaises(HTTPStatus) as cm:
            self.cors_handler.process_request(req, resp)

        self.assertEqual(cm.exception.status, falcon.HTTP_200)


def test_request_logger_preserves_binary_body():
    body = b"\xff\xfe\x00sealed"
    req = helpers.create_req(method="POST", body=body)
    resp = falcon.Response()
    middleware = httping.RequestLoggerMiddleware()

    with (
        mock.patch.object(httping.logger, "isEnabledFor", return_value=True),
        mock.patch.object(httping.logger, "debug") as debug,
    ):
        middleware.process_request(req, resp)

    debug.assert_any_call("Request body    : %r", body)
    assert req.stream.read() == body
    req.stream.seek(0)
    assert req.bounded_stream.read() == body
