# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

Testing the Mark II Agent
"""

import falcon
from falcon import testing
from hio.base import doing
from hio.help import decking
from keri.app import habbing, configing
from keri.app.agenting import Receiptor
from keri.core import coring
from keri.vdr import credentialing

from keria.app import agenting


def test_witnesser(helpers):
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        witners = decking.Deck()
        receiptor = Receiptor(hby=hby)
        wr = agenting.Witnesser(receiptor=receiptor, witners=witners)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        # doist.do(doers=doers)
        deeds = doist.enter(doers=[wr])
        doist.recur(deeds)


def test_keystate_ends(helpers):
    caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=False, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hab = hby.makeHab(name="test")
        agency = agenting.Agency(name="agency", base=None, bran=None, temp=True)
        agentHab = hby.makeHab(caid, ns="agent", transferable=True, data=[caid])

        rgy = credentialing.Regery(hby=hby, name=agentHab.name, base=hby.base)
        agent = agenting.Agent(hby=hby, rgy=rgy, agentHab=agentHab, agency=agency, caid=caid)

        end = agenting.KeyStateCollectionEnd()

        app = falcon.App()
        app.add_middleware(helpers.middleware(agent))
        app.add_route("/states", end)

        client = testing.TestClient(app)

        res = client.simulate_get(f"/states?pre={hab.pre}")
        states = res.json
        assert len(states) == 1

        state = states[0]
        assert state['i'] == hab.pre
        assert state['d'] == "EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3"
        assert state['et'] == 'icp'
        assert state['k'] == ['DGmIfLmgErg4zFHfPwaDckLNxsLqc5iS_P0QbLjbWR0I']
        assert state['n'] == ['EJhRr10e5p7LVB6JwLDIcgqsISktnfe5m60O_I2zZO6N']
        assert state['ee'] == {'ba': [],
                               'br': [],
                               'd': 'EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3',
                               's': '0'}
