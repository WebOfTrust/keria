# -*- encoding: utf-8 -*-
"""
KERIA
keria.core.eventing module

"""

from keri import kering
from keri.core import coring
from keri.db import dbing


def cloneAid(db, pre, fn=0):
    kel = []
    if hasattr(pre, "encode"):
        pre = pre.encode("utf-8")  # convert str to bytes

    for fn, dig in db.getFelItemPreIter(pre, fn=fn):
        evt = dict()
        dgkey = dbing.dgKey(pre, dig)  # get message
        if not (raw := db.getEvt(key=dgkey)):
            raise kering.MissingEntryError("missing event for dig={}.".format(dig))

        serder = coring.Serder(raw=bytes(raw))
        evt["ked"] = serder.ked

        # add indexed signatures to attachments
        if not (sigs := db.getSigs(key=dgkey)):
            raise kering.MissingEntryError("missing sigs for dig={}.".format(dig))

        if len(sigs) != 1:
            raise kering.ValidationError("one and only one signature allowed.")

        evt["sig"] = coring.Siger(qb64b=bytes(sigs[0])).qb64

        kel.append(evt)

    return kel

