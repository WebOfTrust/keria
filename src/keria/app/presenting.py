# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.presenting module

services and endpoint for ACDC credential managements
"""
import falcon
from keri.core import coring, eventing
from keri.peer import exchanging
from keri.vdr import credentialing

from keria.core import httping


def loadEnds(app):
    presentationEnd = PresentationCollectionEnd()
    app.add_route("/identifiers/{name}/credentials/{said}/presentations", presentationEnd)
    requestsEnd = PresentationRequestsCollectionEnd()
    app.add_route("/identifiers/{name}/requests", requestsEnd)


class PresentationCollectionEnd:
    """
    ReST API for admin of credential presentation requests

    """

    @staticmethod
    def on_post(req, rep, name, said):
        """  Presentation POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab
            said (str): qb64 SAID of credential to present

        ---
        summary: Send credential presentation
        description: Send a credential presentation peer to peer (exn) message to recipient
        tags:
           - Credentials
        parameters:
          - in: path
            name: alias
            schema:
              type: string
            required: true
            description: Human readable alias for the holder of credential
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    said:
                      type: string
                      required: true
                      description: qb64 SAID of credential to send
                    recipient:
                      type: string
                      required: true
                      description: qb64 AID to send credential presentation to
                    include:
                      type: boolean
                      required: true
                      default: true
                      description: flag indicating whether to stream credential alongside presentation exn
        responses:
           202:
              description:  credential presentation message sent

        """
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPBadRequest(description=f"Invalid alias {name} for credential presentation")

        body = req.get_media()

        exn = httping.getRequiredParam(body, "exn")
        sig = httping.getRequiredParam(body, 'sig')
        recipient = httping.getRequiredParam(body, 'recipient')

        serder = coring.Serder(ked=exn)
        atc = bytearray(sig.encode("utf-8"))

        creder = agent.rgy.reger.creds.get(said)
        if creder is None:
            raise falcon.HTTPNotFound(description=f"credential {said} not found")

        if recipient in agent.hby.kevers:
            recp = recipient
        else:
            recp = agent.org.find("alias", recipient)
            if len(recp) != 1:
                raise falcon.HTTPBadRequest(description=f"invalid recipient {recipient}")
            recp = recp[0]['id']

        include = body.get("include")
        if include:
            credentialing.sendCredential(agent.hby, hab=hab, reger=agent.rgy.reger, postman=agent.postman,
                                         creder=creder, recp=recp)

        agent.postman.send(src=hab.pre, dest=recp, topic="credential", serder=serder, attachment=atc)

        rep.status = falcon.HTTP_202


class PresentationRequestsCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """  Presentation Request POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab

        ---
        summary: Request credential presentation
        description: Send a credential presentation request peer to peer (exn) message to recipient
        tags:
           - Credentials
        parameters:
          - in: path
            name: alias
            schema:
              type: string
            required: true
            description: Human readable alias for the identifier to create
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    recipient:
                      type: string
                      required: true
                      description: qb64 AID to send presentation request to
                    schema:
                      type: string
                      required: true
                      description: qb64 SAID of schema for credential being requested
                    issuer:
                      type: string
                      required: false
                      description: qb64 AID of issuer of credential being requested
        responses:
           202:
              description:  credential presentation request message sent

        """
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPBadRequest(f"Invalid alias {name} for credential request")

        body = req.get_media()
        exn = httping.getRequiredParam(body, "exn")
        sig = httping.getRequiredParam(body, 'sig')
        recipient = httping.getRequiredParam(body, 'recipient')

        serder = coring.Serder(ked=exn)
        atc = bytearray(sig.encode("utf-8"))

        if recipient in agent.hby.kevers:
            recp = recipient
        else:
            recp = agent.org.find("alias", recipient)
            if len(recp) != 1:
                raise falcon.HTTPBadRequest(description=f"invalid recipient {recipient}")
            recp = recp[0]['id']

        agent.postman.send(src=hab.pre, dest=recp, topic="credential", serder=serder, attachment=atc)

        rep.status = falcon.HTTP_202
