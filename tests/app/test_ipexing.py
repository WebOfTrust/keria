# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ipe module

Testing credentialing endpoint in the Mark II Agent
"""
import json

import falcon
from falcon import testing
from hio.base import doing
from hio.help import decking
from keri.app import habbing, signing
from keri.core import eventing, coring, parsing, serdering
from keri.help import helping
from keri.kering import Roles
from keri.peer import exchanging
from keri.vc import proving
from keri.vdr import eventing as veventing

from keria.app import ipexing, aiding, agenting, credentialing
from keria.app.credentialing import CredentialResourceEnd
from keria.core import longrunning


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

        admitSerder, end = exchanging.exchange(route="/ipex/admit",
                                               payload=dict(),
                                               sender=pre,
                                               embeds=dict(),
                                               dig=dig,
                                               recipient=pre1,
                                               date=helping.nowIso8601())
        assert admitSerder.ked == {'a': {'i': 'EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm'},
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
            exn=admitSerder.ked,
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
            exn=admitSerder.ked,
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


def test_multisig_grant_admit(seeder, helpers):
    with (helpers.openKeria(salter=coring.Salter(raw=b'0123456789abcM00')) as (agency0, agent0, app0, client0), \
            helpers.openKeria(salter=coring.Salter(raw=b'0123456789abcM01')) as (agency1, agent1, app1, client1), \
            helpers.openKeria(salter=coring.Salter(raw=b'0123456789abcM02')) as (hagency0, hagent0, happ0, hclient0), \
            helpers.openKeria(salter=coring.Salter(raw=b'0123456789abcM03')) as (hagency1, hagent1, happ1, hclient1)):

        tock = 0.03125
        doist = doing.Doist(tock=tock, real=True)
        deeds = doist.enter(doers=[agent0, hagent0, agent1, hagent1])

        # Seed database with credential schema
        for agent in [agent0, agent1, hagent0, hagent1]:
            seeder.seedSchema(agent.hby.db)

        for app in [app0, app1, happ0, happ1]:
            # Register the GRANT and ADMIT endpoints
            grantAnd = ipexing.IpexGrantCollectionEnd()
            app.add_route("/identifiers/{name}/ipex/grant", grantAnd)
            admitEnd = ipexing.IpexAdmitCollectionEnd()
            app.add_route("/identifiers/{name}/ipex/admit", admitEnd)

            # Register the Identifier endpoints
            end = aiding.IdentifierCollectionEnd()
            app.add_route("/identifiers", end)
            aidEnd = aiding.IdentifierResourceEnd()
            app.add_route("/identifiers/{name}", aidEnd)

            # Register the Credential endpoints
            registryEnd = credentialing.RegistryCollectionEnd(aidEnd)
            app.add_route("/identifiers/{name}/registries", registryEnd)
            credEnd = credentialing.CredentialCollectionEnd(aidEnd)
            app.add_route("/identifiers/{name}/credentials", credEnd)
            opEnd = longrunning.OperationResourceEnd()
            app.add_route("/operations/{name}", opEnd)

            endRolesEnd = aiding.EndRoleCollectionEnd()
            app.add_route("/identifiers/{name}/endroles", endRolesEnd)

        # Create Issuer Participant 0
        ipsalt0 = b'0123456789abcM00'
        op = helpers.createAid(client0, "issuerParticipant0", ipsalt0)
        ipaid0 = op["response"]
        ippre0 = ipaid0['i']
        assert ippre0 == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        _, signers0 = helpers.incept(ipsalt0, "signify:aid", pidx=0)
        issuerSigner0 = signers0[0]

        # Create Issuer Participant 1
        ipsalt1 = b'0123456789abcM01'
        op = helpers.createAid(client1, "issuerParticipant1", ipsalt1)
        ipaid1 = op["response"]
        ippre1 = ipaid1['i']
        assert ippre1 == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"
        _, signers1 = helpers.incept(ipsalt1, "signify:aid", pidx=0)
        issuerSigner1 = signers1[0]

        # Get their hab dicts
        ip0 = client0.simulate_get("/identifiers/issuerParticipant0").json
        ip1 = client1.simulate_get("/identifiers/issuerParticipant1").json

        assert ip0["prefix"] == ippre0
        assert ip1["prefix"] == ippre1

        # Introduce the participants to each other
        ip0Hab = agent0.hby.habByName("issuerParticipant0")
        ims = ip0Hab.replyToOobi(ip0Hab.pre, role=Roles.agent)
        agent1.parser.parse(ims=bytearray(ims))
        ip1Hab = agent1.hby.habByName("issuerParticipant1")
        ims = ip1Hab.replyToOobi(ip1Hab.pre, role=Roles.agent)
        agent0.parser.parse(ims=bytearray(ims))

        ikeys = [ip0['state']['k'][0], ip1['state']['k'][0]]
        ndigs = [ip0['state']['n'][0], ip1['state']['n'][0]]

        # Create the Issuer mutlsig inception event
        serder = eventing.incept(keys=ikeys,
                                 isith="2",
                                 nsith="2",
                                 ndigs=ndigs,
                                 code=coring.MtrDex.Blake3_256,
                                 toad=0,
                                 wits=[])
        issuerPre = serder.said
        assert issuerPre == "ECJg1cFrp4G2ZHk8_ocsdoS1VuptVpaG9fLktBrwx1Fo"

        sigers = [issuerSigner0.sign(ser=serder.raw, index=0).qb64, issuerSigner1.sign(ser=serder.raw, index=1).qb64]
        states = nstates = [ip0['state'], ip1['state']]

        body = {
            'name': 'issuer',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": ip0,
                "keys": ikeys,
                "ndigs": ndigs
            }
        }

        res = client0.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        body = {
            'name': 'issuer',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": ip1,
                "keys": ikeys,
                "ndigs": ndigs
            }
        }
        res = client1.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        while not agent0.counselor.complete(prefixer=coring.Prefixer(qb64=serder.pre), seqner=coring.Seqner(sn=0)):
            doist.recur(deeds=deeds)

        assert agent1.counselor.complete(prefixer=coring.Prefixer(qb64=serder.pre), seqner=coring.Seqner(sn=0)) is True

        issuer = client0.simulate_get("/identifiers/issuer").json
        assert issuer['prefix'] == issuerPre

        # Lets add both endroles for Issuer multisig
        rpy = helpers.endrole(issuerPre, agent0.agentHab.pre)
        sigs = [issuerSigner0.sign(ser=rpy.raw, index=0).qb64, issuerSigner1.sign(ser=rpy.raw, index=1).qb64]
        body = dict(rpy=rpy.ked, sigs=sigs)

        res = client0.simulate_post(path=f"/identifiers/issuer/endroles", json=body)
        assert res.status_code == 202
        res = client1.simulate_post(path=f"/identifiers/issuer/endroles", json=body)
        assert res.status_code == 202

        # Create Holder Participant 0
        hsalt0 = b'0123456789abcM02'
        op = helpers.createAid(hclient0, "holderParticipant0", hsalt0)
        haid0 = op["response"]
        hpre0 = haid0['i']
        assert hpre0 == "EFevdfJNyE2FPQ-nJLXRamh7-4rdRBZAmroHMGSbuI99"
        _, signers0 = helpers.incept(hsalt0, "signify:aid", pidx=0)
        holderSigner0 = signers0[0]

        # Create Holder Participant 1
        hsalt1 = b'0123456789abcM03'
        op = helpers.createAid(hclient1, "holderParticipant1", hsalt1)
        haid1 = op["response"]
        hpre1 = haid1['i']
        assert hpre1 == "EIA1PcKQkcW6mvs2kVwVpvaf6SMuBHLMCrx57WPW6UPO"
        _, signers1 = helpers.incept(hsalt1, "signify:aid", pidx=0)
        holderSigner1 = signers1[0]

        # Get their hab dicts
        hp0 = hclient0.simulate_get("/identifiers/holderParticipant0").json
        hp1 = hclient1.simulate_get("/identifiers/holderParticipant1").json

        assert hp0["prefix"] == hpre0
        assert hp1["prefix"] == hpre1

        # Introduce the participants to each other
        h0Hab = hagent0.hby.habByName("holderParticipant0")
        ims = h0Hab.replyToOobi(h0Hab.pre, role=Roles.agent)
        hagent1.parser.parse(ims=bytearray(ims))
        h1Hab = hagent1.hby.habByName("holderParticipant1")
        ims = h1Hab.replyToOobi(h1Hab.pre, role=Roles.agent)
        hagent0.parser.parse(ims=bytearray(ims))

        keys = [hp0['state']['k'][0], hp1['state']['k'][0]]
        ndigs = [hp0['state']['n'][0], hp1['state']['n'][0]]

        # Create the mutlsig inception event
        serder = eventing.incept(keys=keys,
                                 isith="2",
                                 nsith="2",
                                 ndigs=ndigs,
                                 code=coring.MtrDex.Blake3_256,
                                 toad=0,
                                 wits=[])
        holderPre = serder.said
        assert holderPre == "EEJCrHnZmQwEJe8W8K1AOtB7XPTN3dBT8pC7tx5AyBmM"

        # Send in all signatures as if we are joining the inception event
        sigers = [holderSigner0.sign(ser=serder.raw, index=0).qb64, holderSigner1.sign(ser=serder.raw, index=1).qb64]
        states = nstates = [hp0['state'], hp1['state']]

        body = {
            'name': 'holder',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": hp0,
                "keys": keys,
                "ndigs": ndigs
            }
        }

        res = hclient0.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        body = {
            'name': 'holder',
            'icp': serder.ked,
            'sigs': sigers,
            "smids": states,
            "rmids": nstates,
            'group': {
                "mhab": hp1,
                "keys": keys,
                "ndigs": ndigs
            }
        }

        res = hclient1.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        while not hagent0.counselor.complete(prefixer=coring.Prefixer(qb64=serder.pre), seqner=coring.Seqner(sn=0)):
            doist.recur(deeds=deeds)

        assert hagent1.counselor.complete(prefixer=coring.Prefixer(qb64=serder.pre), seqner=coring.Seqner(sn=0)) is True
        holder = hclient0.simulate_get("/identifiers/holder").json
        assert holder['prefix'] == holderPre

        # Lets add both endroles for Issuer multisig
        rpy = helpers.endrole(holderPre, hagent0.agentHab.pre)
        sigs = [holderSigner0.sign(ser=rpy.raw, index=0).qb64, holderSigner1.sign(ser=rpy.raw, index=1).qb64]
        body = dict(rpy=rpy.ked, sigs=sigs)

        res = hclient0.simulate_post(path=f"/identifiers/holder/endroles", json=body)
        assert res.status_code == 202
        res = hclient1.simulate_post(path=f"/identifiers/holder/endroles", json=body)
        assert res.status_code == 202

        # Introduce the multisig AIDs to each other
        for name, agent in [("issuer", agent0), ("issuerParticipant0", agent0), ("issuerParticipant1", agent1)]:
            issuerHab = agent.hby.habByName(name)
            ims = issuerHab.replyToOobi(issuerHab.pre, role=Roles.agent)
            hagent0.parser.parse(ims=bytearray(ims))
            hagent1.parser.parse(ims=ims)

            while issuerHab.pre not in hagent0.hby.kevers:
                doist.recur(deeds=deeds)

            assert issuerHab.pre in hagent1.hby.kevers

        for name, agent in [("holder", hagent0), ("holderParticipant0", hagent0), ("holderParticipant1", hagent1)]:
            holderHab = agent.hby.habByName(name)
            ims = holderHab.replyToOobi(holderHab.pre, role=Roles.agent)
            agent0.parser.parse(ims=bytearray(ims))
            agent1.parser.parse(ims=ims)

            while holderHab.pre not in agent0.hby.kevers:
                doist.recur(deeds=deeds)

            assert holderHab.pre in agent1.hby.kevers

        # Create credential registry
        nonce = coring.randomNonce()
        regser = veventing.incept(issuerPre,
                                  baks=[],
                                  toad="0",
                                  nonce=nonce,
                                  cnfg=[eventing.TraitCodex.NoBackers],
                                  code=coring.MtrDex.Blake3_256)

        anchor = dict(i=regser.ked['i'], s=regser.ked["s"], d=regser.said)

        interact = eventing.interact(pre=issuerPre, dig=issuerPre, sn=1, data=[anchor])
        sigs = [issuerSigner0.sign(ser=interact.raw, index=0).qb64, issuerSigner1.sign(ser=interact.raw, index=1).qb64]
        group = {
            "mhab": ip0,
            "keys": ikeys
        }
        body = dict(name="credentialRegistry", alias="issuer", vcp=regser.ked, ixn=interact.ked, sigs=sigs, group=group)
        result = client0.simulate_post(path="/identifiers/issuer/registries", body=json.dumps(body).encode("utf-8"))
        op = result.json
        assert op["done"] is True

        group = {
            "mhab": ip1,
            "keys": ikeys
        }
        body = dict(name="credentialRegistry", alias="issuer", vcp=regser.ked, ixn=interact.ked, sigs=sigs, group=group)
        result = client1.simulate_post(path="/identifiers/issuer/registries", body=json.dumps(body).encode("utf-8"))
        op = result.json
        metadata = op["metadata"]

        regk = regser.pre
        assert op["done"] is True
        assert metadata["anchor"] == anchor
        assert result.status == falcon.HTTP_202

        # Wait for Agent 0 to resolve Registry
        while regk not in agent0.tvy.tevers:
            doist.recur(deeds=deeds)

        # Verify Agent 1 has also resolved the Registry
        assert regk in agent1.tvy.tevers

        # Create a credential.
        dt = helping.nowIso8601()
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        data = dict(LEI="254900DA0GOGCFVWB618", dt=dt)
        creder = proving.credential(issuer=issuerPre,
                                    schema=schema,
                                    recipient=holderPre,
                                    data=data,
                                    source={},
                                    status=regk)

        # Create the issuance event from the credential SAID and the registry SAID
        regser = veventing.issue(vcdig=creder.said, regk=regk, dt=dt)

        anchor = dict(i=regser.ked['i'], s=regser.ked["s"], d=regser.said)
        interact = eventing.interact(pre=issuerPre, dig=interact.said, sn=2, data=[anchor])
        sigs = [issuerSigner0.sign(ser=interact.raw, index=0).qb64, issuerSigner1.sign(ser=interact.raw, index=1).qb64]

        pather = coring.Pather(path=[])

        # Submit the Credential to Agent 0
        body = dict(
            iss=regser.ked,
            ixn=interact.ked,
            sigs=sigs,
            acdc=creder.sad,
            path=pather.qb64,
            group={
                "mhab": ip0,
                "keys": ikeys
            }
        )

        result = client0.simulate_post(path="/identifiers/issuer/credentials", body=json.dumps(body).encode("utf-8"))
        assert result.status == falcon.HTTP_200

        # Submit the Credential to Agent 1
        body = dict(
            iss=regser.ked,
            ixn=interact.ked,
            sigs=sigs,
            acdc=creder.sad,
            path=pather.qb64,
            group={
                "mhab": ip1,
                "keys": ikeys
            }
        )

        result = client1.simulate_post(path="/identifiers/issuer/credentials", body=json.dumps(body).encode("utf-8"))
        assert result.status == falcon.HTTP_200

        # Wait for Agent 0 to resolve the credential
        while not agent0.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        # Verify Agent 1 has resolved the credential
        assert agent1.credentialer.complete(creder.said) is True

        # Now we need to GRANT the message to the HOLDER
        creder, prefixer, seqner, saider = agent0.rgy.reger.cloneCred(said=creder.said)
        acdc = signing.serialize(creder, prefixer, seqner, saider)

        iss = next(agent0.rgy.reger.clonePreIter(pre=creder.said))
        anc = next(agent0.hby.db.clonePreIter(pre=issuerPre, fn=1))
        embeds = dict(
            acdc=acdc,
            iss=iss,
            anc=anc
        )

        grantSerder, end = exchanging.exchange(route="/ipex/grant",
                                               payload=dict(),
                                               sender=issuerPre,
                                               embeds=embeds,
                                               recipient=holderPre,
                                               date=helping.nowIso8601())

        # Sign from both participants
        grantSigers = [issuerSigner0.sign(ser=grantSerder.raw, index=0),
                       issuerSigner1.sign(ser=grantSerder.raw, index=1)]
        seal = eventing.SealEvent(i=issuerPre, s="0", d=issuerPre)  # Seal made easier by issuer being at inception
        ims = eventing.messagize(serder=grantSerder, sigers=grantSigers, seal=seal)
        ims += end

        # Package up the GRANT into a multisig/exn from participant 0 to send to participant 1
        multiExnSerder0, end = exchanging.exchange(route="/multisig/exn",
                                                   payload=dict(),
                                                   sender=ippre0,
                                                   embeds=dict(exn=ims),
                                                   date=helping.nowIso8601())

        body = dict(
            exn=multiExnSerder0.ked,
            sigs=[issuerSigner0.sign(ser=multiExnSerder0.raw, index=0).qb64],
            atc=end.decode("utf-8"),
            rec=[ippre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = client0.simulate_post(path="/identifiers/issuer/ipex/grant", body=data)

        assert res.status_code == 202

        # Package up the GRANT into a multisig/exn from participant 1 to send to participant 0
        multiExnSerder, end = exchanging.exchange(route="/multisig/exn",
                                                  payload=dict(),
                                                  sender=ippre1,
                                                  embeds=dict(exn=ims),
                                                  date=helping.nowIso8601())

        body = dict(
            exn=multiExnSerder.ked,
            sigs=[issuerSigner1.sign(ser=multiExnSerder.raw, index=0).qb64],
            atc=end.decode("utf-8"),
            rec=[ippre0]
        )

        data = json.dumps(body).encode("utf-8")
        res = client1.simulate_post(path="/identifiers/issuer/ipex/grant", body=data)
        assert res.status_code == 202

        # Wait until the GRANT has been persisted by Agent0
        while agent0.exc.complete(said=grantSerder.said) is not True:
            doist.recur(deeds=deeds)

        # Make sure Agent 1 persisted the event too
        assert agent1.exc.complete(said=grantSerder.said) is True

        # Now to get the GRANT event parsed and saved by the holder.
        # This would normally be acheived by Agent0 sending over a transport, but we aren't launching them in unit tests
        exn, pathed = exchanging.cloneMessage(agent0.hby, multiExnSerder0.said)
        assert exn is not None

        grant = serdering.SerderKERI(sad=exn.ked['e']['exn'])
        ims = bytearray(grant.raw) + pathed['exn']
        hagent0.hby.psr.parseOne(ims=bytearray(ims))
        hagent1.hby.psr.parseOne(ims=ims)

        # Ensure the grant message was received by the holder's agents
        assert hagent0.hby.db.exns.get(keys=(grant.said,)) is not None
        assert hagent1.hby.db.exns.get(keys=(grant.said,)) is not None

        # Now lets admit this sucker
        admitSerder, end = exchanging.exchange(route="/ipex/admit",
                                               payload=dict(),
                                               sender=holderPre,
                                               embeds=dict(),
                                               dig=grant.said,
                                               recipient=issuerPre,
                                               date=helping.nowIso8601())

        admitSigers = [holderSigner0.sign(ser=admitSerder.raw, index=0),
                       holderSigner1.sign(ser=admitSerder.raw, index=1)]
        seal = eventing.SealEvent(i=holderPre, s="0", d=holderPre)  # Seal made easy by holder being at inception
        ims = eventing.messagize(serder=admitSerder, sigers=admitSigers, seal=seal)

        # Package up the ADMIT into a multisig/exn from participant 0 to send to participant 1
        multiExnSerder0, end = exchanging.exchange(route="/multisig/exn",
                                                   payload=dict(),
                                                   sender=hpre0,
                                                   embeds=dict(exn=ims),
                                                   date=helping.nowIso8601())

        body = dict(
            exn=multiExnSerder0.ked,
            sigs=[holderSigner0.sign(ser=multiExnSerder0.raw, index=0).qb64],
            atc=end.decode("utf-8"),
            rec=[hpre1]
        )

        data = json.dumps(body).encode("utf-8")
        res = hclient0.simulate_post(path="/identifiers/holder/ipex/admit", body=data)

        assert res.status_code == 202

        # Package up the ADMIT into a multisig/exn from participant 1 to send to participant 0
        multiExnSerder, end = exchanging.exchange(route="/multisig/exn",
                                                  payload=dict(),
                                                  sender=hpre1,
                                                  embeds=dict(exn=ims),
                                                  date=helping.nowIso8601())

        body = dict(
            exn=multiExnSerder.ked,
            sigs=[holderSigner1.sign(ser=multiExnSerder.raw, index=0).qb64],
            atc=end.decode("utf-8"),
            rec=[hpre0]
        )

        data = json.dumps(body).encode("utf-8")
        res = hclient1.simulate_post(path="/identifiers/holder/ipex/admit", body=data)
        assert res.status_code == 202

        # Wait until the ADMIT has been persisted by Hagent0
        while hagent0.exc.complete(said=admitSerder.said) is not True:
            doist.recur(deeds=deeds)

        # Make sure Agent 1 persisted the event too
        assert hagent1.exc.complete(said=admitSerder.said) is True

        # Have to parse the TEL events and their anchoring events, these would normally be streamed over
        for msg in agent0.hby.db.clonePreIter(pre=issuerPre):  # Issuer KEL
            hagent0.parser.parse(ims=bytearray(msg))
            hagent1.parser.parse(ims=msg)
        for msg in agent0.rgy.reger.clonePreIter(pre=regk):  # Registry TEL Event
            hagent0.parser.parse(ims=bytearray(msg))
            hagent1.parser.parse(ims=msg)
        for msg in agent0.rgy.reger.clonePreIter(pre=creder.said):  # Issuance TEL Event
            hagent0.parser.parse(ims=bytearray(msg))
            hagent1.parser.parse(ims=msg)

        # Wait until credential is persisted
        while hagent0.rgy.reger.saved.get(keys=(creder.said,)) is None:
            doist.recur(deeds=deeds)

        # Ensure that the credential has been persisted by both agents
        assert hagent1.rgy.reger.saved.get(keys=(creder.said,)) is not None


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
