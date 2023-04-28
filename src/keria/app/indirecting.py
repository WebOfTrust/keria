# -*- encoding: utf-8 -*-
"""
KERI
keria.app.indirecting module

simple indirect mode demo support classes
"""
import falcon
from keri.app import httping
from keri.core import eventing
from keri.core.coring import Ilks


class HttpEnd:
    """
    HTTP handler that accepts and KERI events POSTed as the body of a request with all attachments to
    the message as a CESR attachment HTTP header.  KEL Messages are processed and added to the database
    of the provided Habitat.

    This also handles `req`, `exn` and `tel` messages that respond with a KEL replay.
    """

    TimeoutQNF = 30
    TimeoutMBX = 5

    def __init__(self, agency):
        """
        Create the KEL HTTP server from the Habitat with an optional Falcon App to
        register the routes with.

        Parameters
             agency (Agency): the agency from which to load the Agent for each request

        """
        self.agency = agency

    def on_post(self, req, rep):
        """
        Handles POST for KERI event messages.

        Parameters:
              req (Request) Falcon HTTP request
              rep (Response) Falcon HTTP response

        ---
        summary:  Accept KERI events with attachment headers and parse
        description:  Accept KERI events with attachment headers and parse.
        tags:
           - Events
        requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 description: KERI event message
        responses:
           204:
              description: KEL EXN, QRY, RPY event accepted.

        """
        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        # TODO, figure out how we load the agent
        agent = self.agency.lookup("??")
        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")

        cr = httping.parseCesrHttpRequest(req=req)
        serder = eventing.Serder(ked=cr.payload, kind=eventing.Serials.json)
        msg = bytearray(serder.raw)
        msg.extend(cr.attachments.encode("utf-8"))

        agent.parser.ims.extend(msg)

        ilk = serder.ked["t"]
        if ilk in (Ilks.icp, Ilks.rot, Ilks.ixn, Ilks.dip, Ilks.drt, Ilks.exn, Ilks.rpy):
            rep.set_header('Content-Type', "application/json")
            rep.status = falcon.HTTP_204
        elif ilk in (Ilks.vcp, Ilks.vrt, Ilks.iss, Ilks.rev, Ilks.bis, Ilks.brv):
            rep.set_header('Content-Type', "application/json")
            rep.status = falcon.HTTP_204
        elif ilk in (Ilks.qry,):
            if serder.ked["r"] in ("mbx",):
                raise falcon.HTTPNotFound("no mailbox support in KERIA")
            else:
                rep.set_header('Content-Type', "application/json")
                rep.status = falcon.HTTP_204