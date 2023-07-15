# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

import pytest
import requests
from keri import kering
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def create_agent():
    url = "http://localhost:3901"
    bran = b'9876543210abcdefghijk'
    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier)
    print(client.controller)
    assert client.controller == "EP5JMOzNfDL8WbpRiyLxrsVg7GF-HcjIOsceqeluauxj"

    evt, siger = client.ctrl.event()

    res = requests.post(url="http://localhost:3903/boot",
                        json=dict(
                            icp=evt.ked,
                            sig=siger.qb64,
                            stem=client.ctrl.stem,
                            pidx=1,
                            tier=client.ctrl.tier))

    if res.status_code != requests.codes.accepted:
        raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    client.connect(url=url, )
    assert client.agent is not None
    print(client.agent.pre)
    assert client.agent.pre == "EERMVxqeHfFo_eIvyzBXaKdT1EyobZdSs1QXuFyYLjmz"
    assert client.agent.delpre == "EP5JMOzNfDL8WbpRiyLxrsVg7GF-HcjIOsceqeluauxj"
    print("Person agent created")


if __name__ == "__main__":
    create_agent()
