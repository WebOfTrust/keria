# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

Testing the Mark II Agent
"""
import json
import os
from builtins import isinstance

import falcon
from falcon import testing
from keri.app import habbing, configing
from keri.app.keeping import Algos
from keri.core import coring, eventing, parsing
from keri.core.coring import MtrDex
from keri.peer import exchanging

from keria.app import aiding


def test_load_ends(helpers):
    caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)
    with helpers.openKeria(caid=caid, salter=salter, cf=cf, temp=True) as (agency, agent, app, client):
        aiding.loadEnds(app=app, agency=agency)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/agent/AEID")
        assert isinstance(end, aiding.AgentResourceEnd)
        (end, *_) = app._router.find("/identifiers")
        assert isinstance(end, aiding.IdentifierCollectionEnd)
        (end, *_) = app._router.find("/identifiers/AID")
        assert isinstance(end, aiding.IdentifierResourceEnd)
        (end, *_) = app._router.find("/identifiers/NAME/oobis")
        assert isinstance(end, aiding.IdentifierOOBICollectionEnd)
        (end, *_) = app._router.find("/identifiers/NAME/endroles")
        assert isinstance(end, aiding.EndRoleCollectionEnd)
        (end, *_) = app._router.find("/identifiers/NAME/endroles/CID/witness/EID")
        assert isinstance(end, aiding.EndRoleResourceEnd)
        (end, *_) = app._router.find("/challenges")
        assert isinstance(end, aiding.ChallengeCollectionEnd)
        (end, *_) = app._router.find("/challenges/NAME")
        assert isinstance(end, aiding.ChallengeResourceEnd)
        (end, *_) = app._router.find("/contacts")
        assert isinstance(end, aiding.ContactCollectionEnd)
        (end, *_) = app._router.find("/contacts/PREFIX")
        assert isinstance(end, aiding.ContactResourceEnd)
        (end, *_) = app._router.find("/contacts/PREFIX/img")
        assert isinstance(end, aiding.ContactImageResourceEnd)


def test_identifier_collection_end(helpers):
    caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)

    with helpers.openKeria(caid, salter, temp=True, cf=cf) as (agency, agent, app, client), \
            habbing.openHby(name="p1", temp=True) as p1hby, \
            habbing.openHby(name="p2", temp=True) as p2hby:

        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)

        client = testing.TestClient(app)

        res = client.simulate_post(path="/identifiers", body=b'{}')
        assert res.status_code == 400
        assert res.json == {'description': "required field 'icp' missing from request",
                            'title': '400 Bad Request'}

        serder, signers = helpers.incept(salt, "signify:aid", pidx=0)
        assert len(signers) == 1
        signer0 = signers[0]
        diger0 = serder.digers[0]

        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid1',
                'icp': serder.ked,
                'sigs': sigers,
                "salty": {
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low',
                    'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert res.json == [{'name': 'aid1',
                             'prefix': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                             'salty': {'dcode': 'E',
                                       'icodes': ['A'],
                                       'kidx': 0,
                                       'ncodes': ['A'],
                                       'pidx': 0,
                                       'stem': 'signify:aid',
                                       'tier': 'low',
                                       'transferable': False}}]

        serder, signer = helpers.incept(salt, "signify:aid", pidx=1, count=3)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid2',
                'icp': serder.ked,
                'sigs': sigers,
                'salty': {'stem': 'signify:aid', 'pidx': 1, 'tier': 'low',
                          'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}}
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
                'salty': {'stem': 'signify:aid', 'pidx': 3, 'tier': 'low',
                          'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}}

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        assert len(agent.witners) == 1
        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 3
        aid = res.json[2]
        assert aid["name"] == "aid3"
        assert aid["prefix"] == serder.pre
        ss = aid[Algos.salty]
        assert ss["pidx"] == 3

        res = client.simulate_get(path=f"/identifiers/aid1")
        mhab = res.json
        agent0 = mhab["state"]

        # create member habs for group AID
        p1 = p1hby.makeHab(name="p1")
        assert p1.pre == "EBPtjiAY9ITdvScWFGeeCu3Pf6_CFFr57siQqffVt9Of"
        p2 = p2hby.makeHab(name="p2")
        assert p2.pre == "EMYBtOuBKVdp3KdW_QM__pi-UAWfrewlDyiqGcbIbopR"

        agentKvy = eventing.Kevery(db=agent.hby.db)
        psr = parsing.Parser(kvy=agentKvy)
        psr.parseOne(p1.makeOwnInception())
        psr.parseOne(p2.makeOwnInception())

        assert p1.pre in agent.hby.kevers
        assert p2.pre in agent.hby.kevers

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
        states = nstates = [agent0, p1.kever.state().ked, p2.kever.state().ked]
        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": mhab,
                "keys": keys,
                "ndigs": ndigs
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
        assert aid["group"] == {'keys': ['DDNGgXzEO4LD8G1z1uD7eIDF2pDj6Y7hVx-nqhYZmU_8',
                                         'DAOF6DRwWDphP8F2r87uxTS9xwIehonmTBE1agJrPklA',
                                         'DPZ-k6HXUhiS5dPy8awuitFpwojGOQJ6DMZiatPjhXKC'],
                                'mhab': {'name': 'aid1',
                                         'prefix': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                                         'salty': {'dcode': 'E',
                                                   'icodes': ['A'],
                                                   'kidx': 0,
                                                   'ncodes': ['A'],
                                                   'pidx': 0,
                                                   'stem': 'signify:aid',
                                                   'tier': 'low',
                                                   'transferable': False}},
                                'ndigs': ['EHj7rmVHVkQKqnfeer068PiYvYm-WFSTVZZpFGsClfT-',
                                          'ECTS-VsMzox2NoMaLIei9Gb6361Z3u0fFFWmjEjEeD64',
                                          'ED7Jk3MscDy8IHtb2k1k6cs0Oe5rEb3_8XKD1Ut_gCo8']}


def test_challenge_ends(helpers):
    caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)
    with helpers.openKeria(caid, salter, temp=True, cf=cf) as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)

        chaEnd = aiding.ChallengeCollectionEnd()
        app.add_route("/challenges", chaEnd)
        chaResEnd = aiding.ChallengeResourceEnd()
        app.add_route("/challenges/{name}", chaResEnd)

        client = testing.TestClient(app)

        result = client.simulate_get(path="/challenges?strength=256")
        assert result.status == falcon.HTTP_200
        assert "words" in result.json
        words = result.json["words"]
        assert len(words) == 24

        result = client.simulate_get(path="/challenges")
        assert result.status == falcon.HTTP_200
        assert "words" in result.json
        words = result.json["words"]
        assert len(words) == 12

        data = dict()
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/challenges/joe", body=b)
        assert result.status == falcon.HTTP_400  # Bad allias
        result = client.simulate_post(path="/challenges/pal", body=b)
        assert result.status == falcon.HTTP_400  # Missing words

        # Create an AID to test against
        aid = helpers.createAid(client, "pal", salt)

        payload = dict(i=aid['i'], words=words)
        exn = exchanging.exchange(route="/challenge/response", payload=payload)
        ims = agent.agentHab.endorse(serder=exn, last=True, pipelined=False)
        del ims[:exn.size]

        data["exn"] = exn.ked
        data["sig"] = ims.decode("utf-8")
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/challenges/pal", body=b)
        assert result.status == falcon.HTTP_400  # Missing recipient

        data["recipient"] = "Eo6MekLECO_ZprzHwfi7wG2ubOt2DWKZQcMZvTbenBNU"
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/challenges/pal", body=b)
        assert result.status == falcon.HTTP_202

        data = dict()
        data["aid"] = "Eo6MekLECO_ZprzHwfi7wG2ubOt2DWKZQcMZvTbenBNU"
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_put(path="/challenges/henk", body=b)
        assert result.status == falcon.HTTP_400  # Missing recipient

        b = json.dumps(data).encode("utf-8")
        result = client.simulate_put(path="/challenges/pal", body=b)
        assert result.status == falcon.HTTP_400  # Missing said

        data["said"] = exn.said
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_put(path="/challenges/pal", body=b)
        assert result.status == falcon.HTTP_202


def test_contact_ends(helpers):
    caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)
    with helpers.openKeria(caid=caid, salter=salter, cf=cf, temp=True) as (agency, agent, app, client), \
            habbing.openHby(name="ken", salt=coring.Salter(raw=b'0123456789ghijkl').qb64) as kenHby:

        # Register the identifier endpoint so we can create an AID for the test
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        aid = helpers.createAid(client, "pal", salt)
        palPre = aid["i"]

        msgs = bytearray()
        aids = []
        for i in range(5):
            hab = kenHby.makeHab(name=f"ken{i}", icount=1, ncount=1, wits=[])
            aids.append(hab.pre)
            msgs.extend(hab.makeOwnInception())

        hab = kenHby.makeHab(name="bad", icount=1, ncount=1, wits=[])
        msgs.extend(hab.makeOwnInception())
        parsing.Parser().parse(ims=msgs, kvy=agent.kvy)

        for aid in aids:
            assert aid in agent.hby.kevers

        contactColEnd = aiding.ContactCollectionEnd()
        app.add_route("/contacts", contactColEnd)
        contactResEnd = aiding.ContactResourceEnd()
        app.add_route("/contacts/{prefix}", contactResEnd)
        contactImgEnd = aiding.ContactImageResourceEnd()
        app.add_route("/contacts/{prefix}/img", contactImgEnd)

        client = testing.TestClient(app)

        response = client.simulate_get("/contacts")
        assert response.status == falcon.HTTP_200
        assert response.json == []

        data = dict(
            name="test"
        )
        b = json.dumps(data).encode("utf-8")
        # POST to an identifier that is not in the Kever
        response = client.simulate_post(f"/contacts/E8AKUcbZyik8EdkOwXgnyAxO5mSIPJWGZ_o7zMhnNnjo/pal", body=b)
        assert response.status == falcon.HTTP_404

        # POST to a local identifier
        response = client.simulate_post(f"/contacts/{palPre}", body=b)
        assert response.status == falcon.HTTP_400

        for i in range(5):
            data = dict(
                id=aid[i],
                first=f"Ken{i}",
                last=f"Burns{i}",
                company="GLEIF"
            )
            b = json.dumps(data).encode("utf-8")
            # POST to an identifier that is not in the Kever
            response = client.simulate_post(f"/contacts/{aids[i]}", body=b)
            assert response.status == falcon.HTTP_200

        response = client.simulate_get(f"/contacts/E8AKUcbZyik8EdkOwXgnyAxO5mSIPJWGZ_o7zMhnNnjo")
        assert response.status == falcon.HTTP_404

        response = client.simulate_get(f"/contacts/{hab.pre}")
        assert response.status == falcon.HTTP_404

        response = client.simulate_get(f"/contacts/{aids[3]}")
        assert response.status == falcon.HTTP_200
        assert response.json == {'company': 'GLEIF',
                                 'first': 'Ken3',
                                 'id': 'EAjKmvW6flpWJfdYYZ2Lu4pllPWKFjCBz0dcX-S86Nvg',
                                 'last': 'Burns3'}

        response = client.simulate_get(f"/contacts")
        assert response.status == falcon.HTTP_200
        assert len(response.json) == 5
        data = {d["id"]: d for d in response.json}
        for aid in aids:
            assert aid in data

        data = dict(id=hab.pre, company="ProSapien")
        b = json.dumps(data).encode("utf-8")

        response = client.simulate_put(f"/contacts/E8AKUcbZyik8EdkOwXgnyAxO5mSIPJWGZ_o7zMhnNnjo", body=b)
        assert response.status == falcon.HTTP_404

        response = client.simulate_put(f"/contacts/{palPre}", body=b)
        assert response.status == falcon.HTTP_400

        response = client.simulate_put(f"/contacts/{aids[2]}", body=b)
        assert response.status == falcon.HTTP_200
        assert response.json == {'company': 'ProSapien',
                                 'first': 'Ken2',
                                 'id': 'ELTQ3tF3n7QS8LDpKMdJyCMhVyMdvNPTiisnqW5ZQP3C',
                                 'last': 'Burns2'}
        response = client.simulate_put(f"/contacts/{aids[4]}", body=b)
        assert response.status == falcon.HTTP_200
        assert response.json == {'company': 'ProSapien',
                                 'first': 'Ken4',
                                 'id': 'EGwcSt3uvK5-oHI7hVU7dKMvWt0vRfMW2demzBBMDnBG',
                                 'last': 'Burns4'}

        response = client.simulate_get("/contacts", query_string="group=company")
        assert response.status == falcon.HTTP_200
        assert len(response.json) == 2

        gleif = response.json["GLEIF"]
        data = {d["id"]: d for d in gleif}
        assert aids[0] in data
        assert aids[1] in data
        assert aids[3] in data

        pros = response.json["ProSapien"]
        data = {d["id"]: d for d in pros}
        assert aids[2] in data
        assert aids[4] in data

        # Begins with search on company name
        response = client.simulate_get("/contacts", query_string="group=company&filter_value=Pro")
        assert response.status == falcon.HTTP_200
        assert len(response.json) == 1

        pros = response.json["ProSapien"]
        data = {d["id"]: d for d in pros}
        assert aids[2] in data
        assert aids[4] in data

        response = client.simulate_get("/contacts", query_string="filter_field=last")
        assert response.status == falcon.HTTP_400

        response = client.simulate_get("/contacts", query_string="filter_field=last&filter_value=Burns3")
        assert response.status == falcon.HTTP_200
        assert response.json == [{'challenges': [],
                                  'company': 'GLEIF',
                                  'first': 'Ken3',
                                  'id': 'EAjKmvW6flpWJfdYYZ2Lu4pllPWKFjCBz0dcX-S86Nvg',
                                  'last': 'Burns3',
                                  'wellKnowns': []}]

        # Begins with search on last name
        response = client.simulate_get("/contacts",
                                       query_string="filter_field=last&filter_value=Burns")
        assert response.status == falcon.HTTP_200
        assert response.json == [{'challenges': [],
                                  'company': 'GLEIF',
                                  'first': 'Ken3',
                                  'id': 'EAjKmvW6flpWJfdYYZ2Lu4pllPWKFjCBz0dcX-S86Nvg',
                                  'last': 'Burns3',
                                  'wellKnowns': []},
                                 {'challenges': [],
                                  'company': 'GLEIF',
                                  'first': 'Ken1',
                                  'id': 'EER-n23rDM2RQB8Kw4KRrm8SFpoid4Jnelhauo6KxQpz',
                                  'last': 'Burns1',
                                  'wellKnowns': []},
                                 {'challenges': [],
                                  'company': 'ProSapien',
                                  'first': 'Ken4',
                                  'id': 'EGwcSt3uvK5-oHI7hVU7dKMvWt0vRfMW2demzBBMDnBG',
                                  'last': 'Burns4',
                                  'wellKnowns': []},
                                 {'challenges': [],
                                  'company': 'ProSapien',
                                  'first': 'Ken2',
                                  'id': 'ELTQ3tF3n7QS8LDpKMdJyCMhVyMdvNPTiisnqW5ZQP3C',
                                  'last': 'Burns2',
                                  'wellKnowns': []},
                                 {'challenges': [],
                                  'company': 'GLEIF',
                                  'first': 'Ken0',
                                  'id': 'EPo8Wy1xpTa6ri25M4IlmWBBzs5y8v4Qn3Z8xP4kEjcK',
                                  'last': 'Burns0',
                                  'wellKnowns': []}]

        response = client.simulate_delete(f"/contacts/E8AKUcbZyik8EdkOwXgnyAxO5mSIPJWGZ_o7zMhnNnjo")
        assert response.status == falcon.HTTP_404

        response = client.simulate_delete(f"/contacts/{aids[3]}")
        assert response.status == falcon.HTTP_202

        response = client.simulate_get("/contacts", query_string="filter_field=last&filter_value=Burns3")
        assert response.status == falcon.HTTP_200
        assert response.json == []

        data = bytearray(os.urandom(50))
        headers = {"Content-Type": "image/png", "Content-Length": "50"}
        response = client.simulate_post(f"/contacts/E8AKUcbZyik8EdkOwXgnyAxO5mSIPJWGZ_o7zMhnNnjo/img", body=data,
                                        headers=headers)
        assert response.status == falcon.HTTP_404

        data = bytearray(os.urandom(1000001))
        headers = {"Content-Type": "image/png", "Content-Length": "1000001"}
        response = client.simulate_post(f"/contacts/{aids[0]}/img", body=data, headers=headers)
        assert response.status == falcon.HTTP_400

        data = bytearray(os.urandom(10000))
        headers = {"Content-Type": "image/png", "Content-Length": "10000"}
        response = client.simulate_post(f"/contacts/{aids[0]}/img", body=data, headers=headers)
        assert response.status == falcon.HTTP_202

        response = client.simulate_get(f"/contacts/E8AKUcbZyik8EdkOwXgnyAxO5mSIPJWGZ_o7zMhnNnjo/img")
        assert response.status == falcon.HTTP_404

        response = client.simulate_get(f"/contacts/{aids[2]}/img")
        assert response.status == falcon.HTTP_404

        response = client.simulate_get(f"/contacts/{aids[0]}/img")
        assert response.status == falcon.HTTP_200
        assert response.content == data
        headers = response.headers
        assert headers["Content-Type"] == "image/png"
        assert headers["Content-Length"] == "10000"
