# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.httping module

"""

import io
import logging
from urllib.parse import urlsplit

import falcon
from falcon.http_status import HTTPStatus
from hio.core import tcp, http

from keria import ogler, log_name

logger = ogler.getLogger(log_name)


class HandleCORS(object):
    def process_request(self, req, resp):
        resp.set_header("Access-Control-Allow-Origin", "*")
        resp.set_header("Access-Control-Allow-Methods", "*")
        resp.set_header("Access-Control-Allow-Headers", "*")
        resp.set_header("Access-Control-Expose-Headers", "*")
        resp.set_header("Access-Control-Max-Age", 1728000)  # 20 days
        if req.method == "OPTIONS":
            raise HTTPStatus(falcon.HTTP_200)


def getRequiredParam(body, name):
    param = body.get(name)
    if param is None:
        raise falcon.HTTPBadRequest(
            description=f"required field '{name}' missing from request"
        )

    return param


def parseRangeHeader(header, name, start=0, end=9):
    """Parse the start and end requested range values, defaults are 0, 9

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
        logger.info("Request received : %s %s", req.method, req.url)
        logger.debug("Request headers : %s", req.headers)
        if req.content_length and logger.isEnabledFor(logging.DEBUG):
            # Read and re-set the stream to allow further processing
            body = req.bounded_stream.read()
            decoded_body = body.decode("utf-8") if body else "<empty>"
            logger.debug("Request body    : %s", decoded_body)
            # Reset the stream for further processing. Falcon reads the body
            # through req.stream (bound to wsgi.input when the request was
            # built) and caches req.bounded_stream, so all three are reset.
            req.stream = req.env["wsgi.input"] = io.BytesIO(body)
            req._bounded_stream = None
            req.env["CONTENT_LENGTH"] = str(
                len(body)
            )  # match WSGI env content length to body length
        else:
            logger.debug("Request body    : No body")

    def process_response(
        self, req: falcon.Request, resp: falcon.Response, resource, req_succeeded
    ):
        """Log outgoing responses."""
        logger.info("Response status  : %s on %s %s", resp.status, req.method, req.url)
        logger.debug("Response headers: %s", resp.headers)


keriHeaders = [
    "cesr-attachment",
    "cesr-date",
    "content-type",
    "signature",
    "signature-input",
    "signify-resource",
    "signify-timestamp",
    "signify-receiver",
]

corsMiddleware = falcon.CORSMiddleware(
    allow_origins="*", allow_credentials="*", expose_headers=keriHeaders
)


def falconApp(logRequests=False, request_type=falcon.Request):
    middlewares: list = [corsMiddleware]
    if logRequests:
        middlewares.append(RequestLoggerMiddleware())
    return falcon.App(middleware=middlewares, request_type=request_type)


def exposeRawUri(server):
    """
    Makes an hio WSGI server also pass the request target as sent to the app.

    hio percent-decodes the request path and re-encodes it with quote() to
    build PATH_INFO, so the application never sees the client's bytes. An RFC
    9421 verifier needs them for @path (RFC 9421 section 2.2.6), so this adds
    the raw request target to every environ the server builds, as RAW_URI,
    the name gunicorn uses.

    Parameters:
        server (hio.core.http.Server): server whose environ to extend

    Returns:
        hio.core.http.Server: the same server
    """
    build = getattr(server, "buildEnviron", None)
    if build is None:  # not a WSGI server, nothing to extend
        return server

    def buildEnviron(requestant):
        environ = build(requestant)
        environ["RAW_URI"] = requestant.url
        return environ

    server.buildEnviron = buildEnviron
    return server


def rawPath(req):
    """
    Returns the path of the request target as the client sent it, percent
    encoding included, from RAW_URI when the server provides it, and
    otherwise req.path. An empty path is "/".

    Parameters:
        req (falcon.Request): request whose environ may carry RAW_URI
    """
    raw = req.env.get("RAW_URI")
    if raw is None:
        return req.path
    if raw.startswith("/"):  # origin-form, the usual case
        path = raw.split("?", 1)[0].split("#", 1)[0]
    else:  # absolute-form
        path = urlsplit(raw).path
    return path or "/"


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
        hio.core.http.Server: with RAW_URI in its environ (see exposeRawUri)
    """
    if keypath is not None and certpath is not None and cafilepath is not None:
        servant = tcp.ServerTls(
            certify=False,
            keypath=keypath,
            certpath=certpath,
            cafilepath=cafilepath,
            port=port,
        )
        server = http.Server(port=port, app=app, servant=servant)
    else:
        server = http.Server(port=port, app=app)
    return exposeRawUri(server)
