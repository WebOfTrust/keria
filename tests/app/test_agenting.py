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
from keri.app import habbing, configing, keeping, delegating
from keri.core import coring, eventing

from keria.app import agenting
from keria.core import longrunning


def test_identifier_collection_end():
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=False, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        swain = delegating.Boatswain(hby=hby)
        monitor = longrunning.Monitor(hby=hby, swain=swain)
        witners = decking.Deck()
        anchors = decking.Deck()
        end = agenting.IdentifierCollectionEnd(hby=hby, witners=witners, anchors=anchors, monitor=monitor)

        app = falcon.App()
        app.add_route("/identifiers", end)

        client = testing.TestClient(app)

        serder, signers = incept(salt, "signify:aid", pidx=0)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        rpy = endrole(serder.pre, "EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf")
        rsigers = [signer.sign(ser=rpy.raw, index=0).qb64 for signer in signers]

        # res = client.simulate_post(path="/identifiers", body=b'{}')
        # assert res.status_code == 400
        # assert res.json == {'title': "required field 'icp' missing from request"}

        body = {'name': 'aid1',
                'icp': serder.ked,
                'sigs': sigers,
                'rpy': rpy.ked,
                'rsigs': rsigers,
                'stem': 'signify:aid', 'pidx': 0, 'tier': 'low', 'temp': False}

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert res.json == [{'name': 'aid1',
                             'pidx': 0,
                             'prefix': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                             'stem': 'signify:aid',
                             'temp': False,
                             'tier': 'low'}]

        serder, signer = incept(salt, "signify:aid", pidx=1, count=3)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        rpy = endrole(serder.pre, "EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf")
        rsigers = [signer.sign(ser=rpy.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid2',
                'icp': serder.ked,
                'sigs': sigers,
                'rpy': rpy.ked,
                'rsigs': rsigers,
                'stem': 'signify:aid', 'pidx': 1, 'tier': 'low', 'temp': True}
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 2
        aid = res.json[0]
        assert aid["name"] == "aid1"
        assert aid["prefix"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        assert aid["pidx"] == 0

        aid = res.json[1]
        assert aid["name"] == "aid2"
        assert aid["prefix"] == "ECL8abFVW_0RTZXFhiiA4rkRobNvjTfJ6t-T8UdBRV1e"
        assert aid["pidx"] == 1

        # Test with witnesses
        serder, signers = incept(salt, "signify:aid", pidx=3,
                                 wits=["BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                                       "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
                                       "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX", ],
                                 toad="2")
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        rpy = endrole(serder.pre, "EPGaq6inGxOx-VVVEcUb_KstzJZldHJvVsHqD4IPxTWf")
        rsigers = [signer.sign(ser=rpy.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid3',
                'icp': serder.ked,
                'sigs': sigers,
                'rpy': rpy.ked,
                'rsigs': rsigers,
                'stem': 'signify:aid', 'pidx': 3, 'tier': 'low', 'temp': False}

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        assert len(end.witners) == 1
        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 3
        aid = res.json[2]
        assert aid["name"] == "aid3"
        assert aid["prefix"] == serder.pre
        assert aid["pidx"] == 3


def incept(bran, stem, pidx, count=1, sith="1", wits=None, toad="0"):
    if wits is None:
        wits = []

    salter = coring.Salter(raw=bran)
    creator = keeping.SaltyCreator(salt=salter.qb64, stem=stem, tier=coring.Tiers.low)

    signers = creator.create(pidx=pidx, ridx=0, tier=coring.Tiers.low, temp=False, count=count)
    nsigners = creator.create(pidx=pidx, ridx=1, tier=coring.Tiers.low, temp=False, count=count)

    keys = [signer.verfer.qb64 for signer in signers]
    ndigs = [coring.Diger(ser=nsigner.verfer.qb64b) for nsigner in nsigners]

    serder = eventing.incept(keys=keys,
                             isith=sith,
                             nsith=sith,
                             ndigs=[diger.qb64 for diger in ndigs],
                             code=coring.MtrDex.Blake3_256,
                             toad=toad,
                             wits=wits)

    return serder, signers


def endrole(cid, eid):
    data = dict(cid=cid, role="agent", eid=eid)
    return eventing.reply(route="/end/role/add", data=data)
