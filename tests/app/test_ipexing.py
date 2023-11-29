# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ipe module

Testing credentialing endpoint in the Mark II Agent
"""
import json

from falcon import testing
from hio.base import doing
from hio.help import decking
from keri.app import habbing, signing
from keri.core import eventing, coring
from keri.help import helping
from keri.peer import exchanging
from keri.vc import proving

from keria.app import ipexing, aiding, agenting
from keria.app.credentialing import CredentialResourceEnd


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        ipexing.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/identifiers/NAME/ipex/admit")
        assert isinstance(end, ipexing.IpexAdmitCollectionEnd)
        (end, *_) = app._router.find("/identifiers/NAME/ipex/grant")
        assert isinstance(end, ipexing.IpexGrantCollectionEnd)


def test_ipex_admit(helpers, mockHelpingNowIso8601):
    with helpers.openKeria() as (agency, agent, app, client):
        client = testing.TestClient(app)

        admitEnd = ipexing.IpexAdmitCollectionEnd()
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
        assert res.json == {'description': 'attempt to send to unknown '
                                           'AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM',
                            'title': '400 Bad Request'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc="",
            rec=[pre1]
        )

        # Bad Sender
        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/BAD/ipex/admit", body=data)
        assert res.status_code == 404

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

        # Bad recipient
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=dict(exn=end.decode("utf-8")),
            rec=["EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'attempt to send to unknown '
                                           'AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM',
                            'title': '400 Bad Request'}

        # Bad attachments
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=dict(bad=end.decode("utf-8")),
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
            atc=dict(exn=end.decode("utf-8")),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        assert res.status_code == 202
        assert len(agent.exchanges) == 2
        assert len(agent.admits) == 1


def test_ipex_grant(helpers, mockHelpingNowIso8601, seeder):
    salt = b'0123456789abcdef'

    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHab(name="issuer", salt=salt, temp=True) as (issuerHby, issuerHab), \
            helpers.withIssuer(name="issuer", hby=issuerHby) as issuer:

        client = testing.TestClient(app)
        seeder.seedSchema(agent.hby.db)
        seeder.seedSchema(issuerHby.db)

        grantAnd = ipexing.IpexGrantCollectionEnd()
        app.add_route("/identifiers/{name}/ipex/grant", grantAnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)

        salt2 = b'0123456789abcdeg'
        op = helpers.createAid(client, "legal-entity", salt2)
        le = op["response"]
        pre1 = le['i']
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"

        salt3 = b'0123456789abc123'
        op = helpers.createAid(client, "verifier", salt3)
        verifier = op["response"]
        pre1 = verifier['i']
        assert pre1 == "EEtaMHCGi83N3IJN05DRDhkpIo5S03LOX5_8IgdvMaVq"

        # Lets issue a QVI credential to the QVI
        issuer.createRegistry(issuerHab.pre, name="issuer")
        qvisaid = issuer.issueQVIvLEI("issuer", issuerHab, le['i'], "78I9GKEFM361IFY3PIN0")

        ims = CredentialResourceEnd.outputCred(issuer.hby, issuer.rgy, qvisaid)

        agent.parser.parse(ims)

        creder, prefixer, seqner, saider = agent.rgy.reger.cloneCred(said=qvisaid)
        acdc = signing.serialize(creder, prefixer, seqner, saider)

        iss = next(agent.rgy.reger.clonePreIter(pre=creder.said))
        anc = next(agent.hby.db.clonePreIter(pre=issuerHab.pre, fn=1))
        embeds = dict(
            acdc=acdc,
            iss=iss,
            anc=anc
        )

        exn, end = exchanging.exchange(route="/ipex/grant",
                                       payload=dict(),
                                       sender=le['i'],
                                       embeds=embeds,
                                       recipient=verifier['i'],
                                       date=helping.nowIso8601())
        assert exn.ked == {'a': {'i': 'EEtaMHCGi83N3IJN05DRDhkpIo5S03LOX5_8IgdvMaVq'},
                           'd': 'EHwjDEsub6XT19ISLft1m1xMNvVXnSfH0IsDGllox4Y8',
                           'dt': '2021-06-27T21:26:21.233257+00:00',
                           'e': {'acdc': {'a': {'LEI': '78I9GKEFM361IFY3PIN0',
                                                'd': 'ELJ7Emhi0Bhxz3s7HyhZ45qcsgpvsT8p8pxwWkG362n3',
                                                'dt': '2021-06-27T21:26:21.233257+00:00',
                                                'i': 'EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm'},
                                          'd': 'EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N',
                                          'i': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                                          'ri': 'EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4',
                                          's': 'EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs',
                                          'v': 'ACDC10JSON000197_'},
                                 'anc': {'a': [{'d': 'EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4',
                                                'i': 'EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4',
                                                's': '0'}],
                                         'd': 'EJd2vLCnlcIb4ZLOhSHZOag4_FD-pxI96-r7e6_FT7CU',
                                         'i': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                                         'p': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                                         's': '1',
                                         't': 'ixn',
                                         'v': 'KERI10JSON00013a_'},
                                 'd': 'EKE374o9DAg9GIiFaDzk0g85sx2IV89cA8Iu4E_84Vug',
                                 'iss': {'d': 'EO83mwXWqiGxovpTXE6QQUBP05xkP9c1xc88xvMwkWWZ',
                                         'dt': '2021-06-27T21:26:21.233257+00:00',
                                         'i': 'EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N',
                                         'ri': 'EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4',
                                         's': '0',
                                         't': 'iss',
                                         'v': 'KERI10JSON0000ed_'}},
                           'i': 'EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm',
                           'p': '',
                           'q': {},
                           'r': '/ipex/grant',
                           't': 'exn',
                           'v': 'KERI10JSON000517_'}
        assert end == (b'-LAg4AACA-e-acdc-IABEBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N'
                       b'0AAAAAAAAAAAAAAAAAAAAAAAEO83mwXWqiGxovpTXE6QQUBP05xkP9c1xc88xvMw'
                       b'kWWZ-LAW5AACAA-e-iss-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAACEKZtbklUNPLO'
                       b'f9soxY6nLGAbqCDDfEMJRvJQfpcoYUdW-LAr5AACAA-e-anc-VAn-AABAAB8FdrC'
                       b'kf1kImQ8zRvKNWv2X_yElspb6bJ7eMg1B6Ly6wyLcDlfAkK5NnyB_qUaGVSilz63'
                       b'D2n4mJ8w_8AAo2wN-EAB0AAAAAAAAAAAAAAAAAAAAAAB1AAG2021-06-27T21c26'
                       b'c21d233257p00c00')
        sigs = ["AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"]

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc="",
            rec=["EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/grant", body=data)
        assert res.status_code == 404

        res = client.simulate_post(path="/identifiers/legal-entity/ipex/grant", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'attempt to send to unknown '
                                           'AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM',
                            'title': '400 Bad Request'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc="",
            rec=[verifier['i']]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/legal-entity/ipex/grant", body=data)
        assert res.status_code == 202
        assert res.json == exn.ked
        assert len(agent.exchanges) == 1
        assert len(agent.grants) == 1

        ims = eventing.messagize(serder=exn, sigers=[coring.Siger(qb64=sigs[0])])
        # Test sending embedded admit in multisig/exn message
        exn, end = exchanging.exchange(route="/multisig/exn",
                                       payload=dict(),
                                       sender=le['i'],
                                       embeds=dict(exn=ims),
                                       date=helping.nowIso8601())

        # Bad recipient
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=dict(exn=end.decode("utf-8")),
            rec=["EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/legal-entity/ipex/grant", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'attempt to send to unknown '
                                           'AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM',
                            'title': '400 Bad Request'}

        # Bad attachments
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=dict(bad=end.decode("utf-8")),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/legal-entity/ipex/grant", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'attachment missing for ACDC, unable to process request.',
                            'title': '400 Bad Request'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=dict(exn=end.decode("utf-8")),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/legal-entity/ipex/grant", body=data)

        assert res.status_code == 202
        assert len(agent.exchanges) == 3
        assert len(agent.grants) == 2


def test_granter(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        grants = decking.Deck()
        granter = agenting.Granter(hby=agent.hby, rgy=agent.rgy, agentHab=agent.agentHab, exc=agent.exc, grants=grants)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        deeds = doist.enter(doers=[granter])

        said = "EHwjDEsub6XT19ISLft1m1xMNvVXnSfH0IsDGllox4Y8"
        msg = dict(said=said)

        grants.append(msg)

        doist.recur(deeds=deeds)

        assert len(grants) == 1
