# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
from pprint import pprint

from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def get():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    identifiers = client.identifiers()

    aid = identifiers.get("multisig")
    pprint(aid)

if __name__ == "__main__":
    get()
