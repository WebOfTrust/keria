# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ipexing module

services and endpoint for IPEX message managements
"""
import json

import falcon
from keri import core
from keri.app import habbing
from keri.core import coring, eventing, serdering
from keri.peer import exchanging

from keria.core import httping, longrunning


def loadEnds(app):
    admitColEnd = IpexAdmitCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/admit", admitColEnd)
    grantColEnd = IpexGrantCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/grant", grantColEnd)
    applyColEnd = IpexApplyCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/apply", applyColEnd)
    offerColEnd = IpexOfferCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/offer", offerColEnd)
    agreeColEnd = IpexAgreeCollectionEnd()
    app.add_route("/identifiers/{name}/ipex/agree", agreeColEnd)


class IpexAdmitCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """ IPEX Admit POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID

        ---
        summary: Accept a credential being issued or presented in response to an IPEX grant
        description: Accept a credential being issued or presented in response to an IPEX grant
        tags:
           - Registries
        responses:
           200:
              description: long running operation of IPEX admit

        """
        agent = req.context.agent
        # Get the hab
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

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
        sigers = [core.Siger(qb64=sig) for sig in sigs]

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
            raise falcon.HTTPBadRequest(description=f"attachment missing for multi-sig admit, unable to process request.")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        grant, _ = exchanging.cloneMessage(agent.hby, admitked['p'])
        if grant is None:
            raise falcon.HTTPBadRequest(description=f"attempt to admit an invalid grant {admitked['p']}")

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))

        serder = serdering.SerderKERI(sad=admitked)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[grant.ked['i']], topic="credential"))
        agent.admits.append(dict(said=admitked['d'], pre=hab.pre))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))


class IpexGrantCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """ IPEX Grant POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID

        ---
        summary: Reply to IPEX agree message or initiate an IPEX exchange with a credential issuance or presentation
        description: Reply to IPEX agree message or initiate an IPEX exchange with a credential issuance or presentation
        tags:
           - Credentials
        responses:
           200:
              description: long running operation of IPEX grant

        """
        agent = req.context.agent
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

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
        sigers = [core.Siger(qb64=sig) for sig in sigs]

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

        if not atc:
            raise falcon.HTTPBadRequest(description=f"attachment missing for multi-sig grant, unable to process request.")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))

        grantRec = grant['a']['i']
        serder = serdering.SerderKERI(sad=grant)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[grantRec], topic="credential"))
        agent.grants.append(dict(said=grant['d'], pre=hab.pre, rec=[grantRec]))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))


class IpexApplyCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """ IPEX Apply POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID

        ---
        summary: Request a credential from another party by initiating an IPEX exchange
        description: Request a credential from another party by initiating an IPEX exchange
        tags:
           - Credentials
        responses:
           200:
              description: long running operation of IPEX apply

        """
        agent = req.context.agent
        # Get the hab
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        rec = httping.getRequiredParam(body, "rec")

        route = ked['r']

        match route:
            case "/ipex/apply":
                op = IpexApplyCollectionEnd.sendApply(agent, hab, ked, sigs, rec)
            case "/multisig/exn":
                atc = httping.getRequiredParam(body, "atc")
                op = IpexApplyCollectionEnd.sendMultisigExn(agent, hab, ked, sigs, atc, rec)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid message route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendApply(agent, hab, ked, sigs, rec):
        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))
        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))

    @staticmethod
    def sendMultisigExn(agent, hab, ked, sigs, atc, rec):
        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description=f"attempt to send multisig message with non-group AID={hab.pre}")

        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        embeds = ked['e']
        applyked = embeds['exn']
        if applyked['r'] != "/ipex/apply":
            raise falcon.HTTPBadRequest(description=f"invalid route for embedded ipex apply {ked['r']}")

        if not atc:
            raise falcon.HTTPBadRequest(description=f"attachment missing for multi-sig apply, unable to process request.")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))
        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))

        applyRec = applyked['a']['i']
        serder = serdering.SerderKERI(sad=applyked)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[applyRec], topic="credential"))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))


class IpexOfferCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """ IPEX Offer POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID

        ---
        summary: Reply to IPEX apply message or initiate an IPEX exchange with an offer for a credential with certain characteristics
        description: Reply to IPEX apply message or initiate an IPEX exchange with an offer for a credential with certain characteristics
        tags:
           - Credentials
        responses:
           200:
              description: long running operation of IPEX offer

        """
        agent = req.context.agent
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")
        rec = httping.getRequiredParam(body, "rec")

        route = ked['r']

        match route:
            case "/ipex/offer":
                op = IpexOfferCollectionEnd.sendOffer(agent, hab, ked, sigs, atc, rec)
            case "/multisig/exn":
                op = IpexOfferCollectionEnd.sendMultisigExn(agent, hab, ked, sigs, atc, rec)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendOffer(agent, hab, ked, sigs, atc, rec):
        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims = ims + atc.encode("utf-8")

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))
        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))

    @staticmethod
    def sendMultisigExn(agent, hab, ked, sigs, atc, rec):
        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description=f"attempt to send multisig message with non-group AID={hab.pre}")

        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        embeds = ked['e']
        offerked = embeds['exn']
        if offerked['r'] != "/ipex/offer":
            raise falcon.HTTPBadRequest(description=f"invalid route for embedded ipex offer {ked['r']}")

        if not atc:
            raise falcon.HTTPBadRequest(description=f"attachment missing for multi-sig offer, unable to process request.")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))
        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        apply, _ = exchanging.cloneMessage(agent.hby, offerked['p'])
        if apply is None:
            raise falcon.HTTPBadRequest(description=f"attempt to offer linked to an invalid apply {offerked['p']}")

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))

        offerRec = offerked['a']['i']
        serder = serdering.SerderKERI(sad=offerked)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[offerRec], topic="credential"))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))


class IpexAgreeCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """ IPEX Agree POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID

        ---
        summary: Reply to IPEX offer message acknowledged willingness to accept offered credential
        description: Reply to IPEX offer message acknowledged willingness to accept offered credential
        tags:
           - Credentials
        responses:
           200:
              description: long running operation of IPEX agree

        """
        agent = req.context.agent
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        rec = httping.getRequiredParam(body, "rec")

        route = ked['r']

        match route:
            case "/ipex/agree":
                op = IpexAgreeCollectionEnd.sendAgree(agent, hab, ked, sigs, rec)
            case "/multisig/exn":
                atc = httping.getRequiredParam(body, "atc")
                op = IpexAgreeCollectionEnd.sendMultisigExn(agent, hab, ked, sigs, atc, rec)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendAgree(agent, hab, ked, sigs, rec):
        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))
        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))

    @staticmethod
    def sendMultisigExn(agent, hab, ked, sigs, atc, rec):
        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description=f"attempt to send multisig message with non-group AID={hab.pre}")

        for recp in rec:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f"attempt to send to unknown AID={recp}")

        embeds = ked['e']
        agreeKed = embeds['exn']
        if agreeKed['r'] != "/ipex/agree":
            raise falcon.HTTPBadRequest(description=f"invalid route for embedded ipex agree {ked['r']}")

        if not atc:
            raise falcon.HTTPBadRequest(description=f"attachment missing for multi-sig agree, unable to process request.")

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments

        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))
        exn, pathed = exchanging.cloneMessage(agent.hby, serder.said)
        if not exn:
            raise falcon.HTTPBadRequest(description=f"invalid exn request message {serder.said}")

        apply, _ = exchanging.cloneMessage(agent.hby, agreeKed['p'])
        if apply is None:
            raise falcon.HTTPBadRequest(description=f"attempt to agree linked to an invalid offer {agreeKed['p']}")

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=rec, topic='credential'))

        agreeRec = agreeKed['a']['i']
        serder = serdering.SerderKERI(sad=agreeKed)
        ims = bytearray(serder.raw) + pathed['exn']
        agent.hby.psr.parseOne(ims=ims)
        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=[agreeRec], topic="credential"))

        return agent.monitor.submit(serder.pre, longrunning.OpTypes.exchange, metadata=dict(said=serder.said))
