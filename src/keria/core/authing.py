# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.authing module

"""

import json
import re
import sys
from dataclasses import dataclass
from io import BytesIO
from enum import Enum
from itertools import chain
from urllib.parse import quote, unquote, unquote_to_bytes, urlsplit
from abc import ABC, abstractmethod

import falcon
import pysodium
from hio.help import Hict
from keri import kering
from keri.core import coring, MtrDex
from keri.end import ending
from keri.help import helping

from typing import TYPE_CHECKING, Any, Mapping, Sequence

if TYPE_CHECKING:
    from keria.app.agenting import Agency

ESSR_CONTEXT_KEY = "keria.essr.context"
HTTP_TOKEN = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
REQUEST_LINE = re.compile(
    r"(?P<method>[!#$%&'*+\-.^_`|~0-9A-Za-z]+) "
    r"(?P<target>\S+) (?P<protocol>HTTP/1\.[01])"
)


def isCorsHeader(name: str) -> bool:
    """Return whether ``name`` is an HTTP CORS response header."""
    return name.lower().startswith("access-control-")


@dataclass(frozen=True)
class ESSRResponseContext:
    """Verified information needed to protect a finalized ESSR response."""

    agent: Any
    destination: str
    protocol: str
    method: str


class AuthMode(Enum):
    SIGNED_HEADERS = ("SIGNED_HEADERS",)
    ESSR = "ESSR"


class ModifiableRequest(falcon.Request):
    def reinit(self, env):
        super().__init__(env, options=self.options)


class Authenticator(ABC):
    def __init__(self, agency: "Agency"):
        """Abstract agent authenticator for verifying requests and preparing responses

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents

        Returns:
              Authenticator

        """
        self.agency = agency

    @staticmethod
    def getRequiredHeader(request: falcon.Request, header: str):
        headers = request.headers
        if header not in headers:
            raise ValueError(f"Missing {header} header")
        return headers[header]

    @staticmethod
    def resource(request: falcon.Request):
        return Authenticator.getRequiredHeader(request, "SIGNIFY-RESOURCE")

    @abstractmethod
    def inbound(self, request: ModifiableRequest):
        pass

    @abstractmethod
    def outbound(self, request: ModifiableRequest, response: falcon.Response):
        pass


class SignedHeaderAuthenticator(Authenticator):
    DefaultFields = ["Signify-Resource", "@method", "@path", "Signify-Timestamp"]

    def __init__(self, agency):
        """Create agent authenticator based on RFC-9421 signed header message signatures

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents

        Returns:
              SignedHeaderAuthenticator

        """
        super().__init__(agency)

    def inbound(self, request: ModifiableRequest):
        """Validate that the request is correctly signed based on our version of RFC-9421

        Parameters:
            request (ModifiableRequest): Falcon request object

        """
        headers = request.headers

        siginput = self.getRequiredHeader(request, "SIGNATURE-INPUT")
        signature = self.getRequiredHeader(request, "SIGNATURE")

        resource = self.resource(request)
        agent = self.agency.get(resource)

        if agent is None:
            raise kering.AuthNError("Unknown controller")

        if resource not in agent.agentHab.kevers:
            raise kering.AuthNError(
                "Unknown or invalid controller (controller KEL not resolved)"
            )

        inputs = ending.desiginput(siginput.encode("utf-8"))
        inputs = [i for i in inputs if i.name == "signify"]

        if not inputs:
            raise kering.AuthNError("Missing signify inputs in signature")

        for inputage in inputs:
            items = []
            for field in inputage.fields:
                if field.startswith("@"):
                    if field == "@method":
                        items.append(f'"{field}": {request.method}')
                    elif field == "@path":
                        items.append(f'"{field}": {request.path}')

                else:
                    key = field.upper()
                    field = field.lower()
                    if key not in headers:
                        continue

                    value = ending.normalize(headers[key])
                    items.append(f'"{field}": {value}')

            values = [f"({' '.join(inputage.fields)})", f"created={inputage.created}"]
            if inputage.expires is not None:
                values.append(f"expires={inputage.expires}")
            if inputage.nonce is not None:
                values.append(f"nonce={inputage.nonce}")
            if inputage.keyid is not None:
                values.append(f"keyid={inputage.keyid}")
            if inputage.context is not None:
                values.append(f"context={inputage.context}")
            if inputage.alg is not None:
                values.append(f"alg={inputage.alg}")

            params = ";".join(values)

            items.append(f'"@signature-params: {params}"')
            ser = "\n".join(items).encode("utf-8")

            ckever = agent.agentHab.kevers[resource]
            signages = ending.designature(signature)
            cig = signages[0].markers[inputage.name]
            if not ckever.verfers[0].verify(sig=cig.raw, ser=ser):
                raise kering.AuthNError(f"Signature for {inputage} invalid")

        request.path = unquote(request.path)
        request.context.mode = AuthMode.SIGNED_HEADERS
        request.context.agent = agent

    def outbound(self, request: ModifiableRequest, response: falcon.Response):
        """Generate and add Signature Input and Signature fields to headers of the response

        Parameters:
            request (ModifiableRequest): Falcon request object
            response (Response): Falcon response object

        """
        request.path = quote(request.path)
        agent = request.context.agent
        response.set_header("Signify-Resource", agent.agentHab.pre)
        response.set_header("Signify-Timestamp", helping.nowIso8601())

        headers = Hict(response.headers)
        header, qsig = ending.siginput(
            "signify",
            request.method,
            request.path,
            headers,
            fields=self.DefaultFields,
            hab=agent.agentHab,
            alg="ed25519",
            keyid=agent.agentHab.pre,
        )
        headers.extend(header)
        signage = ending.Signage(
            markers=dict(signify=qsig),
            indexed=False,
            signer=None,
            ordinal=None,
            digest=None,
            kind=None,
        )
        headers.extend(ending.signature([signage]))

        for key, val in headers.items():
            response.set_header(key, val)


class ESSRAuthenticator(Authenticator):
    def __init__(self, agency):
        """Create agent authenticator for verifying requests and signing+encrypting responses using KERI ESSR

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents

        Returns:
              ESSRAuthenticator

        """
        super().__init__(agency)

    def inbound(self, request: ModifiableRequest):
        """Validates that the wrapper request is correctly signed, and decrypts the embedded HTTP request which is
        passed to the controllers.

        Parameters:
            request (ModifiableRequest): Falcon request object

        """
        if request.path != "/":
            raise kering.AuthNError("Request should not expose endpoint in the clear")

        signature = self.getRequiredHeader(request, "SIGNATURE")
        dt = self.getRequiredHeader(request, "SIGNIFY-TIMESTAMP")
        resource = self.resource(request)
        receiver = self.getRequiredHeader(request, "SIGNIFY-RECEIVER")

        agent = self.agency.get(resource)
        if agent is None or agent.pre != receiver:
            raise kering.AuthNError("Unknown or invalid agent")

        if resource not in agent.agentHab.kevers:
            raise kering.AuthNError("Unknown or invalid controller")

        ckever = agent.agentHab.kevers[resource]
        signages = ending.designature(signature)
        cig = signages[0].markers["signify"]

        cipher = request.bounded_stream.read()
        payload = dict(
            src=resource,
            dest=agent.pre,
            d=coring.Diger(ser=cipher, code=MtrDex.Blake3_256).qb64,
            dt=dt,
        )

        if not ckever.verfers[0].verify(
            sig=cig.raw, ser=json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ):
            raise kering.AuthNError("Signature invalid")

        # The real HTTP request is the plaintext of the body of the wrapper to POST /
        outer = request.env
        environ = self.buildEnviron(agent.agentHab.decrypt(ser=cipher), outer)

        # ESSR "Encrypt Sender"
        if (
            "HTTP_SIGNIFY_RESOURCE" not in environ
            or environ["HTTP_SIGNIFY_RESOURCE"] != resource
        ):
            raise kering.AuthNError(
                "ESSR payload missing or incorrect encrypted sender"
            )

        outer[ESSR_CONTEXT_KEY] = ESSRResponseContext(
            agent=agent,
            destination=resource,
            protocol=environ["SERVER_PROTOCOL"],
            method=environ["REQUEST_METHOD"],
        )

        request.reinit(environ)
        request.context.mode = AuthMode.ESSR
        request.context.agent = agent

    def outbound(self, request: ModifiableRequest, response: falcon.Response):
        """Reject response protection before Falcon has finalized the response."""
        raise RuntimeError("ESSR responses must be finalized by ESSRResponseWrapper")

    def wrapResponse(
        self,
        context: ESSRResponseContext,
        status: str,
        headers: Sequence[tuple[str, str]],
        body: bytes,
        cors: Sequence[tuple[str, str]] = (),
    ) -> tuple[str, list[tuple[str, str]], bytes]:
        """Serialize, encrypt, and sign a finalized inner HTTP response."""
        agent = context.agent
        dest = context.destination

        innerHeaders = [
            (name, value)
            for name, value in headers
            if name.lower() != "signify-resource" and not isCorsHeader(name)
        ]
        innerHeaders.append(("signify-resource", agent.agentHab.pre))
        inner = self.serializeResponse(context.protocol, status, innerHeaders, body)

        ckever = agent.agentHab.kevers[dest]
        dt = helping.nowIso8601()
        pubkey = pysodium.crypto_sign_pk_to_box_pk(ckever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(inner, pubkey)

        diger = coring.Diger(ser=raw, code=MtrDex.Blake3_256)
        payload = dict(
            src=agent.agentHab.pre,
            dest=dest,
            d=diger.qb64,
            dt=dt,
        )
        sig = agent.agentHab.sign(
            json.dumps(payload, separators=(",", ":")).encode("utf-8"), indexed=False
        )
        signage = ending.Signage(
            markers=dict(signify=sig[0]),
            indexed=False,
            signer=None,
            ordinal=None,
            digest=None,
            kind=None,
        )
        outerHeaders = [
            ("signify-resource", agent.agentHab.pre),
            ("signify-receiver", dest),
            ("signify-timestamp", dt),
            ("content-type", "application/octet-stream"),
            ("content-length", str(len(raw))),
            *cors,
        ]
        outerHeaders.extend(ending.signature([signage]).items())

        return falcon.HTTP_200, outerHeaders, raw

    @staticmethod
    def buildEnviron(
        raw: bytes, outer: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build a WSGI environment from KERIA's ESSR HTTP request envelope.

        This deliberately implements only the ESSR envelope emitted by Signify
        clients. It is not a general-purpose HTTP parser. The ASCII head is
        terminated by the first CRLFCRLF; all remaining bytes are the body.

        Parameters:
            raw (bytes): The serialized HTTP request
            outer (Mapping): The WSGI environment of the authenticated wrapper

        Returns:
            dict: The WSGI environ

        """
        head, separator, body = raw.partition(b"\r\n\r\n")
        if not separator:
            raise ValueError("ESSR HTTP request head is not terminated by CRLFCRLF")

        lines = head.decode("ascii").split("\r\n")
        if not lines or (match := REQUEST_LINE.fullmatch(lines[0])) is None:
            raise ValueError("Invalid ESSR HTTP request line")

        method = match.group("method")
        url = match.group("target")
        protocol = match.group("protocol")

        try:
            splitUrl = urlsplit(url)
            hostname = splitUrl.hostname
            explicitPort = splitUrl.port
        except ValueError as ex:
            raise ValueError("Invalid ESSR HTTP request authority") from ex

        scheme = splitUrl.scheme.lower()
        if scheme not in ("http", "https"):
            raise ValueError("ESSR request target must use HTTP or HTTPS")
        if not splitUrl.netloc or hostname is None:
            raise ValueError("ESSR request target must include an authority")
        if splitUrl.username is not None or splitUrl.password is not None:
            raise ValueError("ESSR request target must not include userinfo")
        if splitUrl.fragment:
            raise ValueError("ESSR request target must not include a fragment")
        if ":" in hostname and not splitUrl.netloc.startswith("["):
            raise ValueError("IPv6 authorities must be enclosed in brackets")

        path = splitUrl.path or "/"
        if re.search(r"%(?![0-9A-Fa-f]{2})", path):
            raise ValueError("ESSR request target contains invalid percent encoding")
        pathBytes = unquote_to_bytes(path)
        try:
            pathBytes.decode("utf-8")
        except UnicodeDecodeError as ex:
            raise ValueError("ESSR request path is not valid UTF-8") from ex

        headers: dict[str, str] = {}
        for line in lines[1:]:
            name, sep, value = line.partition(":")
            if not sep or HTTP_TOKEN.fullmatch(name) is None:
                raise ValueError(f"Invalid header line {line}")
            key = name.lower()
            if key in headers:
                raise ValueError(f"Duplicate header field {name}")
            value = value.strip(" \t")
            if any(
                ord(char) < 32 and char != "\t" or ord(char) == 127 for char in value
            ):
                raise ValueError(f"Invalid header value for {name}")
            headers[key] = value

        if "transfer-encoding" in headers:
            raise ValueError("Transfer-Encoding is not supported by ESSR")

        suppliedLength = headers.get("content-length")
        if suppliedLength is not None:
            if not suppliedLength.isdecimal() or int(suppliedLength) != len(body):
                raise ValueError("Content-Length does not match the ESSR body")

        authority = splitUrl.netloc
        suppliedHost = headers.get("host")
        if suppliedHost is not None and suppliedHost.lower() != authority.lower():
            raise ValueError("Host does not match the ESSR request target")

        outer = outer or {}
        port = (
            explicitPort
            if explicitPort is not None
            else (443 if scheme == "https" else 80)
        )

        environ = {
            "wsgi.version": outer.get("wsgi.version", (1, 0)),
            "wsgi.input": BytesIO(body),
            "wsgi.errors": outer.get("wsgi.errors", sys.stderr),
            "wsgi.url_scheme": scheme,
            "wsgi.multithread": outer.get("wsgi.multithread", False),
            "wsgi.multiprocess": outer.get("wsgi.multiprocess", False),
            "wsgi.run_once": outer.get("wsgi.run_once", False),
            "REQUEST_METHOD": method,
            "SCRIPT_NAME": "",
            "SERVER_NAME": hostname,
            "SERVER_PORT": str(port),
            "SERVER_PROTOCOL": protocol,
            # PEP 3333 tunnels decoded path bytes through ISO-8859-1.
            "PATH_INFO": pathBytes.decode("iso-8859-1"),
            "QUERY_STRING": splitUrl.query,
            "CONTENT_TYPE": headers.get("content-type", ""),
            "CONTENT_LENGTH": str(len(body)),
            "HTTP_HOST": authority,
        }

        for key in (
            "REMOTE_ADDR",
            "REMOTE_PORT",
            "SERVER_SOFTWARE",
            "wsgi.file_wrapper",
            "wsgi.server_name",
            "wsgi.server_version",
        ):
            if key in outer:
                environ[key] = outer[key]

        for key, value in headers.items():
            if key in ("content-type", "content-length", "host"):
                continue
            key = "HTTP_" + key.replace("-", "_").upper()
            environ[key] = value

        return environ

    @staticmethod
    def serializeResponse(
        protocol: str,
        status: str,
        headers: Sequence[tuple[str, str]],
        body: bytes,
    ) -> bytes:
        """Serialize finalized WSGI response components for an ESSR envelope.

        Parameters:
            protocol (str): HTTP protocol string
            status (str): Final WSGI response status
            headers (Sequence): Ordered, finalized WSGI response headers
            body (bytes): Exact response body bytes

        Returns:
            bytes: The serialized HTTP response

        """
        lines = [f"{protocol} {status}"]
        lines.extend(f"{key}: {value}" for key, value in headers)
        if any("\r" in line or "\n" in line for line in lines):
            raise ValueError("ESSR HTTP response head contains a line break")
        head = "\r\n".join(lines).encode("ascii")

        return head + b"\r\n\r\n" + body


