# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ipexing module

services and endpoint for IPEX message managements
"""
import json

import falcon
from keri.app import habbing
from keri.core import coring, eventing, serdering
from keri.peer import exchanging

from keria.core import httping, longrunning


def loadEnds(app):
    admitColEnd = IpexAdmitCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/admit", admitColEnd)
    grantColEnd = IpexGrantCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/grant", grantColEnd)


class IpexAdmitCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """  Registries GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for AID

        ---
        summary: List credential issuance and revocation registies
        description: List credential issuance and revocation registies
        tags:
           - Registries
        responses:
           200:
              description:  array of current credential issuance and revocation registies

        """
        agent = req.context.agent
        # Get the hab
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"alias={name} is not a valid reference to an identifier")

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")
        rec = httping.getRequiredParam(body, "rec")

        route = ked['r']

        match route:
            case "/ipex/admit":
                op = IpexAdmitCollectionEnd.sendAdmit(agent, hab, ked, sigs, rec)
            case "/multisig/exn":
                op = IpexAdmitCollectionEnd.sendMultisigExn(agent, hab, ked, sigs, atc, rec)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid message route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendAdmit(agent, hab, ked, sigs, rec):
        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        # now get rid of the event so we can pass it as atc to send
        del ims[:serder.size]

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))
        agent.admits.append(dict(said=ked['d'], pre=hab.pre))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))

    @staticmethod
    def sendMultisigExn(agent, hab, ked, sigs, atc, rec):
        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description=f"attempt to send multisig message with non-group AID={hab.pre}")

        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        embeds = ked['e']
        admitked = embeds['exn']
        if admitked['r'] != "/ipex/admit":
            raise falcon.HTTPBadRequest(description=f"invalid route for embedded ipex admit {admitked['r']}")

        # Have to add the atc to the end... this will be Pathed signatures for embeds
        if not atc:
            raise falcon.HTTPBadRequest(description=f"attachment missing for ACDC, unable to process request.")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))

        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        grant, _ = exchanging.cloneMessage(agent.hby, admitked['p'])
        if grant is None:
            raise falcon.HTTPBadRequest(description=f"attempt to admit an invalid grant {admitked['p']}")

        embeds = grant.ked['e']
        acdc = embeds["acdc"]
        issr = acdc['i']

        serder = serdering.SerderKERI(sad=admitked)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[issr], topic="credential"))
        agent.admits.append(dict(said=admitked['d'], pre=hab.pre))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))


class IpexGrantCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """  Registries GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for AID

        ---
        summary: List credential issuance and revocation registies
        description: List credential issuance and revocation registies
        tags:
           - Registries
        responses:
           200:
              description:  array of current credential issuance and revocation registies

        """
        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"alias={name} is not a valid reference to an identifier")

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")
        rec = httping.getRequiredParam(body, "rec")

        route = ked['r']

        match route:
            case "/ipex/grant":
                op = IpexGrantCollectionEnd.sendGrant(agent, hab, ked, sigs, atc, rec)
            case "/multisig/exn":
                op = IpexGrantCollectionEnd.sendMultisigExn(agent, hab, ked, sigs, atc, rec)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendGrant(agent, hab, ked, sigs, atc, rec):
        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims = ims + atc.encode("utf-8")

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        # now get rid of the event so we can pass it as atc to send
        del ims[:serder.size]

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))
        agent.grants.append(dict(said=ked['d'], pre=hab.pre, rec=rec))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))

    @staticmethod
    def sendMultisigExn(agent, hab, ked, sigs, atc, rec):
        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description=f"attempt to send multisig message with non-group AID={hab.pre}")

        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        embeds = ked['e']
        grant = embeds['exn']
        if grant['r'] != "/ipex/grant":
            raise falcon.HTTPBadRequest(description=f"invalid route for embedded ipex grant {ked['r']}")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))
        holder = grant['a']['i']

        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        serder = serdering.SerderKERI(sad=grant)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[holder], topic="credential"))
        agent.grants.append(dict(said=grant['d'], pre=hab.pre, rec=[holder]))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))
