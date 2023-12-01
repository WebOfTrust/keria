# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.exchanging module

Testing the Mark II Agent Grouping endpoints

"""
import json

from hio.base import doing
from keri.core import eventing, serdering
from keri.peer.exchanging import exchange

from keria.app import aiding
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

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        deeds = doist.enter(doers=[agent])

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
        serder, sigers = helpers.incept(salt, "signify:aid", pidx=0)
        assert serder.pre == pre
        signer = sigers[0]

        ims = eventing.messagize(serder=serder, sigers=sigers)

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
        assert res.status_code == 202
        assert res.json == cexn.ked
        assert len(agent.exchanges) == 1

        doist.recur(deeds=deeds)

        assert len(agent.exchanges) == 0
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
        assert res.status_code == 202
        assert len(agent.exchanges) == 1
        assert res.json == exn.ked

        doist.recur(deeds=deeds)

        assert len(agent.exchanges) == 0
        agent.exnseeker.index(exn.said)

        body = json.dumps({}).encode("utf-8")
        res = client.simulate_post(f"/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        body = json.dumps({'filter': {'-i': pre}, 'sort': ['-dt']}).encode("utf-8")
        res = client.simulate_post(f"/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        ked = res.json[0]['exn']
        serder = serdering.SerderKERI(sad=ked)
        assert serder.said == cexn.said

        ked = res.json[1]['exn']
        serder = serdering.SerderKERI(sad=ked)
        assert serder.said == exn.said

        body = json.dumps({'filter': {'-i': pre}, 'sort': ['-dt'], 'skip': 1, "limit": 1}).encode("utf-8")
        res = client.simulate_post(f"/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 1

        ked = res.json[0]['exn']
        serder = serdering.SerderKERI(sad=ked)
        assert serder.said == exn.said

        res = client.simulate_get(f"/exchanges/{exn.said}")
        assert res.status_code == 200
        serder = serdering.SerderKERI(sad=res.json['exn'])
        assert serder.said == exn.said

        payload = dict(
            m="Please give me credential",
            s=QVI_SAID,
            a=dict(),
            i=pre1
        )

        embeds = dict(
            icp=ims,
        )
        exn, atc = exchange(route="/ipex/offer", payload=payload, sender=pre, embeds=embeds)
        sig = signer.sign(ser=exn.raw, index=0).qb64

        body = dict(
            exn=exn.ked,
            sigs=[sig],
            atc=atc.decode("utf-8"),
            rec=[pre1],
            tpc="/ipex"
        )

        res = client.simulate_post(path="/identifiers/aid1/exchanges", json=body)
        assert res.status_code == 202
        assert len(agent.exchanges) == 1
        assert res.json == exn.ked

        doist.recur(deeds=deeds)
        agent.exnseeker.index(exn.said)

        body = json.dumps({'sort': ['-dt']}).encode("utf-8")
        res = client.simulate_post(f"/exchanges/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 3

        offer = res.json[2]
        assert offer['pathed'] == {'icp': '-AABADzZ23DyzL4TLQqTtjx5IKkWwRt3_NYHHIqc9g1rBjwr'}



