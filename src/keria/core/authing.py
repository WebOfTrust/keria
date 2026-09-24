# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.authing module

"""

import pysodium
import io
import json
import sys
from urllib.parse import urlsplit
from io import BytesIO
from enum import Enum
from urllib.parse import quote, unquote
from abc import ABC, abstractmethod
import falcon
from hio.help import Hict
from keri import kering
from keri.core import coring, MtrDex
from keri.end import ending, httpsigning
from keri.help import helping

from keria.core.httping import rawPath

from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from keria.app.agenting import Agency

CORS_HEADERS = [
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-expose-headers",
    "access-control-max-age",
]


class AuthMode(Enum):
    SIGNED_HEADERS = ("SIGNED_HEADERS",)
    ESSR = "ESSR"
    CANONICAL = "CANONICAL"  # RFC 9421 as written, KERI profile


def readBody(request: falcon.Request):
    """
    Returns the request body as bytes and resets the request so that the
    resource can read it again. The bytes are cached on request.context, so
    a second call, such as the re-verification in AgentResourceEnd.on_put,
    sees the same body even after the resource has consumed the stream.
    """
    body = getattr(request.context, "rawBody", None)
    if body is not None:
        return body
    body = request.bounded_stream.read()
    request.stream = request.env["wsgi.input"] = io.BytesIO(body)
    request._bounded_stream = None
    request.context.rawBody = body
    return body


class ModifiableRequest(falcon.Request):
    def reinit(self, env):
        super().__init__(env)


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

    def __init__(self, agency, acceptLegacy=True, policy=None, clock=None):
        """Create agent authenticator based on RFC-9421 signed header message signatures

        Two modes are verified. Canonical mode is RFC 9421 as written, per the
        KERI profile: the signature covers the method, path and query, and the
        body through Content-Digest, and responses are signed over their
        status and body and bound to the request. Legacy mode is the scheme
        Signify has used since KERIA's first release, verified exactly as
        before. The mode is chosen from the form of the Signature header, and
        a response is signed in the mode its request used.

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents
            acceptLegacy (bool): False refuses legacy-mode requests
            policy (httpsigning.Policy): canonical-mode coverage and freshness
                policy; default httpsigning.DefaultPolicy
            clock (callable): returns now in integer seconds since the epoch,
                for freshness checks; None reads the system clock

        Returns:
              SignedHeaderAuthenticator

        """
        super().__init__(agency)
        self.acceptLegacy = acceptLegacy
        self.policy = policy if policy is not None else httpsigning.DefaultPolicy
        self.clock = clock

    @staticmethod
    def isCanonical(request: falcon.Request):
        """True when the request's Signature header is in canonical form."""
        return httpsigning.peekMode(request.headers) == httpsigning.Canonical

    def inbound(self, request: ModifiableRequest):
        """Validate that the request is correctly signed, in canonical or legacy mode

        Parameters:
            request (ModifiableRequest): Falcon request object

        """
        # Only a request whose Signature header parses as legacy takes the
        # legacy path. Everything else, including an absent or unparsable
        # header, goes to the canonical verifier, which names the refusal by
        # its profile code and, with legacy mode off, refuses a legacy
        # request as malformed-signature.
        if (
            self.acceptLegacy
            and httpsigning.peekMode(request.headers) == httpsigning.Legacy
        ):
            return self.inboundLegacy(request)

        return self.inboundCanonical(request)

    def inboundCanonical(self, request: ModifiableRequest):
        """Verify a canonical-mode (RFC 9421) request and its body

        The agent is found from the keyid the request claims, then the
        signature is verified on the headers alone against the controller's
        key state as that agent holds it, before the body is read. Only then
        is the body read and checked against the covered Content-Digest. Any
        refusal raises an httpsigning.HttpSigError, a kering.AuthNError whose
        code is the KERI profile's section 9 code.

        On success request.context.verified is a completed verification
        (bodyOwed False) whose request field is what the response is bound to.

        Parameters:
            request (ModifiableRequest): Falcon request object

        """
        keyid = httpsigning.signatureKeyid(request.headers)
        agent = self.agency.get(keyid) if keyid else None
        # With no agent for the keyid there is no key state to resolve it in;
        # resolver None refuses a non-AID keyid as malformed-key and any
        # other as unknown-key.
        resolver = (
            httpsigning.keverResolver(agent.agentHab.kevers)
            if agent is not None
            else None
        )

        verified = httpsigning.verifyRequest(
            method=request.method,
            path=rawPath(request),
            query=request.query_string,
            headers=request.headers,
            body=httpsigning.Deferred,
            resolver=resolver,
            policy=self.policy,
            now=self.clock() if self.clock is not None else None,
            acceptLegacy=self.acceptLegacy,
        )

        verified = httpsigning.checkBody(verified, request.headers, readBody(request))

        request.context.verified = verified
        request.path = unquote(request.path)
        request.context.mode = AuthMode.CANONICAL
        request.context.agent = agent

    def inboundLegacy(self, request: ModifiableRequest):
        """Validate that the request is correctly signed based on our version of RFC-9421

        Parameters:
            request (ModifiableRequest): Falcon request object

        """
        self.getRequiredHeader(request, "SIGNATURE-INPUT")
        self.getRequiredHeader(request, "SIGNATURE")

        resource = self.resource(request)
        agent = self.agency.get(resource)

        if agent is None:
            raise kering.AuthNError("Unknown controller")

        # The signer is the first current key of Signify-Resource's KEL,
        # with no derivation-code or single-signer rules (KERI profile
        # section 8); a KEL the agent has not resolved is refused with
        # "Unknown or invalid controller (controller KEL not resolved)".
        verfer = httpsigning.keverResolver(agent.agentHab.kevers).legacy(resource)

        # keripy rebuilds the legacy base and verifies it exactly as KERIA
        # always has, with the same refusal messages.
        httpsigning.verifyLegacy(
            method=request.method,
            path=request.path,
            headers=request.headers,
            verfer=verfer,
        )

        request.path = unquote(request.path)
        request.context.mode = AuthMode.SIGNED_HEADERS
        request.context.agent = agent

    def outbound(self, request: ModifiableRequest, response: falcon.Response):
        """Sign the response in the mode its request used

        Parameters:
            request (ModifiableRequest): Falcon request object
            response (Response): Falcon response object

        """
        if getattr(request.context, "mode", None) == AuthMode.CANONICAL:
            return self.outboundCanonical(request, response)
        return self.outboundLegacy(request, response)

    @staticmethod
    def outboundCanonical(request: ModifiableRequest, response: falcon.Response):
        """Sign a response to a canonical-mode request (KERI profile section 3)

        The signature covers @status, the response body through
        Content-Digest, and the request's method, path, query and
        Content-Digest, each marked req. A streamed body is buffered first so
        that it can be digested, and is then sent from the buffer. The stream
        may be a file-like object or an iterable of byte chunks: KERIA's only
        streamed response is a contact image capped at 1 MB, which
        Organizer.getImg streams from a generator.

        Parameters:
            request (ModifiableRequest): Falcon request object
            response (Response): Falcon response object

        """
        if response.stream is not None:
            stream = response.stream
            if hasattr(stream, "read"):
                data = stream.read()
            else:
                data = b"".join(stream)
            if hasattr(stream, "close"):
                stream.close()
            response.stream = None
            response.data = data

        body = response.render_body() or b""
        agent = request.context.agent
        added = httpsigning.signResponse(
            status=response.status_code,
            request=request.context.verified.request,
            body=body,
            hab=agent.agentHab,
        )
        for key, val in added.items():
            response.set_header(key, val)

    def outboundLegacy(self, request: ModifiableRequest, response: falcon.Response):
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
        environ = self.buildEnviron(agent.agentHab.decrypt(ser=cipher))

        # ESSR "Encrypt Sender"
        if (
            "HTTP_SIGNIFY_RESOURCE" not in environ
            or environ["HTTP_SIGNIFY_RESOURCE"] != resource
        ):
            raise kering.AuthNError(
                "ESSR payload missing or incorrect encrypted sender"
            )

        request.reinit(environ)
        request.path = unquote(request.path)
        request.context.mode = AuthMode.ESSR
        request.context.agent = agent

    def outbound(self, request: ModifiableRequest, response: falcon.Response):
        """Encrypt the HTTP response and place in the body of a wrapping request which contains the signature.

        Parameters:
            request (ModifiableRequest): Falcon request object
            response (Response): Falcon response object

        """
        request.path = quote(request.path)
        agent = request.context.agent
        response.set_header(
            "SIGNIFY-RESOURCE", agent.agentHab.pre
        )  # ESSR "Encrypt Sender"
        inner = self.serializeResponse(request.env.get("SERVER_PROTOCOL"), response)

        response.status = 200

        for header in response.headers.keys():
            if header.lower() in CORS_HEADERS:
                continue
            response.delete_header(header)

        dest = self.resource(request)
        ckever = agent.agentHab.kevers[dest]
        dt = helping.nowIso8601()

        response.set_header("SIGNIFY-RESOURCE", agent.agentHab.pre)
        response.set_header("SIGNIFY-RECEIVER", dest)
        response.set_header("SIGNIFY-TIMESTAMP", dt)
        response.set_header("CONTENT-TYPE", "application/octet-stream")

        pubkey = pysodium.crypto_sign_pk_to_box_pk(ckever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(inner, pubkey)

        response.data = raw
        response.text = None

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
        for key, val in ending.signature([signage]).items():
            response.set_header(key, val)

    @staticmethod
    def buildEnviron(raw: bytes) -> Dict[str, Any]:
        """Deserializes a serialized HTTP request into an environ dict that can initialize falcon request object

        The head is split from the body on the first CRLFCRLF and decoded as UTF-8. The body is
        carried through as raw bytes so the tunnel is byte transparent.

        Parameters:
            raw (bytes): The serialized HTTP request

        Returns:
            dict: The WSGI environ

        """
        head, _, body = raw.partition(b"\r\n\r\n")
        lines = head.decode("utf-8").split("\r\n")

        method, url, protocol = lines[0].split()
        splitUrl = urlsplit(url)
        splitHost = splitUrl.netloc.split(":")

        headers = {}
        for line in lines[1:]:
            name, sep, value = line.partition(":")
            if not sep:
                raise ValueError(f"Invalid header line {line}")
            headers[name.strip().lower()] = value.strip()

        environ = {
            "wsgi.input": BytesIO(body),
            "wsgi.errors": sys.stderr,
            "wsgi.url_scheme": splitUrl.scheme,
            "REQUEST_METHOD": method,
            "SERVER_NAME": splitHost[0],
            "SERVER_PORT": splitHost[1]
            if len(splitHost) > 1
            else ("433" if splitUrl.scheme == "https" else "80"),
            "SERVER_PROTOCOL": protocol,
            "PATH_INFO": splitUrl.path,
            "QUERY_STRING": splitUrl.query,
            "CONTENT_TYPE": headers.get("content-type", ""),
            "CONTENT_LENGTH": str(len(body)),
        }

        for key, value in headers.items():
            key = "HTTP_" + key.replace("-", "_").upper()
            environ[key] = value

        return environ

    @staticmethod
    def serializeResponse(protocol: str, response: falcon.Response) -> bytes:
        """Serializes a falcon response object into a serialized HTTP response

        Parameters:
            protocol (str): HTTP protocol string
            response (falcon.Response): Falcon response object

        Returns:
            bytes: The serialized HTTP response

        """
        # rendering can set content-type, so it has to happen before the head is built
        body = response.render_body() or b""

        lines = [f"{protocol} {response.status}"]
        lines.extend(
            f"{key}: {value}"
            for key, value in response.headers.items()
            if key.lower() not in CORS_HEADERS
        )

        head = "\r\n".join(lines).encode("utf-8")

        return head + b"\r\n\r\n" + body


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
                # An unprotected resource may still verify a canonical
                # signature itself after reading the body (AgentResourceEnd.on_put),
                # so keep a copy of the body for it.
                if SignedHeaderAuthenticator.isCanonical(req):
                    readBody(req)
                return

        authenticator = self.essrAuthn if req.path == "/" else self.authn

        try:
            authenticator.inbound(req)
            if not self.bodyOwed(req):
                return
        except (kering.AuthNError, ValueError, UnicodeDecodeError):
            pass

        # A refused request is not signed in response
        if hasattr(req.context, "agent"):
            del req.context.agent

        rep.complete = (
            True  # This short-circuits Falcon, skipping all further processing
        )
        rep.status = falcon.HTTP_401
        return

    @staticmethod
    def bodyOwed(req: ModifiableRequest):
        """True when the request's verification is not complete because its
        body check is still owed (KERI profile section 5). Such a request must
        not reach a resource."""
        verified = getattr(req.context, "verified", None)
        return verified is not None and verified.bodyOwed

    def process_response(
        self,
        req: ModifiableRequest,
        rep: falcon.Response,
        _resource: object,
        _req_succeeded: bool,
    ):
        """Process every falcon response by signing the response with the Agent AID and encrypting if necessary.

        Parameters:
            req (ModifiableRequest): Falcon request object
            rep (Response): Falcon response object
            _resource (End): endpoint object the request was routed to
            _req_succeeded (boot): True means the request was successfully handled


        """
        if not hasattr(req.context, "agent"):
            return

        authenticator = (
            self.essrAuthn if req.context.mode == AuthMode.ESSR else self.authn
        )
        authenticator.outbound(req, rep)
