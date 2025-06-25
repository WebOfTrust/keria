# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.authing module

"""
import pysodium
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
from keri.end import ending
from keri.help import helping

from typing import TYPE_CHECKING, Dict, Any
if TYPE_CHECKING:
    from keria.app.agenting import Agency

CORS_HEADERS = [
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-expose-headers",
    "access-control-max-age"
]


class AuthMode(Enum):
    SIGNED_HEADERS = "SIGNED_HEADERS",
    ESSR = "ESSR"


class ModifiableRequest(falcon.Request):
    def reinit(self, env):
        super().__init__(env)


class Authenticator(ABC):
    def __init__(self, agency: 'Agency'):
        """ Abstract agent authenticator for verifying requests and preparing responses

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

    DefaultFields = ["Signify-Resource",
                     "@method",
                     "@path",
                     "Signify-Timestamp"]

    def __init__(self, agency):
        """ Create agent authenticator based on RFC-9421 signed header message signatures

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents

        Returns:
              SignedHeaderAuthenticator

        """
        super().__init__(agency)

    def inbound(self, request: ModifiableRequest):
        """ Validate that the request is correctly signed based on our version of RFC-9421

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
            raise kering.AuthNError("Unknown or invalid controller (controller KEL not resolved)")

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

            params = ';'.join(values)

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
        """ Generate and add Signature Input and Signature fields to headers of the response

        Parameters:
            request (ModifiableRequest): Falcon request object
            response (Response): Falcon response object

        """

        request.path = quote(request.path)
        agent = request.context.agent
        response.set_header('Signify-Resource', agent.agentHab.pre)
        response.set_header('Signify-Timestamp', helping.nowIso8601())

        headers = Hict(response.headers)
        header, qsig = ending.siginput("signify", request.method, request.path, headers, fields=self.DefaultFields, hab=agent.agentHab,
                                       alg="ed25519", keyid=agent.agentHab.pre)
        headers.extend(header)
        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        for key, val in headers.items():
            response.set_header(key, val)


class ESSRAuthenticator(Authenticator):
    def __init__(self, agency):
        """ Create agent authenticator for verifying requests and signing+encrypting responses using KERI ESSR

        Parameters:
            agency(Agency): KERIA agency for handling creation and management of Signify agents

        Returns:
              ESSRAuthenticator

        """
        super().__init__(agency)

    def inbound(self, request: ModifiableRequest):
        """ Validates that the wrapper request is correctly signed, and decrypts the embedded HTTP request which is
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

        if not ckever.verfers[0].verify(sig=cig.raw, ser=json.dumps(payload, separators=(",", ":")).encode("utf-8")):
            raise kering.AuthNError("Signature invalid")

        # The real HTTP request is the plaintext of the body of the wrapper to POST /
        environ = self.buildEnviron(agent.agentHab.decrypt(ser=cipher).decode("utf-8"))

        # ESSR "Encrypt Sender"
        if "HTTP_SIGNIFY_RESOURCE" not in environ or environ["HTTP_SIGNIFY_RESOURCE"] != resource:
            raise kering.AuthNError("ESSR payload missing or incorrect encrypted sender")

        request.reinit(environ)
        request.context.mode = AuthMode.ESSR
        request.context.agent = agent

    def outbound(self, request: ModifiableRequest, response: falcon.Response):
        """ Encrypt the HTTP response and place in the body of a wrapping request which contains the signature.

        Parameters:
            request (ModifiableRequest): Falcon request object
            response (Response): Falcon response object

        """
        agent = request.context.agent
        response.set_header("SIGNIFY-RESOURCE", agent.agentHab.pre)  # ESSR "Encrypt Sender"
        inner = self.serializeResponse(request.env.get("SERVER_PROTOCOL"), response).encode("utf-8")

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
        sig = agent.agentHab.sign(json.dumps(payload, separators=(",", ":")).encode("utf-8"), indexed=False)
        signage = ending.Signage(markers=dict(signify=sig[0]), indexed=False, signer=None, ordinal=None,
                                 digest=None,
                                 kind=None)
        for key, val in ending.signature([signage]).items():
            response.set_header(key, val)

    @staticmethod
    def buildEnviron(raw: str) -> Dict[str, Any]:
        """ Deserializes a HTTP request string into an environ dict that can initialize falcon request object

        Parameters:
            raw (str): The serialized HTTP request

        Returns:
            str: The serialized HTTP string

        """
        lines = raw.splitlines()

        method, url, protocol = lines[0].strip().split()
        splitUrl = urlsplit(url)
        splitHost = splitUrl.netloc.split(":")

        headers = {}
        i = 1
        while i < len(lines) and lines[i].strip() != "":
            header_line = lines[i].strip()
            header_name, header_value = header_line.split(":", 1)
            headers[header_name.strip()] = header_value.strip()
            i += 1

        body = "\n".join(lines[i + 1:]).strip()

        environ = {
            "wsgi.input": BytesIO(body.encode("utf-8")),
            "wsgi.errors": sys.stderr,
            "wsgi.url_scheme": splitUrl.scheme,
            "REQUEST_METHOD": method,
            "SERVER_NAME": splitHost[0],
            "SERVER_PORT": splitHost[1] if len(splitHost) > 1 else ("433" if splitUrl.scheme == "https" else "80"),
            "SERVER_PROTOCOL": protocol,
            "PATH_INFO": splitUrl.path,
            "QUERY_STRING": splitUrl.query,
            "CONTENT_TYPE": headers.get("content-type", ""),
            "CONTENT_LENGTH": str(len(body)) if body else "0",
        }

        for key, value in headers.items():
            key = "HTTP_" + key.replace("-", "_").upper()
            environ[key] = value

        return environ

    @staticmethod
    def serializeResponse(protocol: str, response: falcon.Response) -> str:
        """ Serializes a falcon response object into a HTTP string

        Parameters:
            protocol (str): HTTP protocol string
            response (falcon.Response): Falcon response object

        Returns:
            str: The serialized HTTP string

        """
        status_line = f"{protocol} {response.status}"
        headers = "\r\n".join([
            f"{key}: {value}" for key, value in response.headers.items()
            if key.lower() not in CORS_HEADERS
        ])

        if response.text:
            body = response.text
        elif response.data:
            body = response.data.decode("utf-8")
        else:
            body = ""

        return f"{status_line}\r\n{headers}\r\n\r\n{body}"


class AuthenticationMiddleware:
    """ Authenticate incoming signed requests and sign outbound responses (optionally encrypted) """

    def __init__(self, agency, authn: SignedHeaderAuthenticator, essrAuthn: ESSRAuthenticator = None, allowed=None):
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
        """ Process request to ensure has a valid signature from caid, decrypting if necessary.

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
        except (kering.AuthNError, ValueError):
            pass

        rep.complete = True  # This short-circuits Falcon, skipping all further processing
        rep.status = falcon.HTTP_401
        return

    def process_response(self, req: ModifiableRequest, rep: falcon.Response, _resource: object, _req_succeeded: bool):
        """  Process every falcon response by signing the response with the Agent AID and encrypting if necessary.

        Parameters:
            req (ModifiableRequest): Falcon request object
            rep (Response): Falcon response object
            _resource (End): endpoint object the request was routed to
            _req_succeeded (boot): True means the request was successfully handled


        """
        if not hasattr(req.context, "agent"):
            return

        authenticator = self.essrAuthn if req.context.mode == AuthMode.ESSR else self.authn
        authenticator.outbound(req, rep)

