# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ipexing module

services and endpoint for IPEX message managements
"""

import falcon
from keri import core
from keri.app import habbing
from keri.vdr import credentialing
from keri.core import eventing, serdering
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
        """IPEX Admit POST endpoint

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
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")

        route = ked["r"]

        match route:
            case "/ipex/admit":
                op = IpexAdmitCollectionEnd.sendAdmit(agent, hab, ked, sigs)
            case _:
                raise falcon.HTTPBadRequest(
                    description=f"invalid message route {route}"
                )

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendAdmit(agent, hab, ked, sigs):
        recp = ked.get("rp") or ked.get("a", {}).get("i")
        if recp not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(
                description=f"attempt to send to unknown AID={recp}"
            )

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(
            i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d
        )

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # make a copy and parse
        agent.parser.parseOne(ims=bytearray(ims))

        # now get rid of the event so we can pass it as atc to send
        del ims[: serder.size]

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, topic="credential"))
        agent.admits.append(dict(said=ked["d"], pre=hab.pre))

        return agent.monitor.submit(
            serder.said, longrunning.OpTypes.exchange, metadata=dict(said=serder.said)
        )


class IpexGrantCollectionEnd:
    @staticmethod
    def on_post(req, rep, name):
        """IPEX Grant POST endpoint

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
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")

        route = ked["r"]

        match route:
            case "/ipex/grant":
                op = IpexGrantCollectionEnd.sendGrant(agent, hab, ked, sigs, atc)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendGrant(agent, hab, ked, sigs, atc):
        recp = ked.get("rp") or ked.get("a", {}).get("i") or None
        if recp not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(
                description=f"attempt to send to unknown AID={recp}"
            )

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(
            i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d
        )

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims = ims + atc.encode("utf-8")

        # make a copy and parse
        agent.parser.parseOne(ims=bytearray(ims))

        # now get rid of the event so we can pass it as atc to send
        del ims[: serder.size]

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, topic="credential"))
        agent.grants.append(dict(said=ked["d"], pre=hab.pre))

        return agent.monitor.submit(
            serder.said, longrunning.OpTypes.exchange, metadata=dict(said=serder.said)
        )


class IpexApplyCollectionEnd:
    @staticmethod
    def on_post(req, rep, name):
        """IPEX Apply POST endpoint

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
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")

        route = ked["r"]

        match route:
            case "/ipex/apply":
                op = IpexApplyCollectionEnd.sendApply(agent, hab, ked, sigs)
            case _:
                raise falcon.HTTPBadRequest(
                    description=f"invalid message route {route}"
                )

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendApply(agent, hab, ked, sigs):
        recp = ked.get("rp") or ked.get("a", {}).get("i") or None
        if recp not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(
                description=f"attempt to send to unknown AID={recp}"
            )

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(
            i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d
        )

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # make a copy and parse
        agent.parser.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, topic="credential"))
        return agent.monitor.submit(
            serder.said, longrunning.OpTypes.exchange, metadata=dict(said=serder.said)
        )


class IpexOfferCollectionEnd:
    @staticmethod
    def on_post(req, rep, name):
        """IPEX Offer POST endpoint

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
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")

        route = ked["r"]

        match route:
            case "/ipex/offer":
                op = IpexOfferCollectionEnd.sendOffer(agent, hab, ked, sigs, atc)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendOffer(agent, hab, ked, sigs, atc):
        recp = ked.get("rp") or ked.get("a", {}).get("i")
        if recp not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(
                description=f"attempt to send to unknown AID={recp}"
            )

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(
            i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d
        )

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims = ims + atc.encode("utf-8")

        # make a copy and parse
        agent.parser.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, topic="credential"))
        return agent.monitor.submit(
            serder.said, longrunning.OpTypes.exchange, metadata=dict(said=serder.said)
        )


class IpexAgreeCollectionEnd:
    @staticmethod
    def on_post(req, rep, name):
        """IPEX Agree POST endpoint

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
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        body = req.get_media()

        ked = httping.getRequiredParam(body, "exn")
        sigs = httping.getRequiredParam(body, "sigs")

        route = ked["r"]

        match route:
            case "/ipex/agree":
                op = IpexAgreeCollectionEnd.sendAgree(agent, hab, ked, sigs)
            case _:
                raise falcon.HTTPBadRequest(description=f"invalid route {route}")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

    @staticmethod
    def sendAgree(agent, hab, ked, sigs):
        recp = ked.get("rp") or ked.get("a", {}).get("i") or None
        if recp not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(
                description=f"attempt to send to unknown AID={recp}"
            )

        # use that data to create th Serder and Sigers for the exn
        serder = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # Now create the stream to send, need the signer seal
        kever = hab.kever
        seal = eventing.SealEvent(
            i=hab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d
        )

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)

        # make a copy and parse
        agent.parser.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, topic="credential"))
        return agent.monitor.submit(
            serder.said, longrunning.OpTypes.exchange, metadata=dict(said=serder.said)
        )


def gatherArtifacts(
    hby: habbing.Habery,
    reger: credentialing.Reger,
    creder: serdering.SerderACDC,
    recp: str,
):
    """
    Gathers a list from the local database of all dependent credential artifacts needed by the
    recipient to fully verify an ACDC including all KEL and TEL events for the issuer and issuee and
    any of their (delegators.

    Parameters:
        hby: Habery to read KELs from
        reger: Registry to read registries and ACDCs from
        creder: The credential to send
        recp: recipient

    Returns:
        A list of (Serder, attachment) tuples to send
    """
    messages = []
    issr = creder.issuer
    isse = creder.attrib["i"] if "i" in creder.attrib else None
    regk = creder.regi

    # Get issuer delegation parent KELs
    ikever = hby.db.kevers[issr]
    for msg in hby.db.cloneDelegation(ikever):
        serder = serdering.SerderKERI(raw=msg)
        atc = msg[serder.size :]
        messages.append((serder, atc))

    # get issuer KEL
    for msg in hby.db.clonePreIter(pre=issr):
        serder = serdering.SerderKERI(raw=msg)
        atc = msg[serder.size :]
        messages.append((serder, atc))

    # If sending to recipient that is no the issuee then
    # Get issuee KEL and delegation parent KELs
    if isse != recp:
        ikever = hby.db.kevers[isse]
        for msg in hby.db.cloneDelegation(ikever):
            serder = serdering.SerderKERI(raw=msg)
            atc = msg[serder.size :]
            messages.append((serder, atc))

        for msg in hby.db.clonePreIter(pre=isse):
            serder = serdering.SerderKERI(raw=msg)
            atc = msg[serder.size :]
            messages.append((serder, atc))

    # Get registry TEL
    if regk is not None:
        for msg in reger.clonePreIter(pre=regk):
            serder = serdering.SerderKERI(raw=msg)
            atc = msg[serder.size :]
            messages.append((serder, atc))

    # get ACDC iss or bis event
    for msg in reger.clonePreIter(pre=creder.said):
        serder = serdering.SerderKERI(raw=msg)
        atc = msg[serder.size :]
        messages.append((serder, atc))

    return messages
