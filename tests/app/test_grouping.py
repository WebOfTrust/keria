# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.grouping module

Testing the Mark II Agent Grouping endpoints

"""
import json

from keri.app.habbing import SignifyGroupHab
from keri.core import eventing, coring
from keri.peer import exchanging

from keria.app import grouping, aiding


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        grouping.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/identifiers/NAME/multisig/request")
        assert isinstance(end, grouping.MultisigRequestCollectionEnd)
        (end, *_) = app._router.find("/multisig/request/SAID")
        assert isinstance(end, grouping.MultisigRequestResourceEnd)


def test_multisig_request_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        grouping.loadEnds(app=app)
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)
        msrCol = grouping.MultisigRequestCollectionEnd()
        app.add_route("/identifiers/{name}/multisig/request", msrCol)
        msrRes = grouping.MultisigRequestResourceEnd()
        app.add_route("/multisig/request/{said}", msrRes)

        # First create participants (aid0, aid1) in a multisig AID
        salt0 = b'0123456789abcdef'
        op = helpers.createAid(client, "aid0", salt0)
        aid0 = op["response"]
        pre0 = aid0['i']
        assert pre0 == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        serder, signers0 = helpers.incept(salt0, "signify:aid", pidx=0)
        assert serder.pre == pre0
        signer0 = signers0[0]

        salt1 = b'abcdef0123456789'
        op = helpers.createAid(client, "aid1", salt1)
        aid1 = op["response"]
        pre1 = aid1['i']
        assert pre1 == "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"
        serder, signers1 = helpers.incept(salt1, "signify:aid", pidx=0)
        assert serder.pre == pre1
        signer1 = signers1[0]

        # Get their hab dicts
        m0 = client.simulate_get("/identifiers/aid0").json
        m1 = client.simulate_get("/identifiers/aid1").json

        assert m0["prefix"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        assert m1["prefix"] == "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"

        keys = [m0['state']['k'][0], m1['state']['k'][0]]
        ndigs = [m0['state']['n'][0], m1['state']['n'][0]]

        # Create the mutlsig inception event
        serder = eventing.incept(keys=keys,
                                 isith="2",
                                 nsith="2",
                                 ndigs=ndigs,
                                 code=coring.MtrDex.Blake3_256,
                                 toad=0,
                                 wits=[])
        assert serder.said == "EG8p1Zb4BfyKYkA9SkpyTvCo9xoCsISlOl7YlsB5b1Vt"

        # Send in all signatures as if we are joining the inception event
        sigers = [signer0.sign(ser=serder.raw, index=0).qb64, signer1.sign(ser=serder.raw, index=1).qb64]
        states = nstates = [m0['state'], m1['state']]

        body = {
            'name': 'multisig',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": m0,
                "keys": keys,
                "ndigs": ndigs
            }
        }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        # Get the multisig AID hab dict
        m2 = client.simulate_get(path="/identifiers/multisig").json
        pre2 = m2['prefix']
        assert pre2 == "EG8p1Zb4BfyKYkA9SkpyTvCo9xoCsISlOl7YlsB5b1Vt"

        payload = dict(i=pre2, words="these are the words being signed for this response")
        cexn, _ = exchanging.exchange(route="/challenge/response", payload=payload, sender=agent.agentHab.pre)

        # Signing this with agentHab because I'm lazing.  Nothing will be done with this signature
        cha = agent.agentHab.endorse(serder=cexn, last=False, pipelined=False)

        embeds = dict(
            exn=cha
        )
        exn, end = exchanging.exchange(route="/multisig/exn", payload=dict(gid=pre2), embeds=embeds,
                                       sender=pre0)
        sig = signer0.sign(exn.raw, index=0).qb64
        body = dict(
            exn=exn.ked,
            sigs=[sig],
            atc=end.decode("utf-8")
        )

        res = client.simulate_post(path="/identifiers/badaid/multisig/request", json=body)
        assert res.status_code == 404

        res = client.simulate_post(path="/identifiers/aid1/multisig/request", json=body)
        assert res.status_code == 400

        res = client.simulate_post(path="/identifiers/multisig/multisig/request", json=body)
        assert res.status_code == 200
        assert res.json == exn.ked

        said = exn.said

        # Fudge this because we won't be able to save a message from someone else:
        esaid = exn.ked['e']['d']
        agent.hby.db.meids.add(keys=(esaid,), val=coring.Saider(qb64=exn.said))

        res = client.simulate_get(path=f"/multisig/request/BADSAID")
        assert res.status_code == 404

        res = client.simulate_get(path=f"/multisig/request/{said}")
        assert res.status_code == 200
        assert len(res.json) == 1

        req = res.json[0]

        assert req['exn'] == exn.ked
        path = req['paths']['exn']
        assert '-LA35AACAA-e-exn' + path == end.decode("utf-8")

        # We've send this one exn to our other participants
        assert len(agent.exchanges) == 1


def test_join(helpers, monkeypatch):
    with helpers.openKeria() as (agency, agent, app, client):
        grouping.loadEnds(app)

        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)

        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "recipient", salt)
        aid = op["response"]

        assert aid["i"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        body = dict(
            rot=dict(
                k=[
                    "DNp1NUbUEgei6KOlIfT5evXueOi3TDFZkUXgJQWNvegf",
                    "DLsXs0-dxqrM4hugX7NkfZUzET13ngfRhWC9GgXvX9my",
                    "DE2W_yGSF-m44vXPuQ5_wHJ9EK59N-OIT3hABgdAcCKs",
                    "DKFKNK7s0xLhazlmL3xH9YEl9sc3fVoqUSsQxK6DZ3oC",
                    "DEyEcy5NzjqA3KQ1DTE0BJs-XMIdWIvPWligyq6y1TxS",
                    "DGhflVckn2wVLJH6wq94gGQxmpvsFdsZvd61Owj3Qhjl",
                ],
                n=[
                    "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",
                    "EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1",
                    "EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc",
                    "EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5",
                    "EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh",
                    "EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs"
                ]
            ),
            sigs=[],
            gid="EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I",
            smids=[
                "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",
                "EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1",
                "EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc",
                "EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5",
                "EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh",
                "EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs"
            ],
            rmids=[
                "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",
                "EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1",
                "EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc",
                "EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5",
                "EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh",
                "EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs"
            ]
        )

        res = client.simulate_post("/identifiers/mms/multisig/join", json=body)
        assert res.status_code == 400

        for smid in body['smids']:
            agent.hby.kevers[smid] = {}

        for rmid in body['rmids']:
            agent.hby.kevers[rmid] = {}

        res = client.simulate_post("/identifiers/mms/multisig/join", json=body)
        assert res.status_code == 400
        assert res.json == {'description': 'Invalid multisig group rotation request, signing member list '
                                           "must contain a local identifier'",
                            'title': '400 Bad Request'}

        body['smids'][0] = aid["i"]

        res = client.simulate_post("/identifiers/mms/multisig/join", json=body)
        assert res.status_code == 400
        assert res.json == {'description': "Missing version string field in {'k': "
                                           "['DNp1NUbUEgei6KOlIfT5evXueOi3TDFZkUXgJQWNvegf', "
                                           "'DLsXs0-dxqrM4hugX7NkfZUzET13ngfRhWC9GgXvX9my', "
                                           "'DE2W_yGSF-m44vXPuQ5_wHJ9EK59N-OIT3hABgdAcCKs', "
                                           "'DKFKNK7s0xLhazlmL3xH9YEl9sc3fVoqUSsQxK6DZ3oC', "
                                           "'DEyEcy5NzjqA3KQ1DTE0BJs-XMIdWIvPWligyq6y1TxS', "
                                           "'DGhflVckn2wVLJH6wq94gGQxmpvsFdsZvd61Owj3Qhjl'], 'n': "
                                           "['EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4', "
                                           "'EJccSRTfXYF6wrUVuenAIHzwcx3hJugeiJsEKmndi5q1', "
                                           "'EBFg-5SGDCv5YfwpkArWRBdTxNRUXU8uVcDKNzizOQZc', "
                                           "'EBmW2bXbgsP3HITwW3FmITzAb3wVmHlxCusZ46vgGgP5', "
                                           "'EL4RpdS2Atb2Syu5xLdpz9CcNNYoFUUDlLHxHD09vcgh', "
                                           "'EAiBVuuhCZrgckeHc9KzROVGJpmGbk2-e1B25GaeRrJs']}.",
                            'title': '400 Bad Request'}

        body['rot'] = {
            "v": "KERI10JSON00030c_",
            "t": "rot",
            "d": "EPKCBT0rSgFKTDRjynYzOTsYWo7fDNElTxFbRZZW9f6R",
            "i": "EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I",
            "s": "3",
            "p": "EM2OaIZuLWyGGyxf4Tzs6yeoENvjP47i1Dn88GGxw3_Z",
            "kt": [
                "0",
                "0",
                "1/2",
                "1/2",
                "1/2",
                "1/2"
            ],
            "k": [
                "DNp1NUbUEgei6KOlIfT5evXueOi3TDFZkUXgJQWNvegf",
                "DLsXs0-dxqrM4hugX7NkfZUzET13ngfRhWC9GgXvX9my",
                "DE2W_yGSF-m44vXPuQ5_wHJ9EK59N-OIT3hABgdAcCKs",
                "DKFKNK7s0xLhazlmL3xH9YEl9sc3fVoqUSsQxK6DZ3oC",
                "DEyEcy5NzjqA3KQ1DTE0BJs-XMIdWIvPWligyq6y1TxS",
                "DGhflVckn2wVLJH6wq94gGQxmpvsFdsZvd61Owj3Qhjl"
            ],
            "nt": [
                "1/2",
                "1/2",
                "1/2",
                "1/2"
            ],
            "n": [
                "EDr0gf60BDB9cZyVoz_Os55Ma49muyCNTZoWG-VWAe6g",
                "EIM3hKH1VBG_ofS7hD-XMfTG-dP1ziJwloFhrNx34G7o",
                "EOi609MGQlByLPdaUgqGQn_IOEE4cf6u7zCW-J3E82Qz",
                "ECQF1Tdpcqew6dqN6nHNpz4jhYTZtojl7EpqVJhXRBav"
            ],
            "bt": "3",
            "br": [],
            "ba": [],
            "a": []
        }

        def make(self, serder, sigers):
            return True

        monkeypatch.setattr(SignifyGroupHab, "make", make)

        res = client.simulate_post("/identifiers/mms/multisig/join", json=body)
        assert res.status_code == 202
        assert res.json == {'done': False,
                            'error': None,
                            'metadata': {'sn': 3},
                            'name': 'group.EDWg3-rB5FTpcckaYdBcexGmbLIO6AvAwjaJTBlXUn_I',
                            'response': None}

        res = client.simulate_post("/identifiers/mms/multisig/join", json=body)
        assert res.status_code == 400
        assert res.json == {'description': 'attempt to create identifier with an already used alias=mms',
                            'title': '400 Bad Request'}
