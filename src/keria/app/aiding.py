# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ending module

"""
import json
from urllib.parse import urlparse

import falcon
from hio.help import decking
from keri import kering
from keri.app import habbing
from keri.app.keeping import Algos
from keri.core import coring
from keri.core.coring import Ilks
from keri.db import dbing
from keri.help import ogler

from .keeping import RemoteManager
from ..core import longrunning, httping

logger = ogler.getLogger()


def loadEnds(app, hby, monitor, groups, anchors, witners):
    aidsEnd = IdentifierCollectionEnd(hby, witners=witners, groups=groups, anchors=anchors, monitor=monitor)
    app.add_route("/identifiers", aidsEnd)
    aidEnd = IdentifierResourceEnd(hby, witners=witners, anchors=anchors, monitor=monitor)
    app.add_route("/identifiers/{name}", aidEnd)

    aidOOBIsEnd = IdentifierOOBICollectionEnd(hby)
    app.add_route("/identifiers/{name}/oobis", aidOOBIsEnd)

    endRolesEnd = EndRoleCollectionEnd(hby=hby)
    app.add_route("/identifiers/{name}/endroles", endRolesEnd)

    endRoleEnd = EndRoleResourceEnd(hby=hby)
    app.add_route("/identifiers/{name}/endroles/{cid}/{role}/{eid}", endRoleEnd)


class IdentifierCollectionEnd:
    """ Resource class for creating and managing identifiers """

    def __init__(self, hby, monitor, groups, anchors, witners, rm=None):
        """

        Parameters:
            hby (Habery): Controller database and keystore environment
            monitor (Monitor): Long running process monitor
            witners (decking.Deck): cues for witness receiption
            anchors (decking.Deck): cues for delegation processing

        """
        self.hby = hby
        self.mon = monitor
        self.groups = groups
        self.anchors = anchors
        self.witners = witners
        self.rm = rm if rm is not None else RemoteManager(hby=hby)

    def on_get(self, _, rep):
        """ Identifier List GET endpoint

        Parameters:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        """
        res = []

        for pre, hab in self.hby.habs.items():
            data = info(hab, self.rm)
            res.append(data)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    def on_post(self, req, rep):
        """ Inception event POST endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """
        try:
            body = req.get_media()
            icp = httping.getRequiredParam(body, "icp")
            name = httping.getRequiredParam(body, "name")
            sigs = httping.getRequiredParam(body, "sigs")

            serder = coring.Serder(ked=icp)
            sigers = [coring.Siger(qb64=sig) for sig in sigs]
            inits = dict(pre=serder.pre)

            # client is requesting agent to join multisig group
            if "group" in body:
                inits |= loadGroupParams(self.hby, body)
                hab = self.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                try:
                    self.rm.group(**inits)
                except ValueError as e:
                    self.hby.deleteHab(name=name)
                    raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                # Generate response, either the serder or a long running operaton indicator for the type
                rep.content_type = "application/json"
                self.groups.append(dict(pre=hab.pre, sn=0, d=serder.said, smids=inits["smids"], rmids=inits["rmids"]))
                op = self.mon.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=0))
                rep.status = falcon.HTTP_202
                rep.data = op.to_json().encode("utf-8")

            else:
                # client is requesting that the Agent track the Salty parameters
                if Algos.salty in body:
                    inits |= loadSaltyParams(body)
                    hab = self.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        self.rm.salty(**inits)
                    except ValueError as e:
                        self.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                # client is storing encrypted randomly generated key material on agent
                elif "rand" in body:
                    inits |= dict(verfers=serder.verfers, digers=serder.digers)
                    inits |= loadRandyParams(body)
                    hab = self.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        self.rm.randy(**inits)
                    except ValueError as e:
                        self.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                else:
                    raise falcon.HTTPBadRequest(description="invalid request: one of group, rand or salt field required")

                # create Hab and incept the key store (if any)
                # Generate response, either the serder or a long running operaton indicator for the type
                rep.content_type = "application/json"
                if hab.kever.delegator:
                    self.anchors.append(dict(pre=hab.pre, sn=0))
                    op = self.mon.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.delegation,
                                         metadata=dict(sn=0))
                    rep.status = falcon.HTTP_202
                    rep.data = op.to_json().encode("utf-8")

                elif hab.kever.wits:
                    self.witners.append(dict(serder=serder))
                    op = self.mon.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.witness,
                                         metadata=dict(sn=0))
                    rep.status = falcon.HTTP_202
                    rep.data = op.to_json().encode("utf-8")

                else:
                    rep.status = falcon.HTTP_200
                    rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]


class IdentifierResourceEnd:
    """ Resource class for updating and deleting identifiers """

    def __init__(self, hby, monitor, witners, anchors, rm=None):
        """

        Parameters:
            hby (Habery): Controller database and keystore environment
            monitor (Monitor): Long running process monitor
            witners (decking.Deck): cues for witness receiption
            anchors (decking.Deck): cues for delegation processing

        """
        self.hby = hby
        self.rm = rm if rm is not None else RemoteManager(hby=hby)
        self.mon = monitor
        self.witners = witners
        self.anchors = anchors

    def on_get(self, _, rep, name):
        """ Identifier GET endpoint

        Parameters:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab to GET

        """
        hab = self.hby.habByName(name)
        if hab is None:
            rep.status = falcon.HTTP_400
            return

        data = info(hab, self.rm, full=True)
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(data).encode("utf-8")

    def on_put(self, req, rep, name):
        """ Identifier UPDATE endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object
            name (str): human readable name for Hab to rotate or interact

        """
        try:
            body = req.get_media()
            typ = Ilks.ixn if req.params.get("type") == "ixn" else Ilks.rot

            if typ in (Ilks.rot,):
                data = self.rotate(name, body)
            else:
                data = self.interact(name, body)

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = data

        except (kering.AuthError, ValueError) as e:
            raise falcon.HTTPBadRequest(description=e.args[0])

    def rotate(self, name, body):
        hab = self.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID with name {name} found")

        rot = body.get("rot")
        if rot is None:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'rot' missing from request")

        sigs = body.get("sigs")
        if sigs is None or len(sigs) == 0:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'sigs' missing from request")

        serder = coring.Serder(ked=rot)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        hab.rotate(serder=serder, sigers=sigers)

        if "rand" in body:
            rand = body["rand"]
            if "prxs" not in rand:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "prxs" missing from body.rand')
            prxs = rand["prxs"]

            if "nxts" not in rand:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "nxts" missing from body.rand')
            nxts = rand["nxts"]

            self.rm.update(pre=serder.pre, algo=Algos.randy, verfers=serder.verfers, digers=serder.digers,
                           prxs=prxs, nxts=nxts)

        elif "group" in body:
            group = body["group"]
            if "smids" not in group:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "smids" missing from body.group')
            smids = group["smids"]
            local = False
            for smid in smids:
                if smid['i'] in self.hby.habs:
                    local = True
                    break

            if not local:
                raise falcon.HTTPBadRequest(desctiption="No local AID in group multisig request")

            if "rmids" not in group:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "rmids" missing from body.group')
            rmids = group["rmids"]

            self.rm.update(pre=serder.pre, algo=Algos.randy, verfers=serder.verfers, digers=serder.digers,
                           smids=smids, rmids=rmids)

        if hab.kever.delegator:
            self.anchors.append(dict(alias=name, pre=hab.pre, sn=0))
            op = self.mon.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.delegation,
                                 metadata=dict(sn=hab.kever.sn))
            return op.to_json().encode("utf-8")

        if hab.kever.wits:
            self.witners.append(dict(serder=serder))
            op = self.mon.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.witness,
                                 metadata=dict(sn=hab.kever.sn))
            return op.to_json().encode("utf-8")

        return serder.raw

    def interact(self, name, body):
        hab = self.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID {name} found")

        ixn = body.get("ixn")
        if ixn is None:
            raise falcon.HTTPBadRequest(title="invalid interaction",
                                        description=f"required field 'ixn' missing from request")

        sigs = body.get("sigs")
        if sigs is None or len(sigs) == 0:
            raise falcon.HTTPBadRequest(title="invalid interaction",
                                        description=f"required field 'sigs' missing from request")

        serder = coring.Serder(ked=ixn)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        hab.interact(serder=serder, sigers=sigers)

        if hab.kever.wits:
            self.witners.append(dict(serder=serder))
            op = self.mon.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.delegation,
                                 metadata=dict(sn=hab.kever.sn))
            return op.to_json().encode("utf-8")

        return serder.raw


def info(hab, rm, full=False):
    data = dict(
        name=hab.name,
        prefix=hab.pre,
    )

    if not isinstance(hab, habbing.SignifyHab):
        raise kering.ConfigurationError("agent only allows SignifyHab instances")

    data |= rm.keyParams(hab.pre)

    if hab.accepted and full:
        kever = hab.kevers[hab.pre]
        data["transferable"] = kever.transferable
        data["state"] = kever.state().ked
        dgkey = dbing.dgKey(kever.prefixer.qb64b, kever.serder.saidb)
        wigs = hab.db.getWigs(dgkey)
        data["windexes"] = [coring.Siger(qb64b=bytes(wig)).index for wig in wigs]

    return data


class IdentifierOOBICollectionEnd:
    """
      This class represents the OOBI subresource collection endpoint for Identfiiers

    """

    def __init__(self, hby):
        """  Initialize Identifier / OOBI subresource endpoint

        Parameters:
            hby (Habery): database environment for controller AIDs

        """
        self.hby = hby

    def on_get(self, req, rep, name):
        """ Identifier GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab to GET

        """

        hab = self.hby.habByName(name)
        if not hab:
            raise falcon.HTTPNotFound(f"invalid alias {name}")

        if "role" not in req.params:
            raise falcon.HTTPBadRequest("role parameter required")

        role = req.params["role"]

        res = dict(role=role)
        if role in (kering.Roles.witness,):  # Fetch URL OOBIs for all witnesses
            oobis = []
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http)
                if not urls:
                    raise falcon.HTTPNotFound(f"unable to query witness {wit}, no http endpoint")

                up = urlparse(urls[kering.Schemes.http])
                oobis.append(f"{kering.Schemes.http}://{up.hostname}:{up.port}/oobi/{hab.pre}/witness/{wit}")
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http)
            if not urls:
                raise falcon.HTTPNotFound(f"unable to query controller {hab.pre}, no http endpoint")

            up = urlparse(urls[kering.Schemes.http])
            oobis.append(f"{kering.Schemes.http}://{up.hostname}:{up.port}/oobi/{hab.pre}/controller")
            res["oobis"] = oobis
        elif role in (kering.Roles.agent,):  # Fetch URL OOBIs for all witnesses
            roleUrls = hab.fetchRoleUrls(cid=hab.pre, role=kering.Roles.agent, scheme=kering.Schemes.http)
            aoobis = roleUrls[kering.Roles.agent]

            oobis = list()
            for agent in set(aoobis.keys()):
                murls = aoobis.naball(agent)
                for murl in murls:
                    for url in murl.naball(kering.Schemes.http):
                        up = urlparse(url)
                        oobis.append(f"{kering.Schemes.http}://{up.hostname}:{up.port}/oobi/{hab.pre}/agent/{agent}")

            res["oobis"] = oobis
        else:
            raise falcon.HTTPBadRequest(description=f"unsupport role type {role} for oobi request")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")


class EndRoleCollectionEnd:

    def __init__(self, hby):
        self.hby = hby

    def on_post(self, req, rep, name):
        """

        Args:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object
            name (str): human readable alias for AID

        """
        body = req.get_media()

        rpy = httping.getRequiredParam(body, "rpy")
        rsigs = httping.getRequiredParam(body, "sigs")

        rserder = coring.Serder(ked=rpy)
        data = rserder.ked['a']
        pre = data['cid']
        role = data['role']
        eid = data['eid']

        hab = self.hby.habByName(name)
        if hab is None:
            raise falcon.errors.HTTPNotFound(f"invalid alias {name}")

        if pre != hab.pre:
            raise falcon.errors.HTTPBadRequest(f"error trying to create end role for unknown local AID {pre}")

        rsigers = [coring.Siger(qb64=rsig) for rsig in rsigs]
        tsg = (hab.kever.prefixer, coring.Seqner(sn=hab.kever.sn), hab.kever.serder.saider, rsigers)
        self.hby.rvy.processReply(rserder, tsgs=[tsg])

        msg = hab.loadEndRole(cid=pre, role=role, eid=eid)
        if msg is None:
            raise falcon.errors.HTTPBadRequest(f"invalid end role rpy={rserder.ked}")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = rserder.raw


class EndRoleResourceEnd:

    def __init__(self, hby):
        self.hby = hby

    def on_delete(self, req, rep):
        pass


def loadSaltyParams(body):
    salt = body[Algos.salty]
    if "stem" not in salt:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "stem" missing from body.salt')
    stem = salt["stem"]

    if "pidx" not in salt:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "pidx" missing from body.salt')
    pidx = salt["pidx"]

    if "tier" not in salt:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "tier" missing from body.salt')
    tier = salt["tier"]

    dcode = httping.getRequiredParam(salt, "dcode")
    icodes = httping.getRequiredParam(salt, "icodes")
    ncodes = httping.getRequiredParam(salt, "ncodes")

    inits = dict(pidx=pidx, stem=stem, tier=tier, icodes=icodes, ncodes=ncodes, dcode=dcode)

    return inits


def loadRandyParams(body):
    rand = body[Algos.salty]
    if "prxs" not in rand:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "prxs" missing from body.rand')
    prxs = rand["prxs"]
    if "nxts" not in rand:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "nxts" missing from body.rand')
    nxts = rand["nxts"]
    inits = dict(algo=Algos.randy, prxs=prxs, nxts=nxts)
    return inits


def loadGroupParams(hby, body):
    group = body["group"]
    if "smids" not in group:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "smids" missing from body.group')
    smids = group["smids"]
    local = False
    for smid in smids:
        if smid['i'] in hby.habs:
            local = True
            break

    if not local:
        raise falcon.HTTPBadRequest(desctiption="No local AID in group multisig request")

    if "rmids" not in group:
        raise falcon.HTTPBadRequest(title="invalid inception",
                                    description=f'required field "rmids" missing from body.group')
    rmids = group["rmids"]

    inits = dict(algo=Algos.group, smids=smids, rmids=rmids)
    return inits
