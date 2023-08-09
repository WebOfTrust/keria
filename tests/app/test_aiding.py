# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

Testing the Mark II Agent
"""
import json
import os
from builtins import isinstance
from dataclasses import asdict

import falcon
from falcon import testing
from keri import kering
from keri.app import habbing, keeping
from keri.app.keeping import Algos
from keri.core import coring, eventing, parsing
from keri.core.coring import MtrDex
from keri.db.basing import LocationRecord
from keri.peer import exchanging

from keria.app import aiding, agenting
from keria.app.aiding import IdentifierOOBICollectionEnd, RpyEscrowCollectionEnd


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        aiding.loadEnds(app=app, agency=agency, authn=None)
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
        (end, *_) = app._router.find("/identifiers/NAME/endroles/witness/EID")
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


def test_endrole_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        idResEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", idResEnd)
        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)
        app.add_route("/endroles/{aid}", endRolesEnd)
        app.add_route("/endroles/{aid}/{role}", endRolesEnd)

        # Bad route to test error condition
        app.add_route("/endroles", endRolesEnd)

        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "user1", salt)
        aid = op["response"]
        recp = aid['i']
        assert recp == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        rpy = helpers.endrole(recp, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)

        res = client.simulate_post(path=f"/identifiers/user1/endroles", json=body)
        op = res.json
        ked = op["response"]
        serder = coring.Serder(ked=ked)
        assert serder.raw == rpy.raw

        keys = (recp, 'agent', agent.agentHab.pre)
        end = agent.hby.db.ends.get(keys=keys)
        assert end is not None
        assert end.allowed is True

        # Test GET method
        # Must be valid aid alias
        res = client.simulate_get(path=f"/identifiers/bad/endroles")
        assert res.status_code == 404

        # Get endrols
        res = client.simulate_get(path=f"/identifiers/user1/endroles")
        assert res.status_code == 200

        ends = res.json
        assert len(ends) == 1
        assert ends[0] == {'cid': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                           'role': 'agent',
                           'eid': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9'}

        # Test access with AID
        res = client.simulate_get(path="/endroles")
        assert res.status_code == 400

        res = client.simulate_get(path="/endroles/EXXXVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY")
        assert res.status_code == 200
        assert len(res.json) == 0

        res = client.simulate_get(path="/endroles/EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert ends[0] == {'cid': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                           'role': 'agent',
                           'eid': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9'}

        res = client.simulate_get(path="/endroles/EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY/agent")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert ends[0] == {'cid': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                           'role': 'agent',
                           'eid': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9'}








def test_agent_resource(helpers, mockHelpingNowUTC):
    with helpers.openKeria() as (agency, agent, app, client):
        agentEnd = aiding.AgentResourceEnd(agency=agency, authn=None)
        app.add_route("/agent/{caid}", agentEnd)

        client = testing.TestClient(app=app)

        res = client.simulate_get(path="/agent/bad_pre")
        assert res.status_code == 404

        res = client.simulate_get(path=f"/agent/{agent.caid}")
        assert res.status_code == 200
        assert res.json["agent"] == {'b': [],
                                     'bt': '0',
                                     'c': [],
                                     'd': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9',
                                     'di': 'EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx',
                                     'dt': '2021-01-01T00:00:00.000000+00:00',
                                     'ee': {'ba': [],
                                            'br': [],
                                            'd': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9',
                                            's': '0'},
                                     'et': 'dip',
                                     'f': '0',
                                     'i': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9',
                                     'k': ['DKDAV2tanHP1NpxGrdMRwF0ALPfzr0E87XUB4lnIaGad'],
                                     'kt': '1',
                                     'n': ['EKcqCVGNZIsKnPP9UwtENc8U0hygWZWCMrg0NNpNmwLe'],
                                     'nt': '1',
                                     'p': '',
                                     's': '0',
                                     'vn': [1, 0]}
        assert res.json["controller"] == {'ee': {'a': [],
                                                 'b': [],
                                                 'bt': '0',
                                                 'c': [],
                                                 'd': 'EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx',
                                                 'i': 'EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx',
                                                 'k': ['DMVCX7CtEX7KgHtNLKQdSuqZhAs0m-tt9KSVI1kv1sYV'],
                                                 'kt': '1',
                                                 'n': ['EJ_E97qRUDPOKbQmpuIgG-0G_-AO0obz7KSidyblcGC8'],
                                                 'nt': '1',
                                                 's': '0',
                                                 't': 'icp',
                                                 'v': 'KERI10JSON00012b_'},
                                          'state': {'b': [],
                                                    'bt': '0',
                                                    'c': [],
                                                    'd': 'EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx',
                                                    'di': '',
                                                    'dt': '2021-01-01T00:00:00.000000+00:00',
                                                    'ee': {'ba': [],
                                                           'br': [],
                                                           'd': 'EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx',
                                                           's': '0'},
                                                    'et': 'icp',
                                                    'f': '0',
                                                    'i': 'EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx',
                                                    'k': ['DMVCX7CtEX7KgHtNLKQdSuqZhAs0m-tt9KSVI1kv1sYV'],
                                                    'kt': '1',
                                                    'n': ['EJ_E97qRUDPOKbQmpuIgG-0G_-AO0obz7KSidyblcGC8'],
                                                    'nt': '1',
                                                    'p': '',
                                                    's': '0',
                                                    'vn': [1, 0]}}
        assert res.json["pidx"] == 0


def test_identifier_collection_end(helpers):
    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHby(name="p1", temp=True) as p1hby, \
            habbing.openHby(name="p2", temp=True) as p2hby:
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)

        groupEnd = aiding.GroupMemberCollectionEnd()
        app.add_route("/identifiers/{name}/members", groupEnd)

        client = testing.TestClient(app)

        res = client.simulate_post(path="/identifiers", body=b'{}')
        assert res.status_code == 400
        assert res.json == {'description': "required field 'icp' missing from request",
                            'title': '400 Bad Request'}

        salt = b'0123456789abcdef'
        serder, signers = helpers.incept(salt, "signify:aid", pidx=0)
        assert len(signers) == 1
        signer0 = signers[0]
        diger0 = serder.digers[0]

        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]
        body = {'name': 'aid1',
                'icp': serder.ked,
                'sigs': sigers,
                }

        # Try to create one without key params
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 400
        assert res.json == {'description': 'invalid request: one of group, rand or salt field required',
                            'title': '400 Bad Request'}

        salter = coring.Salter(raw=salt)
        encrypter = coring.Encrypter(verkey=signers[0].verfer.qb64)
        sxlt = encrypter.encrypt(salter.qb64).qb64

        body = {'name': 'aid1',
                'icp': serder.ked,
                'sigs': sigers,
                "salty": {
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low', 'sxlt': sxlt,
                    'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        # Try to resubmit and get an error
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 500
        assert res.json == {'description': 'Already incepted '
                                           'pre=EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY.',
                            'title': '500 Internal Server Error'}

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 1
        aid = res.json[0]
        assert aid["name"] == "aid1"
        assert aid["prefix"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        serder, signer = helpers.incept(salt, "signify:aid", pidx=1, count=3)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'aid2',
                'icp': serder.ked,
                'sigs': sigers,
                'salty': {'stem': 'signify:aid', 'pidx': 1, 'tier': 'low', 'sxlt': sxlt,
                          'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}}
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

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
                'salty': {'stem': 'signify:aid', 'pidx': 3, 'tier': 'low', 'sxlt': sxlt,
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
        states = nstates = [agent0, asdict(p1.kever.state()), asdict(p2.kever.state())]

        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "keys": keys,
                "ndigs": ndigs
            }
        }
        # Try without mhab
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 400
        assert res.json == {'description': 'required field "mhab" missing from body.group',
                            'title': '400 Bad Request'}

        bad = dict(mhab)
        bad["prefix"] = "12345"
        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": bad,
                "keys": keys,
                "ndigs": ndigs
            }
        }
        # Try with bad mhab
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 400
        assert res.json == {'description': 'signing member 12345 not a local AID',
                            'title': '400 Bad Request'}

        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": mhab,
                "ndigs": ndigs
            }
        }
        # Try without keys
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 400
        assert res.json == {'description': 'required field "keys" missing from body.group',
                            'title': '400 Bad Request'}

        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": mhab,
                "keys": keys,
            }
        }

        # Try without ndigs
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 400
        assert res.json == {'description': 'required field "ndigs" missing from body.group',
                            'title': '400 Bad Request'}

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

        # Resubmit to get an error
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 500
        assert res.json == {'description': 'Already incepted '
                                           'pre=EGOSjnzaVz4nZ55wk3-SV78WgdaTJZddhom9ZLeNFEd3.',
                            'title': '500 Internal Server Error'}

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 4
        aid = res.json[3]
        assert aid["name"] == "multisig"
        assert aid["prefix"] == serder.pre
        group = aid["group"]

        assert group["keys"] == ['DDNGgXzEO4LD8G1z1uD7eIDF2pDj6Y7hVx-nqhYZmU_8',
                                 'DAOF6DRwWDphP8F2r87uxTS9xwIehonmTBE1agJrPklA',
                                 'DPZ-k6HXUhiS5dPy8awuitFpwojGOQJ6DMZiatPjhXKC']
        assert group["ndigs"] == ['EHj7rmVHVkQKqnfeer068PiYvYm-WFSTVZZpFGsClfT-',
                                  'ECTS-VsMzox2NoMaLIei9Gb6361Z3u0fFFWmjEjEeD64',
                                  'ED7Jk3MscDy8IHtb2k1k6cs0Oe5rEb3_8XKD1Ut_gCo8']

        # Test Group Members

        # try with bad aid alias
        res = client.simulate_get(path="/identifiers/janky/members")
        assert res.status_code == 404

        # try with single sig
        res = client.simulate_get(path="/identifiers/aid1/members")
        assert res.status_code == 400

        res = client.simulate_get(path="/identifiers/multisig/members")
        assert res.status_code == 200
        assert "signing" in res.json
        signing = res.json["signing"]
        assert len(signing) == 5  # this number is a little janky because we reuse public keys above, leaving for now
        assert "rotation" in res.json
        rotation = res.json["rotation"]
        assert len(rotation) == 5  # this number is a little janky because we reuse rotation keys above, leaving for now

    # Lets test randy with some key rotations and interaction events
    with helpers.openKeria() as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)
        eventsEnd = agenting.KeyEventCollectionEnd()
        app.add_route("/events", eventsEnd)

        client = testing.TestClient(app)

        # Test with randy
        salt = b'0123456789abcdef'
        serder, signers, prxs, nxts = helpers.inceptRandy(bran=salt, count=1)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'randy1',
                'icp': serder.ked,
                'sigs': sigers,
                'randy': {
                    "prxs": prxs,
                    "nxts": nxts,
                    "transferable": True,
                }
                }
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        # Resubmit and get an error
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 500
        assert res.json['title'] == '500 Internal Server Error'

        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 1
        randy1 = res.json[0]
        assert randy1['name'] == "randy1"
        pre = randy1["prefix"]
        params = randy1["randy"]

        salter = coring.Salter(raw=salt)
        signer = salter.signer(transferable=False)
        decrypter = coring.Decrypter(seed=signer.qb64)
        encrypter = coring.Encrypter(verkey=signer.verfer.qb64)

        # Now rotate, we must decrypt the prxs, nxts, create a new next key and the rotation event
        nxts = params["nxts"]
        signers = [decrypter.decrypt(cipher=coring.Cipher(qb64=nxt),
                                     transferable=True) for nxt in nxts]
        creator = keeping.RandyCreator()
        nsigners = creator.create(count=1)
        keys = [signer.verfer.qb64 for signer in signers]
        ndigs = [coring.Diger(ser=nsigner.verfer.qb64b) for nsigner in nsigners]

        serder = eventing.rotate(keys=keys,
                                 pre=pre,
                                 dig=pre,
                                 isith="1",
                                 nsith="1",
                                 ndigs=[diger.qb64 for diger in ndigs])

        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]
        prxs = [encrypter.encrypt(matter=signer).qb64 for signer in signers]
        nxts = [encrypter.encrypt(matter=signer).qb64 for signer in nsigners]

        body = {'rot': serder.ked,
                'sigs': sigers,
                'randy': {
                    "prxs": prxs,
                    "nxts": nxts,
                    "transferable": True,
                }
                }
        res = client.simulate_put(path="/identifiers/randy1", body=json.dumps(body))
        assert res.status_code == 200
        assert res.json["response"] == serder.ked
        res = client.simulate_get(path="/identifiers")
        assert res.status_code == 200
        assert len(res.json) == 1

        res = client.simulate_get(path=f"/events?pre={pre}")
        assert res.status_code == 200
        events = res.json
        assert len(events) == 2
        assert events[1] == serder.ked

        serder = eventing.interact(pre=pre, dig=serder.said, sn=len(events), data=[pre])
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]
        body = {'ixn': serder.ked,
                'sigs': sigers
                }
        res = client.simulate_put(path="/identifiers/randy1?type=ixn", body=json.dumps(body))
        assert res.status_code == 200
        assert res.json["response"] == serder.ked

        res = client.simulate_get(path=f"/events?pre={pre}")
        assert res.status_code == 200
        events = res.json
        assert len(events) == 3
        assert events[2] == serder.ked

    # Lets test delegated AID
    with helpers.openKeria() as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)
        eventsEnd = agenting.KeyEventCollectionEnd()
        app.add_route("/events", eventsEnd)

        client = testing.TestClient(app)
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "delegator", salt)
        aid = op["response"]
        delpre = aid['i']
        assert delpre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        op = helpers.createAid(client, "delegatee", salt, delpre=delpre)
        assert op['name'] == "delegation.EFt8G8gkCJ71e4amQaRUYss0BDK4pUpzKelEIr3yZ1D0"

    # Test extern keys for HSM integration, only initial tests, work still needed
    with helpers.openKeria() as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)

        client = testing.TestClient(app)

        # Test with randy
        serder, signers = helpers.inceptExtern(count=1)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': 'randy1',
                'icp': serder.ked,
                'sigs': sigers,
                'extern': {
                    "stem": "test-fake-stem",
                    "transferable": True,
                }
                }
        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202


def test_challenge_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
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
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "pal", salt)
        aid = op["response"]

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
    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHby(name="ken", salt=coring.Salter(raw=b'0123456789ghijkl').qb64) as kenHby:

        # Register the identifier endpoint so we can create an AID for the test
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "pal", salt)
        aid = op["response"]
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


def test_identifier_resource_end(helpers):
    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHby(name="p1", temp=True) as p1hby, \
            habbing.openHby(name="p2", temp=True) as p2hby:
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)

        client = testing.TestClient(app)
        salt = b'0123456789abcdef'
        serder, signers = helpers.incept(salt, "signify:aid", pidx=0)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]
        salter = coring.Salter(raw=salt)
        encrypter = coring.Encrypter(verkey=signers[0].verfer.qb64)
        sxlt = encrypter.encrypt(salter.qb64).qb64

        body = {'name': 'aid1',
                'icp': serder.ked,
                'sigs': sigers,
                "salty": {
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low', 'sxlt': sxlt,
                    'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        res = client.simulate_get(path="/identifiers/bad")
        assert res.status_code == 404
        assert res.json == {'description': 'bad is not a valid identifier name', 'title': '404 Not Found'}

        res = client.simulate_get(path="/identifiers/aid1")
        assert res.status_code == 200
        assert res.json['prefix'] == 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY'


def test_oobi_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)

        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)
        aidOOBIsEnd = IdentifierOOBICollectionEnd()
        app.add_route("/identifiers/{name}/oobis", aidOOBIsEnd)

        client = testing.TestClient(app)
        # Create an AID to test against
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "pal", salt)
        iserder = coring.Serder(ked=op["response"])
        assert iserder.pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        # Test before endroles are added
        res = client.simulate_get("/identifiers/pal/oobis?role=agent")
        assert res.status_code == 404

        rpy = helpers.endrole(iserder.pre, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)

        res = client.simulate_post(path=f"/identifiers/pal/endroles", json=body)
        op = res.json
        ked = op["response"]
        serder = coring.Serder(ked=ked)
        assert serder.raw == rpy.raw

        # must be a valid aid alias
        res = client.simulate_get("/identifiers/bad/oobis")
        assert res.status_code == 404

        # role parameter is required
        res = client.simulate_get("/identifiers/pal/oobis")
        assert res.status_code == 400
        assert res.json == {'description': 'role parameter required', 'title': '400 Bad Request'}

        # role parameter must be valie
        res = client.simulate_get("/identifiers/pal/oobis?role=banana")
        assert res.status_code == 400
        assert res.json == {'description': 'unsupport role type banana for oobi request',
                            'title': '400 Bad Request'}

        res = client.simulate_get("/identifiers/pal/oobis?role=agent")
        assert res.status_code == 200
        role = res.json['role']
        oobis = res.json['oobis']

        assert role == "agent"
        assert len(oobis) == 1
        assert oobis[0] == ("http://127.0.0.1:3902/oobi/EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY/agent/EI7AkI40M1"
                            "1MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9")

        res = client.simulate_get("/identifiers/pal/oobis?role=witness")
        assert res.status_code == 200
        role = res.json['role']
        oobis = res.json['oobis']

        assert role == "witness"
        assert len(oobis) == 0

        res = client.simulate_get("/identifiers/pal/oobis?role=controller")
        assert res.status_code == 404

        # Jam HTTP loc record for pre in database
        agent.hby.db.locs.pin(keys=(iserder.pre, kering.Schemes.http), val=LocationRecord(url="http://localhost:1234/"))

        res = client.simulate_get("/identifiers/pal/oobis?role=controller")
        assert res.status_code == 200
        role = res.json['role']
        oobis = res.json['oobis']

        assert role == "controller"
        assert len(oobis) == 1
        assert oobis[0] == "http://localhost:1234/oobi/EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY/controller"


def test_rpy_escow_end(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        rpyEscrowEnd = RpyEscrowCollectionEnd()
        app.add_route("/escrows/rpy", rpyEscrowEnd)

        rpy1 = helpers.endrole("EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
                              "ECL8abFVW_0RTZXFhiiA4rkRobNvjTfJ6t-T8UdBRV1e")
        agent.hby.db.rpes.add(keys=("/end/role",), val=rpy1.saider)
        agent.hby.db.rpys.put(keys=(rpy1.said,), val=rpy1)

        rpy2 = helpers.endrole("EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
                              "ECL8abFVW_0RTZXFhiiA4rkRobNvjTfJ6t-T8UdBRV1e",
                              role=kering.Roles.controller)
        agent.hby.db.rpes.add(keys=("/end/role",), val=rpy2.saider)
        agent.hby.db.rpys.put(keys=(rpy2.said,), val=rpy2)

        rpy3 = helpers.endrole("EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
                              "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
                              role=kering.Roles.witness)
        agent.hby.db.rpes.add(keys=("/end/role",), val=rpy3.saider)
        agent.hby.db.rpys.put(keys=(rpy3.said,), val=rpy3)

        res = client.simulate_get(path="/escrows/rpy?route=/end/role")
        assert res.status_code == 200
        assert len(res.json) == 3

        esc = res.json
        assert esc[0] == rpy1.ked
        assert esc[1] == rpy2.ked
        assert esc[2] == rpy3.ked