class ESSRResponseWrapper:
    """Seal authenticated ESSR responses after Falcon's WSGI finalization."""

    def __init__(self, app, authn: ESSRAuthenticator):
        self.app = app
        self.authn = authn

    def __call__(self, environ, start_response):
        captured: dict[str, Any] = {}
        written: list[bytes] = []

        def capture(status, headers, exc_info=None):
            if exc_info is not None and captured:
                captured.clear()
            elif captured:
                raise AssertionError("start_response called more than once")
            captured["status"] = status
            captured["headers"] = list(headers)
            return written.append

        iterable = self.app(environ, capture)
        if not captured:
            close = getattr(iterable, "close", None)
            if close is not None:
                close()
            return self._outerError(start_response)

        context = environ.get(ESSR_CONTEXT_KEY)
        if context is None:
            writer = start_response(captured["status"], captured["headers"])
            for chunk in written:
                writer(chunk)
            return iterable

        headers = captured["headers"]
        cors = [(name, value) for name, value in headers if isCorsHeader(name)]
        innerHeaders = [
            (name, value) for name, value in headers if not isCorsHeader(name)
        ]

        try:
            status, innerHeaders, body = self._finalizedBody(
                context,
                captured["status"],
                innerHeaders,
                written,
                iterable,
            )
            outerStatus, outerHeaders, ciphertext = self.authn.wrapResponse(
                context, status, innerHeaders, body, cors
            )
        except Exception:
            return self._outerError(start_response, cors)

        start_response(outerStatus, outerHeaders)
        return [ciphertext]

    @staticmethod
    def _close(iterable):
        close = getattr(iterable, "close", None)
        if close is not None:
            close()

    def _finalizedBody(self, context, status, headers, written, iterable):
        try:
            code = int(status.partition(" ")[0])
        except ValueError:
            self._close(iterable)
            return self._innerError(
                context, falcon.HTTP_500, "Falcon returned an invalid status."
            )

        if 100 <= code < 200:
            self._close(iterable)
            return self._innerError(
                context,
                falcon.HTTP_500,
                "ESSR does not support a standalone informational response.",
            )

        method = context.method.upper()
        if method == "HEAD" or code in (204, 205, 304):
            self._close(iterable)
            headers = self._withoutHeader(headers, "transfer-encoding")
            if code == 204:
                headers = self._withoutHeader(headers, "content-length")
            elif code == 205:
                headers = self._replaceHeader(headers, "content-length", "0")
            return status, headers, b""

        if self._headerValues(headers, "transfer-encoding"):
            self._close(iterable)
            return self._innerError(
                context,
                falcon.HTTP_500,
                "Transfer-Encoding is not supported inside ESSR.",
            )

        lengths = self._headerValues(headers, "content-length")
        if not lengths:
            self._close(iterable)
            return self._innerError(
                context,
                falcon.HTTP_501,
                "Unbounded response streams are not supported by ESSR.",
            )
        if len(lengths) != 1 or not lengths[0].isdecimal():
            self._close(iterable)
            return self._innerError(
                context, falcon.HTTP_500, "Invalid response Content-Length."
            )

        expected = int(lengths[0])
        if expected == 0:
            if any(written):
                self._close(iterable)
                return self._innerError(
                    context, falcon.HTTP_500, "Response exceeded Content-Length."
                )
            self._close(iterable)
            headers = self._replaceHeader(headers, "content-length", "0")
            return status, headers, b""

        chunks: list[bytes] = []
        size = 0
        try:
            for chunk in chain(written, iterable):
                if not isinstance(chunk, bytes):
                    return self._innerError(
                        context, falcon.HTTP_500, "Invalid ESSR response body chunk."
                    )
                if not chunk:
                    continue
                if size + len(chunk) > expected:
                    return self._innerError(
                        context, falcon.HTTP_500, "Response exceeded Content-Length."
                    )
                chunks.append(chunk)
                size += len(chunk)
                if size == expected:
                    break
        except Exception:
            return self._innerError(
                context, falcon.HTTP_500, "Failed to read the ESSR response body."
            )
        finally:
            self._close(iterable)

        if size != expected:
            return self._innerError(
                context, falcon.HTTP_500, "Response ended before Content-Length."
            )

        body = b"".join(chunks)
        headers = self._replaceHeader(headers, "content-length", str(len(body)))
        return status, headers, body

    @staticmethod
    def _headerValues(headers, target):
        return [value for name, value in headers if name.lower() == target]

    @staticmethod
    def _withoutHeader(headers, target):
        return [(name, value) for name, value in headers if name.lower() != target]

    @classmethod
    def _replaceHeader(cls, headers, target, value):
        headers = cls._withoutHeader(headers, target)
        headers.append((target, value))
        return headers

    @staticmethod
    def _innerError(_context, status, message):
        body = message.encode("utf-8")
        return (
            status,
            [
                ("content-type", "text/plain; charset=utf-8"),
                ("content-length", str(len(body))),
            ],
            body,
        )

    @staticmethod
    def _outerError(start_response, cors=()):
        start_response(
            falcon.HTTP_500,
            [("content-length", "0"), *cors],
        )
        return [b""]


