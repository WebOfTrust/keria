# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ending module

"""
import falcon.errors
from keri.core import coring

from keria.core import httping


class EndRoleCollectionEnd:

    def __init__(self, hby):
        self.hby = hby

    def on_post(self, req, rep):
        """

        Args:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object

        """
        body = req.get_media()

        rpy = httping.getRequiredParam(body, "rpy")
        rsigs = httping.getRequiredParam(body, "sigs")

        rserder = coring.Serder(ked=rpy)
        data = rserder.ked['a']
        pre = data['cid']
        role = data['role']
        eid = data['eid']

        if pre not in self.hby.habs:
            raise falcon.errors.HTTPBadRequest(f"error trying to create end role for unknown local AID {pre}")

        hab = self.hby.habs[pre]
        rsigers = [coring.Siger(qb64=rsig) for rsig in rsigs]
        tsg = (hab.kever.prefixer, coring.Seqner(sn=hab.kever.sn), hab.kever.serder.saider, rsigers)
        self.hby.rvy.processReply(rserder, tsgs=[tsg])

        msg = hab.loadEndRole(cid=pre, role=role, eid=eid)
        if msg is None:
            raise falcon.errors.HTTPBadRequest(f"invalid end role rpy={rserder.ked}")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = msg


class EndRoleResourceEnd:

    def __init__(self, hby):
        self.hby = hby

    def on_delete(self, req, rep):
        pass
