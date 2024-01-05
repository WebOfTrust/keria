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
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

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

        psalt0 = b'0123456789abcM00'
        op = helpers.createAid(client, "part0", psalt0)
        paid0 = op["response"]
        ppre0 = paid0['i']
        assert ppre0 == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        _, signers0 = helpers.incept(psalt0, "signify:aid", pidx=0)
        signer0 = signers0[0]

        psalt1 = b'0123456789abcM01'
        op = helpers.createAid(client, "part1", psalt1)
        paid1 = op["response"]
        ppre1 = paid1['i']
        assert ppre1 == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"
        _, signers1 = helpers.incept(psalt1, "signify:aid", pidx=0)
        signer1 = signers1[0]

        # Get their hab dicts
        m0 = client.simulate_get("/identifiers/part0").json
        m1 = client.simulate_get("/identifiers/part1").json

        assert m0["prefix"] == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        assert m1["prefix"] == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"

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
        assert serder.said == "ECJg1cFrp4G2ZHk8_ocsdoS1VuptVpaG9fLktBrwx1Fo"

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

        ims = eventing.messagize(serder=exn, sigers=[coring.Siger(qb64=sigs[0])])
        # Test sending embedded admit in multisig/exn message
        exn, end = exchanging.exchange(route="/multisig/exn",
                                       payload=dict(),
                                       sender=serder.pre,
                                       embeds=dict(exn=ims),
                                       dig=dig,
                                       date=helping.nowIso8601())

        # Bad recipient
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=end.decode("utf-8"),
            rec=["EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'attempt to send multisig message with non-group '
                                           'AID=EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                            'title': '400 Bad Request'}

        # Multi-sign the exn message
        sigs = [signer0.sign(ser=exn.raw, index=0).qb64, signer1.sign(ser=exn.raw, index=1).qb64]
        # Bad attachments
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=end.decode("utf-8"),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/multisig/ipex/admit", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'invalid exn request message '
                                           'EGJBe7LIp2x3PpeeG0utsj3ScTGR5_TA28622WUFYP8B',
                            'title': '400 Bad Request'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=end.decode("utf-8"),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/multisig/ipex/admit", body=data)

        # TODO: Fix test
        assert res.status_code == 400
        assert len(agent.exchanges) == 2
        assert len(agent.admits) == 0


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
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

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

        psalt0 = b'0123456789abcM00'
        op = helpers.createAid(client, "part0", psalt0)
        paid0 = op["response"]
        ppre0 = paid0['i']
        assert ppre0 == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        _, signers0 = helpers.incept(psalt0, "signify:aid", pidx=0)
        signer0 = signers0[0]

        psalt1 = b'0123456789abcM01'
        op = helpers.createAid(client, "part1", psalt1)
        paid1 = op["response"]
        ppre1 = paid1['i']
        assert ppre1 == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"
        _, signers1 = helpers.incept(psalt1, "signify:aid", pidx=0)
        signer1 = signers1[0]

        # Get their hab dicts
        m0 = client.simulate_get("/identifiers/part0").json
        m1 = client.simulate_get("/identifiers/part1").json

        assert m0["prefix"] == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        assert m1["prefix"] == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"

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
        assert serder.said == "ECJg1cFrp4G2ZHk8_ocsdoS1VuptVpaG9fLktBrwx1Fo"

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
            atc=end.decode("utf-8"),
            rec=["EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/legal-entity/ipex/grant", body=data)
        assert res.status_code == 400
        assert res.json == {'description': 'attempt to send multisig message with non-group '
                                           'AID=EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm',
                            'title': '400 Bad Request'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=end.decode("utf-8"),
            rec=[pre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/multisig/ipex/grant", body=data)

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
