# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.authing module

"""
from urllib.parse import quote, unquote
import falcon
from hio.help import Hict
from keri import kering
from keri.end import ending
from keri.help import helping


class Authenticater:

    DefaultFields = ["Signify-Resource",
                     "@method",
                     "@path",
                     "Signify-Timestamp"]

    def __init__(self, agency):
        """ Create Agent Authenticator for verifying requests and signing responses

        Parameters:
            agency(Agency): habitat of Agent for signing responses

        Returns:
              Authenicator:  the configured habery

        """
        self.agency = agency

    @staticmethod
    def resource(request):
        headers = request.headers
        if "SIGNIFY-RESOURCE" not in headers:
            raise ValueError("Missing signify resource header")

        return headers["SIGNIFY-RESOURCE"]

    def verify(self, request):
        headers = request.headers
        if "SIGNATURE-INPUT" not in headers or "SIGNATURE" not in headers:
            return False

        siginput = headers["SIGNATURE-INPUT"]
        if not siginput:
            return False
        signature = headers["SIGNATURE"]
        if not signature:
            return False

        inputs = ending.desiginput(siginput.encode("utf-8"))
        inputs = [i for i in inputs if i.name == "signify"]

        if not inputs:
            return False

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

            resource = self.resource(request)
            agent = self.agency.get(resource)

            if agent is None:
                raise kering.AuthNError("unknown or invalid controller")

            if resource not in agent.agentHab.kevers:
                raise kering.AuthNError("unknown or invalid controller")

            ckever = agent.agentHab.kevers[resource]
            signages = ending.designature(signature)
            cig = signages[0].markers[inputage.name]
            if not ckever.verfers[0].verify(sig=cig.raw, ser=ser):
                raise kering.AuthNError(f"Signature for {inputage} invalid")

        return True

    def sign(self, agent, headers, method, path, fields=None):
        """ Generate and add Signature Input and Signature fields to headers

        Parameters:
            agent (Agent): The agent that is replying to the request
            headers (Hict): HTTP header to sign
            method (str): HTTP method name of request/response
            path (str): HTTP Query path of request/response
            fields (Optional[list]): Optional list of Signature Input fields to sign.

        Returns:
            headers (Hict): Modified headers with new Signature and Signature Input fields

        """

        if fields is None:
            fields = self.DefaultFields

        header, qsig = ending.siginput("signify", method, path, headers, fields=fields, hab=agent.agentHab,
                                       alg="ed25519", keyid=agent.agentHab.pre)
        headers.extend(header)
        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        return headers


class SignatureValidationComponent(object):
    """ Validate Signature and Signature-Input header signatures """

    def __init__(self, agency, authn: Authenticater, allowed=None):
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

    def process_request(self, req, resp):
        """ Process request to ensure has a valid signature from caid

        Parameters:
            req: Http request object
            resp: Http response object


        """

        for path in self.allowed:
            if req.path.startswith(path):
                return

        req.path = quote(req.path)

        try:
            # Use Authenticater to verify the signature on the request
            if self.authn.verify(req):
                req.path = unquote(req.path)
                resource = self.authn.resource(req)
                agent = self.agency.get(caid=resource)

                req.context.agent = agent
                return

        except kering.AuthNError:
            pass
        except ValueError:
            pass

        resp.complete = True  # This short-circuits Falcon, skipping all further processing
        resp.status = falcon.HTTP_401
        return

    def process_response(self, req, rep, resource, req_succeeded):
        """  Process every falcon response by adding signature headers signed by the Agent AID.

        Parameters:
            req (Request): Falcon request object
            rep (Response): Falcon response object
            resource (End): endpoint object the request was routed to
            req_succeeded (boot): True means the request was successfully handled


        """

        if hasattr(req.context, "agent"):
            req.path = quote(req.path)
            agent = req.context.agent
            rep.set_header('Signify-Resource', agent.agentHab.pre)
            rep.set_header('Signify-Timestamp', helping.nowIso8601())
            headers = self.authn.sign(agent, Hict(rep.headers), req.method, req.path)
            for key, val in headers.items():
                rep.set_header(key, val)

