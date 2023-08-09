# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""
import json
from time import sleep

from keri.app.keeping import Algos
from keri.core.coring import Tiers
from signify.app.clienting import SignifyClient


def stream_escrows():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low

    client = SignifyClient(passcode=bran, tier=tier, url=url)

    endroles = client.endroles()




    escrows = client.escrows()

    for rpy in escrows.getEscrowReplyIter(route="/end/role"):
        print(rpy)


if __name__ == "__main__":
    stream_escrows()
