# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.grouping module

"""
from math import ceil

import falcon.errors
from keri.core import eventing
from keri.core.coring import Serder, Tholder, MtrDex
from keri.db import dbing

from keria.core import httping


def loadEnds(app, agentHby):
    groupsEnd = GroupEventCollectionEnd(agentHby)
    app.add_route("/groups", groupsEnd)
    groupsEventsEnd = GroupEventCollectionEnd(agentHby)
    app.add_route("/groups/events", groupsEventsEnd)


class GroupCollectionEnd:

    def __init__(self, hby):
        self.hby = hby
        pass


class MissingEventError(Exception):
    pass


class GroupEventCollectionEnd:

    def __init__(self, hby):
        self.hby = hby
        pass

    def on_post(self, req, rep):
        """

        Parameters:
            req (Request):  falcon HTTP request object
            rep (Response): falcon HTTP response object

        """
        body = req.get_media()

        # Get requirement parameters used to generate keys and ndigs
        smids = httping.getRequiredParam(body, "smids")
        nmids = httping.getRequiredParam(body, "rmids")

        # Build up the rest of the arguments to incept/delcept that can be defaulted
        kwargs = dict()
        kwargs["code"] = body.get("code") or MtrDex.Blake3_256
        kwargs["toad"] = body.get("toad") or "0"
        kwargs["wits"] = body.get("wits") or []
        kwargs["data"] = body.get("data") or None

        if (delpre := body.get("delpre")) is not None:
            kwargs["delpre"] = delpre

        if (isith := body.get("isith")) is None:  # compute default
            isith = f"{max(1, ceil(len(smids) / 2)):x}"
        if (nsith := body.get("nsith")) is None:  # compute default
            nsith = f"{max(0, ceil(len(nmids) / 2)):x}"
        kwargs["isith"] = Tholder(sith=isith).sith  # current signing threshold
        kwargs["nsith"] = Tholder(sith=nsith).sith  # next signing threshold

        cnfg = []
        if body.get("estOnly"):
            cnfg.append(eventing.TraitCodex.EstOnly)
        if body.get("DnD"):
            cnfg.append(eventing.TraitCodex.DoNotDelegate)

        kwargs["cnfg"] = cnfg

        try:
            keys = extractSigningKeys(self.hby, smids, ssns)
            ndigs = extractNextDigests(self.hby, nmids, nsns)
        except MissingEventError as e:
            # TODO: cue and return long running op
            return

        serder = event(keys, ndigs, **kwargs)
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = serder.raw


def extractNextDigests(hby, nmids, nsns):
    """ Generate ndigs from Kevers of rmids and nsns """
    ndigs = [None] * len(nmids)
    for idx, nmid in enumerate(nmids):
        if nmid not in hby.kevers:
            raise falcon.HTTPNotFound(description=f"Proposed rotation member {nmid} not found")

        if idx > len(nsns):
            raise falcon.HTTPBadRequest(description="Not enough sequence numbers provided for rotation members")

        sn = nsns[idx]
        kever = hby.kevers[nmid]
        if sn > kever.sn:
            raise MissingEventError(kever.pre, sn)

        dig = hby.db.getKeLast(dbing.snKey(nmid, sn))
        raw = hby.db.getEvt(dbing.dgKey(nmid, dig))
        serder = Serder(raw=bytes(raw))
        if not serder.est:
            raise falcon.HTTPBadRequest(description=f"invalid non-establishment event {sn} for rotation"
                                                    f"member: {nmid}")

        ndigs[idx] = serder.digers[0].qb64
    return ndigs


def extractSigningKeys(hby, smids, ssns):
    """ Generate keys from Kevers of smids and sns """
    keys = [None] * len(smids)
    for idx, smid in enumerate(smids):
        if smid not in hby.kevers:
            raise falcon.HTTPNotFound(description=f"Proposed signing member {smid} not found")

        if idx > len(ssns):
            raise falcon.HTTPBadRequest(description="Not enough sequence numbers provided for signing members")

        sn = ssns[idx]
        kever = hby.kevers[smid]
        if sn > kever.sn:
            raise MissingEventError(kever.pre, sn)

        dig = hby.db.getKeLast(dbing.snKey(smid, sn))
        raw = hby.db.getEvt(dbing.dgKey(smid, dig))
        serder = Serder(raw=bytes(raw))
        if not serder.est:
            raise falcon.HTTPBadRequest(description=f"invalid non-establishment event {sn} for "
                                                    f"signing member: {smid}")

        keys[idx] = serder.verfers[0].qb64

    return keys


def event(keys, ndigs, **kwargs):
    if "delpre" in kwargs:
        return eventing.delcept(keys=keys,
                                ndigs=ndigs,
                                **kwargs)
    else:
        return eventing.incept(keys=keys,
                               ndigs=ndigs,
                               **kwargs)
