# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.exchanging module

Testing the Mark II Agent Grouping endpoints

"""
import json

from keri.app import habbing, signing
from keri.core import coring, parsing
from keri.peer.exchanging import exchange, Exchanger
from keri.vc import protocoling

from keria.app import aiding, credentialing
from keria.core import longrunning
from keria.db import basing
from keria.peer import exchanging


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        exchanging.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/identifiers/NAME/exchanges")
        assert isinstance(end, exchanging.ExchangeCollectionEnd)


def test_exchange_end(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        exchanging.loadEnds(app=app)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)

        # First create participants (aid1, aid2) in a multisig AID
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "aid1", salt)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        serder, signers = helpers.incept(salt, "signify:aid", pidx=0)
        assert serder.pre == pre
        signer = signers[0]

        salt1 = b'abcdef0123456789'
        op = helpers.createAid(client, "aid2", salt1)
        aid1 = op["response"]
        pre1 = aid1['i']
        assert pre1 == "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"

        payload = dict(i=pre, words="these are the words being signed for this response")
        cexn, _ = exchange(route="/challenge/response", payload=payload, sender=pre)
        sig = signer.sign(ser=cexn.raw, index=0).qb64

        body = dict(
            exn=cexn.ked,
            sigs=[sig],
            atc="",
            rec=[pre1],
            tpc="/credentials"
        )

        res = client.simulate_post(path="/identifiers/aid1/exchanges", json=body)
        assert res.status_code == 200
        assert res.json == cexn.ked
        assert len(agent.postman.evts) == 1
        agent.exnseeker.index(cexn.said)

        QVI_SAID = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        payload = dict(
            m="Please give me credential",
            s=QVI_SAID,
            a=dict(),
            i=pre1
        )
        exn, _ = exchange(route="/ipex/apply", payload=payload, sender=pre)
        sig = signer.sign(ser=exn.raw, index=0).qb64

        body = dict(
            exn=exn.ked,
            sigs=[sig],
            atc="",
            rec=[pre1],
            tpc="/credentials"
        )

        res = client.simulate_post(path="/identifiers/bad/exchanges", json=body)
        assert res.status_code == 404

        res = client.simulate_post(path="/identifiers/aid1/exchanges", json=body)
        assert res.status_code == 200
        assert res.json == exn.ked
        assert len(agent.postman.evts) == 2
        agent.exnseeker.index(exn.said)

        body = json.dumps({}).encode("utf-8")
        res = client.simulate_post(f"/identifiers/aid1/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        body = json.dumps({'filter': {'-i': pre}, 'sort': ['-dt']}).encode("utf-8")
        res = client.simulate_post(f"/identifiers/aid1/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        ked = res.json[0]['exn']
        serder = coring.Serder(ked=ked)
        assert serder.said == cexn.said

        ked = res.json[1]['exn']
        serder = coring.Serder(ked=ked)
        assert serder.said == exn.said

        body = json.dumps({'filter': {'-i': pre}, 'sort': ['-dt'], 'skip': 1, "limit": 1}).encode("utf-8")
        res = client.simulate_post(f"/identifiers/aid1/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 1

        ked = res.json[0]['exn']
        serder = coring.Serder(ked=ked)
        assert serder.said == exn.said

        res = client.simulate_get(f"/identifiers/aid1/exchanges/{exn.said}")
        assert res.status_code == 200
        serder = coring.Serder(ked=res.json['exn'])
        assert serder.said == exn.said
