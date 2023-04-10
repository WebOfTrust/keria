# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

Testing the Mark II Agent
"""
import json

import falcon
from falcon import testing
from hio.help import decking
from keri.app import habbing, configing, delegating, grouping
from keri.app.keeping import Algos
from keri.core import coring, eventing, parsing

from keria.app import agenting
from keria.core import longrunning


def test_identifier_collection_end(helpers):
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=False, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby, \
            habbing.openHby(name="p1", temp=True) as p1hby, \
            habbing.openHby(name="p2", temp=True) as p2hby:
        swain = delegating.Boatswain(hby=hby)
        counselor = grouping.Counselor(hby=hby)
        monitor = longrunning.Monitor(hby=hby, swain=swain, counselor=counselor)
        witners = decking.Deck()
        anchors = decking.Deck()
        groups = decking.Deck()
        end = agenting.IdentifierCollectionEnd(hby=hby, witners=witners, anchors=anchors, monitor=monitor,
                                               groups=groups)

        app = falcon.App()
        app.add_route("/identifiers", end)

        client = testing.TestClient(app)

        res = client.simulate_post(path="/identifiers", body=b'{}')
        assert res.status_code == 400
        assert res.json == {'title': "required field 'icp' missing from request"}

        serder, signers = helpers.incept(salt, "signify:aid", pidx=0)
        assert len(signers) == 1
        signer0 = signers[0]
        diger0 = serder.digers[0]

        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid1',
                'icp': serder.ked,
                'sigs': sigers,
                "salty": {
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low', 'temp': False}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert res.json == [{'group': {'rmids': [], 'smids': []},
                             'name': 'aid1',
                             'prefix': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                             'rand': {'nxts': [], 'prxs': []},
                             'salt': {'algo': 'salty', 'pidx': 0, 'stem': 'signify:aid', 'tier': 'low'}}
                            ]

        serder, signer = helpers.incept(salt, "signify:aid", pidx=1, count=3)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid2',
                'icp': serder.ked,
                'sigs': sigers,
                'salt': {'stem': 'signify:aid', 'pidx': 1, 'tier': 'low', 'temp': True}}
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 2
        aid = res.json[0]
        assert aid["name"] == "aid1"
        assert aid["prefix"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        ss = aid[Algos.salty]
        assert ss["pidx"] == 0

        aid = res.json[1]
        assert aid["name"] == "aid2"
        assert aid["prefix"] == "ECL8abFVW_0RTZXFhiiA4rkRobNvjTfJ6t-T8UdBRV1e"
        ss = aid[Algos.salty]
        assert ss["pidx"] == 1

        # Test with witnesses
        serder, signers = helpers.incept(salt, "signify:aid", pidx=3,
                                         wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                               "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                               "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX", ],
                                         toad="2")
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid3',
                'icp': serder.ked,
                'sigs': sigers,
                'salt': {'stem': 'signify:aid', 'pidx': 3, 'tier': 'low', 'temp': False}}

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        assert len(end.witners) == 1
        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 3
        aid = res.json[2]
        assert aid["name"] == "aid3"
        assert aid["prefix"] == serder.pre
        ss = aid[Algos.salty]
        assert ss["pidx"] == 3

        # create member habs for group AID
        p1 = p1hby.makeHab(name="p1")
        assert p1.pre == "EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of"
        p2 = p2hby.makeHab(name="p2")
        assert p2.pre == "EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR"

        agentKvy = eventing.Kevery(db=hby.db)
        psr = parsing.Parser(kvy=agentKvy)
        psr.parseOne(p1.makeOwnInception())
        psr.parseOne(p2.makeOwnInception())

        assert p1.pre in hby.kevers
        assert p2.pre in hby.kevers

        # Test Group Multisig
        keys = [signer0.verfer.qb64, p1.kever.verfers[0].qb64, p2.kever.verfers[0].qb64, ]
        ndigs = [diger0.qb64, p1.kever.digers[0].qb64, p2.kever.digers[0].qb64]

        serder = eventing.incept(keys=keys,
                                 isith="2",
                                 nsith="2",
                                 ndigs=ndigs,
                                 code=coring.MtrDex.Blake3_256,
                                 toad=0,
                                 wits=[])

        # Send in all signatures as if we are joining the inception event
        sigers = [signer0.sign(ser=serder.raw, index=0).qb64, p1.sign(ser=serder.raw, indices=[1])[0].qb64,
                  p2.sign(ser=serder.raw, indices=[2])[0].qb64]

        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            'group': {
                "smids": [
                    {'i': "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY", "s": 0},
                    {'i': p1.pre, "s": 0},
                    {'i': p2.pre, "s": 0}
                ],
                "rmids": [
                    {'i': "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY", "s": 0},
                    {'i': p1.pre, "s": 0},
                    {'i': p2.pre, "s": 0}
                ]
            }
        }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 4
        aid = res.json[3]
        assert aid["name"] == "multisig"
        assert aid["prefix"] == serder.pre
        assert aid["group"] == {'smids': [{'i': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY', 's': 0},
                                          {'i': 'EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of', 's': 0},
                                          {'i': 'EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR', 's': 0}
                                          ],
                                'rmids': [{'i': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY', 's': 0},
                                          {'i': 'EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of', 's': 0},
                                          {'i': 'EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR', 's': 0}
                                          ]
                                }


def test_keystate_ends():
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=False, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hab = hby.makeHab(name="test")

        end = agenting.KeyStateCollectionEnd(hby=hby)

        app = falcon.App()
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
