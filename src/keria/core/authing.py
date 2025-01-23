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
import falcon
from keri import kering
from keri.core import coring, MtrDex
from keri.end import ending
from keri.help import helping

CORS_HEADERS = [
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-expose-headers",
    "access-control-max-age"
]


class ModifiableRequest(falcon.Request):
    def replace(self, env):
        super().__init__(env)


class Authenticator:
    def __init__(self, agency):
        """ Create Agent Authenticator for verifying requests and signing responses using ESSR

        Parameters:
            agency(Agency): habitat of Agent for signing responses

        Returns:
              Authenticator:  the configured authenticator

        """
        self.agency = agency

    @staticmethod
    def getRequiredHeader(request, header):
        headers = request.headers
        if header not in headers:
            raise ValueError(f"Missing {header} header")
        return headers[header]

    @staticmethod
    def resource(request):
        return Authenticator.getRequiredHeader(request, "SIGNIFY-RESOURCE")

    def unwrap(self, request):
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

        plaintext = agent.agentHab.decrypt(ser=cipher).decode("utf-8")
        environ = buildEnviron(plaintext)

        # ESSR "Encrypt Sender"
        if "HTTP_SIGNIFY_RESOURCE" not in environ or environ["HTTP_SIGNIFY_RESOURCE"] != resource:
            raise kering.AuthNError("ESSR payload missing or incorrect encrypted sender")

        return agent, environ

    @staticmethod
    def wrap(req, rep):
        agent = req.context.agent
        rep.set_header("SIGNIFY-RESOURCE", agent.agentHab.pre)  # ESSR "Encrypt Sender"
        inner = serializeResponse(req.env.get("SERVER_PROTOCOL"), rep).encode("utf-8")

        rep.status = 200

        for header in rep.headers.keys():
            if header.lower() in CORS_HEADERS:
                continue
            rep.delete_header(header)

        dest = Authenticator.resource(req)
        ckever = agent.agentHab.kevers[dest]
        dt = helping.nowIso8601()

        rep.set_header("SIGNIFY-RESOURCE", agent.agentHab.pre)
        rep.set_header("SIGNIFY-RECEIVER", dest)
        rep.set_header("SIGNIFY-TIMESTAMP", dt)
        rep.set_header("CONTENT-TYPE", "application/octet-stream")

        pubkey = pysodium.crypto_sign_pk_to_box_pk(ckever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(inner, pubkey)

        rep.data = raw
        rep.text = None

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
            rep.set_header(key, val)


class SignatureValidationComponent(object):
    """ Validate Signature and Signature-Input header signatures """

    def __init__(self, agency, authn: Authenticator, allowed=None):
        """

        Parameters:
            authn (Authenticater): Authenticator to validate signature headers on request
            allowed (list[str]): Paths that are not protected.
        """
        if allowed is None:
            allowed = []
        self.agency = agency
        self.authn = authn
        self.allowed = allowed

    def process_request(self, req: ModifiableRequest, resp: falcon.Response):
        """ Process request to ensure has a valid ESSR payload from caid

        Parameters:
            req (ModifiableRequest): Falcon request object
            resp (Response): Falcon response object

        """
        for path in self.allowed:
            if req.path.startswith(path):
                return

        try:
            # Decrypt embedded HTTP req and inject into Falcon req
            agent, environ = self.authn.unwrap(req)
            req.replace(environ)
            req.context.agent = agent
            return
        except (kering.AuthNError, ValueError):
            pass

        resp.complete = True  # This short-circuits Falcon, skipping all further processing
        resp.status = falcon.HTTP_401
        return

    def process_response(self, req: ModifiableRequest, rep: falcon.Response, _resource: object, _req_succeeded: bool):
        """  Process every falcon response by adding signature headers signed by the Agent AID.

        Parameters:
            req (ModifiableRequest): Falcon request object
            rep (Response): Falcon response object
            _resource (End): endpoint object the request was routed to
            _req_succeeded (bool): True means the request was successfully handled


        """
        if hasattr(req.context, "agent"):
            self.authn.wrap(req, rep)


def buildEnviron(raw: str):
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


def serializeResponse(protocol: str, response: falcon.Response):
    status_line = f"{protocol} {response.status}"
    headers = "\r\n".join([
        f"{key}: {value}" for key, value in response.headers.items()
        if key.lower() not in CORS_HEADERS
    ])

    if response.text:
        body = response.text.strip()
    elif response.data:
        body = response.data.decode("utf-8")
    else:
        body = ""

    return f"{status_line}\r\n{headers}\r\n\r\n{body}"
