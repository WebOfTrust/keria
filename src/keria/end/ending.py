# -*- encoding: utf-8 -*-
"""
KERIA
keria.end.ending module

ReST API endpoints

"""
import falcon
from keri import kering
from keri.end import ending
from ordered_set import OrderedSet as oset


def loadEnds(app, agency, default=None):
    end = OOBIEnd(agency=agency, default=default)
    app.add_route("/oobi", end)
    app.add_route("/oobi/{aid}", end)
    app.add_route("/oobi/{aid}/{role}", end)
    app.add_route("/oobi/{aid}/{role}/{eid}", end)


class OOBIEnd:
    """ REST API for OOBI endpoints

    Attributes:
        .hby (Habery): database access

    """

    def __init__(self, agency, default=None):
        """  End point for responding to OOBIs

        Parameters:
            default (str) qb64 AID of the 'self' of the node for

        """
        self.agency = agency
        self.default = default

    def on_get(self, _, rep, aid=None, role=None, eid=None):
        """  GET endoint for OOBI resource

        Parameters:
            _: Falcon request object
            rep: Falcon response object
            aid: qb64 identifier prefix of OOBI
            role: requested role for OOBI rpy message
            eid: qb64 identifier prefix of participant in role

        """
        if aid is None:
            if self.default is None:
                rep.status = falcon.HTTP_NOT_FOUND
                rep.text = "no blind oobi for this node"
                return

            aid = self.default

        agent = self.agency.lookup(pre=aid)
        if agent is None:
            rep.status = falcon.HTTP_NOT_FOUND
            rep.text = "AID not found for this OOBI"
            return

        if aid not in agent.hby.kevers:
            rep.status = falcon.HTTP_NOT_FOUND
            return

        kever = agent.hby.kevers[aid]
        if not agent.hby.db.fullyWitnessed(kever.serder):
            rep.status = falcon.HTTP_NOT_FOUND
            return

        if kever.prefixer.qb64 in agent.hby.prefixes:  # One of our identifiers
            hab = agent.hby.habs[kever.prefixer.qb64]
        else:  # Not allowed to respond
            rep.status = falcon.HTTP_NOT_ACCEPTABLE
            return

        eids = []
        if eid:
            eids.append(eid)

        msgs = hab.replyToOobi(aid=aid, role=role, eids=eids)
        if not msgs and role is None:
            msgs = hab.replyToOobi(aid=aid, role=kering.Roles.witness, eids=eids)
            msgs.extend(hab.replay(aid))

        if msgs:
            rep.status = falcon.HTTP_200  # This is the default status
            rep.set_header(ending.OOBI_AID_HEADER, aid)
            rep.content_type = "application/json+cesr"
            rep.data = bytes(msgs)

        else:
            rep.status = falcon.HTTP_NOT_FOUND
