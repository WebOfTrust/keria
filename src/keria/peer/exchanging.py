# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.exchanging module

"""
import json

import falcon
from keri.core import coring, eventing
from keri.peer import exchanging

from keria.core import httping


def loadEnds(app):
    exnColEnd = ExchangeCollectionEnd()
    app.add_route("/identifiers/{name}/exchanges", exnColEnd)

    exnColEnd = ExchangeQueryCollectionEnd()
    app.add_route("/identifiers/{name}/exchanges/query", exnColEnd)

    exnResEnd = ExchangeResourceEnd()
    app.add_route("/identifiers/{name}/exchanges/{said}", exnResEnd)


class ExchangeCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """  POST endpoint for exchange message collection

        Args:
            req (Request): falcon HTTP request object
            rep (Response): falcon HTTP response object
            name (str): human readable alias for AID context

        """
        agent = req.context.agent

        body = req.get_media()

        # Get the hab
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"alias={name} is not a valid reference to an identfier")

        # Get the exn, sigs, additional attachments and recipients  from the request
        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")
        rec = httping.getRequiredParam(body, "rec")
        topic = httping.getRequiredParam(body, "tpc")

        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(f"attempt to send to unknown AID={recp}")

        # use that data to create th Serder and Sigers for the exn
        serder = coring.Serder(ked=ked)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(i=hab.pre, s=hex(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # Have to add the atc to the end... this will be Pathed signatures for embeds
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        # now get rid of the event so we can pass it as atc to send
        del ims[:serder.size]

        msg = dict(said=serder.said, pre=hab.pre, rec=rec, topic=topic)

        agent.exchanges.append(msg)

        rep.status = falcon.HTTP_202
        rep.data = json.dumps(serder.ked).encode("utf-8")


class ExchangeQueryCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """  POST endpoint for exchange message collection

        Args:
            req (Request): falcon HTTP request object
            rep (Response): falcon HTTP response object
            name (str): human readable alias for AID context

        """
        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identfier")

        try:
            body = req.get_media()
            if "filter" in body:
                filtr = body["filter"]
            else:
                filtr = {}

            if "sort" in body:
                sort = body["sort"]
            else:
                sort = None

            if "skip" in body:
                skip = body["skip"]
            else:
                skip = 0

            if "limit" in body:
                limit = body["limit"]
            else:
                limit = 25
        except falcon.HTTPError:
            filtr = {}
            sort = {}
            skip = 0
            limit = 25

        cur = agent.exnseeker.find(filtr=filtr, sort=sort, skip=skip, limit=limit)
        saids = [coring.Saider(qb64=said) for said in cur]

        exns = []
        for said in saids:
            serder, pathed = exchanging.cloneMessage(agent.hby, said.qb64)
            exns.append(dict(exn=serder.ked, pathed=pathed))

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(exns).encode("utf-8")


class ExchangeResourceEnd:
    """ Exchange message resource endpoint class """

    @staticmethod
    def on_get(req, rep, name, said):
        """GET endpoint for exchange message collection

        Args:
            req (Request): falcon HTTP request object
            rep (Response): falcon HTTP response object
            name (str): human readable alias for AID context
            said (str): qb64 SAID of exchange message to retrieve

        """
        agent = req.context.agent

        # Get the hab
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"alias={name} is not a valid reference to an identfier")

        serder, pathed = exchanging.cloneMessage(agent.hby, said)

        if serder is None:
            raise falcon.HTTPNotFound(description=f"SAID {said} does not match a verified EXN message")

        exn = dict(exn=serder.ked, pathed={k: v.decode("utf-8") for k, v in pathed.items()})
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(exn).encode("utf-8")
