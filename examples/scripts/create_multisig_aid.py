# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json
from time import sleep

from keri.app.keeping import Algos
from keri.core import eventing, coring
from keri.core.coring import Tiers
from keri.peer import exchanging
from signify.app.clienting import SignifyClient


def create_multisig_aid():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()
    operations = client.operations()
    states = client.keyStates()
    exchanges = client.exchanges()

    aid = identifiers.get("multisig-sigpy")
    sigPy = aid["state"]

    kli = states.get("EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ")
    sigTs = states.get("ELViLL4JCh-oktYca-pmPLwkmUaeYjyPmCLxELAKZW8V")

    assert len(kli) == 1
    assert len(sigTs) == 1

    states = rstates = [sigPy, kli[0], sigTs[0]]
    for state in states:
        print(json.dumps(state, indent=2))

    icp, isigs, op = identifiers.create("multisig", algo=Algos.group, mhab=aid,
                                        delpre="EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7",
                                        toad=2,
                                        wits=[
                                            "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                            "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                            "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
                                        ],
                                        isith=["1/3", "1/3", "1/3"], nsith=["1/3", "1/3", "1/3"],
                                        states=states,
                                        rstates=rstates)

    smids = ["EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk",
             "EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ",
             "ELViLL4JCh-oktYca-pmPLwkmUaeYjyPmCLxELAKZW8V"]
    recp = ["EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ",
            "ELViLL4JCh-oktYca-pmPLwkmUaeYjyPmCLxELAKZW8V"]

    embeds = dict(
        icp=eventing.messagize(serder=icp, sigers=[coring.Siger(qb64=sig) for sig in isigs])
    )

    exchanges.send("multisig-sigpy", "multisig", sender=aid, route="/multisig/icp",
                   payload=dict(gid=icp.pre, smids=smids, rmids=smids),
                   embeds=embeds, recipients=recp)

    print("waiting on multisig creation...")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    gAid = op["response"]
    print(f"group multisig created:")
    print(json.dumps(gAid, indent=2))


if __name__ == "__main__":
    create_multisig_aid()
