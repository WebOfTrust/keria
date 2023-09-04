# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json
from pprint import pprint

from keri.core import coring
from keri.core.coring import Tiers
from keri.core.eventing import messagize, SealEvent
from keri.peer import exchanging
from signify.app.clienting import SignifyClient


def list_notifications():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()
    notificatons = client.notifications()
    groups = client.groups()
    registries = client.registries()

    res = notificatons.list()

    for note in res["notes"]:
        body = note['a']
        route = body['r']
        match route.split("/"):
            case ["", "multisig", "icp"]:
                pass
                # print(body)
                # print(f"Recv: inception request for multisig AID=BLAH")
            case ["", "multisig", "vcp"]:
                said = body['d']
                res = groups.get_request(said=said)
                msg = next(exn for exn in res if exn['exn']['d'] == said)

                sender = msg['sender']
                group = msg["groupName"]

                exn = msg['exn']
                usage = exn['a']["usage"]
                print(f"Credential registry inception request for group AID  {group}:")
                print(f"\tReceived from:  {sender}")
                print(f"\tPurpose:  \"{usage}\"")
                yes = input("Approve [Y|n]? ")

                if yes in ('', 'y', 'Y'):
                    registryName = input("Enter new local name for registry: ")
                    embeds = exn['e']
                    vcp = embeds['vcp']
                    ixn = embeds['ixn']
                    serder = coring.Serder(ked=ixn)
                    ghab = identifiers.get(group)

                    keeper = client.manager.get(aid=ghab)
                    sigs = keeper.sign(ser=serder.raw)

                    ims = messagize(serder=serder, sigers=[coring.Siger(qb64=sig) for sig in sigs])
                    embeds = dict(
                        vcp=coring.Serder(ked=vcp).raw,
                        ixn=ims
                    )

                    sender = ghab["group"]["mhab"]
                    keeper = client.manager.get(aid=sender)
                    exn, end = exchanging.exchange(route="/multisig/vcp",
                                                   payload={'gid': ghab["prefix"], 'usage': "test"},
                                                   sender=sender["prefix"], embeds=embeds)

                    esigs = keeper.sign(ser=exn.raw)
                    groups.send_request(group, exn.ked, esigs, end)

                    return registries.create_from_events(name=group, hab=ghab, registryName=registryName, vcp=vcp,
                                                         ixn=ixn, sigs=sigs)


if __name__ == "__main__":
    list_notifications()
