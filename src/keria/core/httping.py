# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.httping module

"""
import io
import logging

import falcon
from falcon.http_status import HTTPStatus
from hio.core import tcp, http

from keria import ogler, log_name

logger = ogler.getLogger(log_name)

class HandleCORS(object):
    def process_request(self, req, resp):
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', '*')
        resp.set_header('Access-Control-Allow-Headers', '*')
        resp.set_header('Access-Control-Max-Age', 1728000)  # 20 days
        if req.method == 'OPTIONS':
            raise HTTPStatus(falcon.HTTP_200)


def getRequiredParam(body, name):
    param = body.get(name)
    if param is None:
        raise falcon.HTTPBadRequest(description=f"required field '{name}' missing from request")

    return param


def parseRangeHeader(header, name, start=0, end=9):
    """ Parse the start and end requested range values, defaults are 0, 9

    Parameters:
        header(str):  HTTP Range header value
        name (str): range name to look for
        start (int): default start index
        end(int): default end index

    Returns:
        (start, end): tuple of start index and end index

    """

    if not header.startswith(f"{name}="):
        return start, end

    header = header.strip(f"{name}=")
    try:
        if header.startswith("-"):
            return start, int(header[1:])

        if header.endswith("-"):
            return int(header[:-1]), end

        vals = header.split("-")
        if not len(vals) == 2:
            return start, end

        return int(vals[0]), int(vals[1])
    except ValueError:
        return start, end


# noinspection PyMethodMayBeStatic
class RequestLoggerMiddleware:
    """Simple request logger Falcon middleware."""

    def process_request(self, req: falcon.Request, resp: falcon.Response):
        """Log incoming requests."""
        logger.info('Request received : %s %s', req.method, req.url)
        logger.debug('Request headers : %s', req.headers)
        if req.content_length and logger.isEnabledFor(logging.DEBUG):
            # Read and re-set the stream to allow further processing
            body = req.stream.read()
            decoded_body = body.decode('utf-8') if body else '<empty>'
            logger.debug('Request body    : %s', decoded_body)
            req.env['wsgi.input'] = io.BytesIO(body)  # Reset the stream for further processing
            req.env['CONTENT_LENGTH'] = str(len(body))  # match WSGI env content length to body length
        else:
            logger.debug('Request body    : No body')

    def process_response(self, req: falcon.Request, resp: falcon.Response, resource, req_succeeded):
        """Log outgoing responses."""
        logger.info('Response status  : %s on %s %s', resp.status, req.method, req.url)
        logger.debug('Response headers: %s', resp.headers)


def keri_headers():
    return [
        'cesr-attachment',
        'cesr-date',
        'content-type',
        'signature',
        'signature-input',
        'signify-resource',
        'signify-timestamp'
    ]


def corsMiddleware():
    return falcon.CORSMiddleware(
        allow_origins='*',
        allow_credentials='*',
        expose_headers=keri_headers()
    )


def falconApp():
    return falcon.App(middleware=[corsMiddleware(), RequestLoggerMiddleware()])


def createHttpServer(port, app, keypath=None, certpath=None, cafilepath=None):
    """
    Create an HTTP or HTTPS server depending on whether TLS key material is present

    Parameters:
        port (int)         : port to listen on for all HTTP(s) server instances
        app (falcon.App)   : application instance to pass to the http.Server instance
        keypath (string)   : the file path to the TLS private key
        certpath (string)  : the file path to the TLS signed certificate (public key)
        cafilepath (string): the file path to the TLS CA certificate chain file
    Returns:
        hio.core.http.Server
    """
    if keypath is not None and certpath is not None and cafilepath is not None:
        servant = tcp.ServerTls(certify=False,
                                keypath=keypath,
                                certpath=certpath,
                                cafilepath=cafilepath,
                                port=port)
        server = http.Server(port=port, app=app, servant=servant)
    else:
        server = http.Server(port=port, app=app)
    return server
