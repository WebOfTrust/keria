# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ipe module

Testing credentialing endpoint in the Mark II Agent
"""
import json

from falcon import testing
from keri.core import eventing, coring
from keri.help import helping
from keri.peer import exchanging

from keria.app import ipexing, aiding


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        ipexing.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/identifiers/NAME/ipex/admit")
        assert isinstance(end, ipexing.IpexAdmitCollectonEnd)


def test_ipex_admit(helpers, mockHelpingNowIso8601):
    with helpers.openKeria() as (agency, agent, app, client):
        client = testing.TestClient(app)

        admitEnd = ipexing.IpexAdmitCollectonEnd()
        app.add_route("/identifiers/{name}/ipex/admit", admitEnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        dig = "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT"

        salt2 = b'0123456789abcdeg'
        op = helpers.createAid(client, "recp", salt2)
        aid1 = op["response"]
        pre1 = aid1['i']
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"

        exn, end = exchanging.exchange(route="/ipex/admit",
                                       payload=dict(),
                                       sender=pre,
                                       embeds=dict(),
                                       dig=dig,
                                       recipient=pre1,
                                       date=helping.nowIso8601())
        assert exn.ked == {'a': {'i': 'EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm'},
                           'd': 'EBrMlfQbJRS9RYuP90t2PPPV24Qynmtu7BefWAqWzb0Q',
                           'dt': '2021-06-27T21:26:21.233257+00:00',
                           'e': {},
                           'i': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                           'p': 'EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT',
                           'q': {},
                           'r': '/ipex/admit',
                           't': 'exn',
                           'v': 'KERI10JSON00013d_'}
        assert end == b''
        sigs = ["AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"]

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc="",
            rec=["EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        assert res.status_code == 400
        assert res.json == {'title': 'attempt to send to unknown '
                                     'AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc="",
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        assert res.status_code == 400
        assert res.json == {'description': 'attachment missing for ACDC, unable to process request.',
                            'title': '400 Bad Request'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc="this is a fake attachment",
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        assert res.status_code == 202
        assert len(agent.exchanges) == 1
        assert len(agent.admits) == 1

        agent.exchanges.clear()
        agent.admits.clear()

        ims = eventing.messagize(serder=exn, sigers=[coring.Siger(qb64=sigs[0])])
        # Test sending embedded admit in multisig/exn message
        exn, end = exchanging.exchange(route="/multisig/exn",
                                       payload=dict(),
                                       sender=pre,
                                       embeds=dict(exn=ims),
                                       dig=dig,
                                       date=helping.nowIso8601())

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=dict(exn=end.decode("utf-8")),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        print(res.json)
        assert res.status_code == 202
        assert len(agent.exchanges) == 2
        assert len(agent.admits) == 1
