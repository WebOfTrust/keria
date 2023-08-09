# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def list_aids():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()
    res = identifiers.list()
    for aid in res["aids"]:
        print(f"{aid['name']}: {aid['prefix']}")


if __name__ == "__main__":
    list_aids()
