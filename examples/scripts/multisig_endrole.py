# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

import json
from time import sleep

from keri.app.keeping import Algos
from keri.core import coring
from keri.core.coring import Tiers
from keri.help import helping
from signify.app.clienting import SignifyClient

url = "http://localhost:3901"
bran = b'9876543210abcdefghijk'
tier = Tiers.low

def authorize_endroles():
    client = SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()
    escrows = client.escrows()
    endroles = client.endroles()

    members = identifiers.members("multisig")
    hab = identifiers.get("multisig")
    aid = hab["prefix"]

    auths = {}
    stamp = helping.nowUTC()

    for member in members['signing']:
        ends = member["ends"]
        if not ends:
            print("\tNone")

        for role in ("agent", "mailbox"):
            if role in ends:
                for k, v in ends[role].items():
                    auths[(aid, role, k)] = stamp

    rpys = escrows.getEscrowReply(route="/end/role")
    for rpy in rpys:
        serder = coring.Serder(ked=rpy)
        payload = serder.ked['a']
        keys = tuple(payload.values())
        then = helping.fromIso8601(serder.ked["dt"])
        if keys in auths and then < stamp:
            identifiers.addEndRole("multisig", role=payload["role"], eid=payload['eid'], stamp=helping.toIso8601(then))
            auths[keys] = then  # track signed role auths by timestamp signed

    print("Waiting for approvals from other members...")
    authKeys = set(auths.keys())
    while authKeys - endrole_set(endroles, "multisig"):
        rpys = escrows.getEscrowReply(route="/end/role")
        for rpy in rpys:
            serder = coring.Serder(ked=rpy)
            payload = serder.ked['a']
            keys = tuple(payload.values())
            if keys in auths:
                then = helping.fromIso8601(serder.ked["dt"])
                stamp = auths[keys]

                if stamp == then:
                    continue

                if then < stamp:
                    print(f"authing {payload} - {then}")
                    identifiers.addEndRole("multisig", role=payload["role"], eid=payload['eid'],
                                           stamp=serder.ked["dt"])
                    auths[keys] = then  # track signed role auths by timestamp signed

    print("All endpoint role authorizations approved")


def endrole_set(er, name):
    ends = er.list(name=name)
    return {(end['cid'], end['role'], end['eid']) for end in ends}


def list_endroles():
    client = SignifyClient(passcode=bran, tier=tier, url=url)

    endroles = client.endroles()
    print(endrole_set(endroles, "multisig"))


if __name__ == "__main__":
    authorize_endroles()
    # list_endroles()
