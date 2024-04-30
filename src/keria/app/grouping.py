# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.grouping module

"""
import json

import falcon
from keri import core
from keri.app import habbing
from keri.core import coring, eventing, serdering
from keri.kering import SerializeError

from keria.core import httping, longrunning


def loadEnds(app):
    msrCol = MultisigRequestCollectionEnd()
    app.add_route("/identifiers/{name}/multisig/request", msrCol)
    joinCol = MultisigJoinCollectionEnd()
    app.add_route("/identifiers/{name}/multisig/join", joinCol)
    msrRes = MultisigRequestResourceEnd()
    app.add_route("/multisig/request/{said}", msrRes)


class MultisigRequestCollectionEnd:
    """ Collection endpoint class for creating mulisig exn requests from """

    @staticmethod
    def on_post(req, rep, name):
        """ POST method for multisig request collection

        Parameters:
            req (falcon.Request): HTTP request object
            rep (falcon.Response): HTTP response object
            name (str): AID of Hab to load credentials for

        """
        agent = req.context.agent

        body = req.get_media()

        # Get the hab
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"alias={name} is not a valid reference to an identifier")

        # ...and make sure we're a Group
        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description=f"hab for alias {name} is not a multisig")

        # grab all of the required parameters
        ked = httping.getRequiredParam(body, "exn")
        serder = serdering.SerderKERI(sad=ked)
        sigs = httping.getRequiredParam(body, "sigs")
        atc = httping.getRequiredParam(body, "atc")

        # create sigers from the edge signatures so we can messagize the whole thing
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        # create seal for the proper location to find the signatures
        kever = hab.mhab.kever
        seal = eventing.SealEvent(i=hab.mhab.pre, s="{:x}".format(kever.lastEst.s), d=kever.lastEst.d)

        ims = eventing.messagize(serder=serder, sigers=sigers, seal=seal)
        ims.extend(atc.encode("utf-8"))  # add the pathed attachments
        # make a copy and parse
        agent.hby.psr.parseOne(ims=bytearray(ims))
        # now get rid of the event so we can pass it as atc to send
        del ims[:serder.size]

        smids = hab.db.signingMembers(pre=hab.pre)
        smids.remove(hab.mhab.pre)

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=smids, topic='multisig'))

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(serder.ked).encode("utf-8")


class MultisigJoinCollectionEnd:
    """ Collection endpoint class for creating mulisig exn requests from """

    @staticmethod
    def on_post(req, rep, name):
        """ POST method for multisig request collection

        Parameters:
            req (falcon.Request): HTTP request object
            rep (falcon.Response): HTTP response object
            name (str): AID of Hab to load credentials for

        """
        agent = req.context.agent

        # Get the hab
        hab = agent.hby.habByName(name)
        if hab is not None:
            raise falcon.HTTPBadRequest(description=f"attempt to create identifier with an already used alias={name}")

        agent = req.context.agent
        body = req.get_media()

        # Get the rot, sigs and recipients  from the request
        rot = httping.getRequiredParam(body, "rot")
        sigs = httping.getRequiredParam(body, "sigs")

        # Get group specific values
        gid = httping.getRequiredParam(body, "gid")
        smids = httping.getRequiredParam(body, "smids")
        rmids = httping.getRequiredParam(body, "rmids")

        both = list(set(smids + (rmids or [])))
        for recp in both:  # Have to verify we already know all the recipients.
            if recp not in agent.hby.kevers:
                agent.hby.deleteHab(name=name)
                raise falcon.HTTPBadRequest(description=f"attempt to merge with unknown AID={recp}")

        sigers = [core.Siger(qb64=sig) for sig in sigs]
        verfers = [coring.Verfer(qb64=k) for k in rot['k']]
        digers = [coring.Diger(qb64=n) for n in rot['n']]

        mhab = None
        for mid in both:
            if mid in agent.hby.habs:
                mhab = agent.hby.habs[mid]
                break

        if mhab is None:
            raise falcon.HTTPBadRequest(description="Invalid multisig group rotation request,"
                                                    " signing member list must contain a local identifier'")

        hab = agent.hby.joinSignifyGroupHab(gid, name=name, mhab=mhab, smids=smids, rmids=rmids)
        try:
            hab.make(serder=serdering.SerderKERI(sad=rot), sigers=sigers)
            agent.inceptGroup(pre=gid, mpre=mhab.pre, verfers=verfers, digers=digers)
        except (ValueError, SerializeError) as e:
            agent.hby.deleteHab(name=name)
            raise falcon.HTTPBadRequest(description=f"{e.args[0]}")

        serder = serdering.SerderKERI(sad=rot)
        agent.groups.append(dict(pre=hab.pre, serder=serder, sigers=sigers, smids=smids, rmids=rmids))
        op = agent.monitor.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=serder.sn))

        rep.content_type = "application/json"
        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class MultisigRequestResourceEnd:
    """ Resource endpoint class for getting full data for a mulisig exn request from a notification """

    @staticmethod
    def on_get(req, rep, said):
        """ GET method for multisig resources

        Parameters:
            req (falcon.Request): HTTP request object
            rep (falcon.Response): HTTP response object
            said (str): qb64 SAID of EXN multisig message.

        """
        agent = req.context.agent
        exn = agent.hby.db.exns.get(keys=(said,))
        if exn is None:
            raise falcon.HTTPNotFound(description=f"no multisig request with said={said} found")

        route = exn.ked['r']
        if not route.startswith("/multisig"):
            raise falcon.HTTPBadRequest(f"invalid mutlsig conversation with said={said}")

        payload = exn.ked['a']
        match route.split("/"):
            case ["", "multisig", "icp"]:
                pass
            case ["", "multisig", "rot"]:
                pass
            case ["", "multisig", *_]:
                gid = payload["gid"]
                if gid not in agent.hby.habs:
                    raise falcon.HTTPBadRequest(f"multisig request for non-local group pre={gid}")

        esaid = exn.ked['e']['d']
        exns = agent.mux.get(esaid=esaid)

        for d in exns:
            exn = d['exn']
            serder = serdering.SerderKERI(sad=exn)

            route = serder.ked['r']
            payload = serder.ked['a']
            match route.split("/"):
                case ["", "multisig", "icp"]:
                    pass
                case ["", "multisig", "rot"]:
                    gid = payload["gid"]
                    if gid in agent.hby.habs:
                        ghab = agent.hby.habs[gid]
                        d['groupName'] = ghab.name
                        d['memberName'] = ghab.mhab.name

                case ["", "multisig", "vcp"]:
                    gid = payload["gid"]
                    ghab = agent.hby.habs[gid]
                    d['groupName'] = ghab.name
                    d['memberName'] = ghab.mhab.name

                    sender = serder.ked['i']
                    if (c := agent.org.get(sender)) is not None:
                        d['sender'] = c['alias']
                case ["", "multisig", "iss"]:
                    gid = payload["gid"]
                    ghab = agent.hby.habs[gid]
                    d['groupName'] = ghab.name
                    d['memberName'] = ghab.mhab.name

                    sender = serder.ked['i']
                    if (c := agent.org.get(sender)) is not None:
                        d['sender'] = c['alias']

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(exns).encode("utf-8")
