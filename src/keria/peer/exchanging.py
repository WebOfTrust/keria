# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.exchanging module

"""
import json

import falcon
from keri.core import coring, eventing

from keria.core import httping


def loadEnds(app):
    exnColEnd = ExchangeCollectionEnd()
    app.add_route("/identifiers/{name}/exchanges", exnColEnd)


class ExchangeCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """ POST endpoint for exchange message collection """
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

        for recp in rec:  # now let's send it off the all the recipients
            agent.postman.send(hab=agent.agentHab,
                               dest=recp,
                               topic=topic,
                               serder=serder,
                               attachment=ims)

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(serder.ked).encode("utf-8")


