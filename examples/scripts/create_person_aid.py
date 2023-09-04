# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from time import sleep

from keri.core import coring
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def create_aid():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()
    operations = client.operations()
    oobis = client.oobis()

    res = identifiers.list()
    assert res["aids"] == []

    wits = [
        "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
        "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
        "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX"
    ]

    _, _, op = identifiers.create("multisig-sigpy", bran="0123456789abcdefghijk", wits=wits, toad="2")

    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)

    icp = coring.Serder(ked=op["response"])
    assert icp.pre == "EBcIURLpxmVwahksgrsGW6_dUw0zBhyEHYFk17eWrZfk"
    print(f"Person AID {icp.pre} created")

    identifiers.addEndRole("multisig-sigpy", eid=client.agent.pre)

    print("multisig-sigpy resolving delegator...")
    op = oobis.resolve(
        oobi="http://127.0.0.1:5642/oobi/EHpD0-CDWOdu5RJ8jHBSUkOqBZ3cXeDVHWNb_Ul89VI7/witness/BBilc4-L3tFUnfM_wJr4S4OJ"
             "anAv_VmF_dJNN6vkf2Ha",
        alias="delegator")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    print("multisig-sigpy resolving multisig-kli...")
    op = oobis.resolve(
        oobi="http://127.0.0.1:5642/oobi/EFBmwh8vdPTofoautCiEjjuA17gSlEnE3xc-xy-fGzWZ",
        alias="multisig-kli")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")

    input(f"\nPress any key after multisig-sigts is created? ")

    print("multisig-sigpy resolving multisig-sigts...")
    op = oobis.resolve(
        oobi="http://127.0.0.1:3902/oobi/ELViLL4JCh-oktYca-pmPLwkmUaeYjyPmCLxELAKZW8V/agent/EEXekkGu9IAzav6pZVJhkLnjt"
             "jM5v3AcyA-pdKUcaGei",
        alias="multisig-sigts")
    while not op["done"]:
        op = operations.get(op["name"])
        sleep(1)
    print("... done")


if __name__ == "__main__":
    create_aid()