class AuthenticationMiddleware:
    """Authenticate incoming signed requests and sign outbound responses (optionally encrypted)"""

    def __init__(
        self,
        agency,
        authn: SignedHeaderAuthenticator,
        essrAuthn: ESSRAuthenticator = None,
        allowed=None,
    ):
        """

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents
            authn (SignedHeaderAuthenticator): Authenticator to validate signature headers on request
            essrAuthn (ESSRAuthenticator): Authenticator based on KERI ESSR combination of signatures and encryption
            allowed (list[str]): Paths that are not protected.
        """
        self.agency = agency
        self.authn = authn
        self.essrAuthn = essrAuthn if essrAuthn else ESSRAuthenticator(agency=agency)
        self.allowed = allowed if allowed else []

    def process_request(self, req: ModifiableRequest, rep: falcon.Response):
        """Process request to ensure has a valid signature from caid, decrypting if necessary.

        Parameters:
            req (ModifiableRequest): Falcon request object
            rep (Response): Falcon response object


        """
        for path in self.allowed:
            if req.path.startswith(path):
                return

        authenticator = self.essrAuthn if req.path == "/" else self.authn

        try:
            authenticator.inbound(req)
            return
        except (kering.AuthNError, ValueError, UnicodeDecodeError):
            pass

        rep.complete = (
            True  # This short-circuits Falcon, skipping all further processing
        )
        rep.status = falcon.HTTP_401
        return

    def process_response(
        self,
        req: ModifiableRequest,
        rep: falcon.Response,
        _resource: object,
        _req_succeeded: bool,
    ):
        """Sign finalized signed-header responses with the Agent AID.

        ESSR response protection is deferred to ``ESSRResponseWrapper`` so it
        runs after Falcon has finalized the WSGI status, headers, and body.

        Parameters:
            req (ModifiableRequest): Falcon request object
            rep (Response): Falcon response object
            _resource (End): endpoint object the request was routed to
            _req_succeeded (boot): True means the request was successfully handled


        """
        if not hasattr(req.context, "agent"):
            return

        if req.context.mode == AuthMode.SIGNED_HEADERS:
            self.authn.outbound(req, rep)
