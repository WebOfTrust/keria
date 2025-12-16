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
        (end, *_) = app._router.find("/identifiers/NAME/ipex/apply")
        assert isinstance(end, ipexing.IpexApplyCollectionEnd)
        (end, *_) = app._router.find("/identifiers/NAME/ipex/offer")
        assert isinstance(end, ipexing.IpexOfferCollectionEnd)
        (end, *_) = app._router.find("/identifiers/NAME/ipex/agree")
        assert isinstance(end, ipexing.IpexAgreeCollectionEnd)


def test_ipex_admit(helpers, mockHelpingNowIso8601):
    with helpers.openKeria() as (agency, agent, app, client):
        admitEnd = ipexing.IpexAdmitCollectionEnd()
        app.add_route("/identifiers/{name}/ipex/admit", admitEnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid["i"]
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        dig = "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT"

        salt2 = b"0123456789abcdeg"
        op = helpers.createAid(client, "recp", salt2)
        aid1 = op["response"]
        pre1 = aid1["i"]
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"

        admitSerder, end = exchanging.exchange(
            route="/ipex/admit",
            payload=dict(),
            sender=pre,
            embeds=dict(),
            dig=dig,
            recipient=pre1,
            date=helping.nowIso8601(),
        )
        assert admitSerder.ked == {
            "a": {"i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"},
            "d": "EEsFX0BFd58i84TBnq4S4Z_5XZuuz1HGtDC5Hb7NdU1P",
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "e": {},
            "i": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
            "rp": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
            "p": "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT",
            "q": {},
            "r": "/ipex/admit",
            "t": "exn",
            "v": "KERI10JSON000171_",
        }
        assert end == b""
        sigs = [
            "AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"
        ]

        # Test with unknown recipient - create message with unknown recipient
        unknownRecipient = "EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"
        unknownAdmitSerder, _ = exchanging.exchange(
            route="/ipex/admit",
            payload=dict(),
            sender=pre,
            embeds=dict(),
            dig=dig,
            recipient=unknownRecipient,
            date=helping.nowIso8601(),
        )

        body = dict(
            exn=unknownAdmitSerder.ked,
            sigs=sigs,
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        assert res.status_code == 400
        assert res.json == {
            "description": "attempt to send to unknown "
            "AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM",
            "title": "400 Bad Request",
        }

        # Test with valid recipient
        body = dict(exn=admitSerder.ked, sigs=sigs)

        # Bad Sender
        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/BAD/ipex/admit", body=data)
        assert res.status_code == 404

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/admit", body=data)

        assert res.status_code == 200
        assert len(agent.exchanges) == 1
        assert len(agent.admits) == 1


def test_ipex_grant(helpers, mockHelpingNowIso8601, seeder):
    salt = b"0123456789abcdef"

    with (
        helpers.openKeria() as (agency, agent, app, client),
        habbing.openHab(name="issuer", salt=salt, temp=True) as (issuerHby, issuerHab),
        helpers.withIssuer(name="issuer", hby=issuerHby) as issuer,
    ):
        client = testing.TestClient(app)
        seeder.seedSchema(agent.hby.db)
        seeder.seedSchema(issuerHby.db)

        grantAnd = ipexing.IpexGrantCollectionEnd()
        app.add_route("/identifiers/{name}/ipex/grant", grantAnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

        salt2 = b"0123456789abcdeg"
        op = helpers.createAid(client, "legal-entity", salt2)
        le = op["response"]
        pre1 = le["i"]
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"

        salt3 = b"0123456789abc123"
        op = helpers.createAid(client, "verifier", salt3)
        verifier = op["response"]
        pre1 = verifier["i"]
        assert pre1 == "EEtaMHCGi83N3IJN05DRDhkpIo5S03LOX5_8IgdvMaVq"

        psalt0 = b"0123456789abcM00"
        op = helpers.createAid(client, "part0", psalt0)
        paid0 = op["response"]
        ppre0 = paid0["i"]
        assert ppre0 == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        _, signers0 = helpers.incept(psalt0, "signify:aid", pidx=0)
        signer0 = signers0[0]

        psalt1 = b"0123456789abcM01"
        op = helpers.createAid(client, "part1", psalt1)
        paid1 = op["response"]
        ppre1 = paid1["i"]
        assert ppre1 == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"
        _, signers1 = helpers.incept(psalt1, "signify:aid", pidx=0)
        signer1 = signers1[0]

        # Get their hab dicts
        m0 = client.simulate_get("/identifiers/part0").json
        m1 = client.simulate_get("/identifiers/part1").json

        assert m0["prefix"] == "EI0XLIyKcSFFXi14HZGnLxU24BSsX78ZmZ_w3-N0fRSy"
        assert m1["prefix"] == "EGFFaJOT9HV3jqxk6PaIrLJQz2qQK2TnqbhjwiIij2m8"

        keys = [m0["state"]["k"][0], m1["state"]["k"][0]]
        ndigs = [m0["state"]["n"][0], m1["state"]["n"][0]]

        # Create the mutlsig inception event
        serder = eventing.incept(
            keys=keys,
            isith="2",
            nsith="2",
            ndigs=ndigs,
            code=coring.MtrDex.Blake3_256,
            toad=0,
            wits=[],
        )
        assert serder.said == "ECJg1cFrp4G2ZHk8_ocsdoS1VuptVpaG9fLktBrwx1Fo"

        # Send in all signatures as if we are joining the inception event
        sigers = [
            signer0.sign(ser=serder.raw, index=0).qb64,
            signer1.sign(ser=serder.raw, index=1).qb64,
        ]
        states = [m0["state"], m1["state"]]
        smids = rmids = [state["i"] for state in states if "i" in state]

        body = {
            "name": "multisig",
            "icp": serder.ked,
            "sigs": sigers,
            "smids": smids,
            "rmids": rmids,
            "group": {"mhab": m0, "keys": keys, "ndigs": ndigs},
        }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 202

        # Lets issue a QVI credential to the QVI
        issuer.createRegistry(issuerHab.pre, name="issuer")
        qvisaid = issuer.issueQVIvLEI(
            "issuer", issuerHab, le["i"], "78I9GKEFM361IFY3PIN0"
        )

        ims = CredentialResourceEnd.outputCred(issuer.hby, issuer.rgy, qvisaid)

        agent.parser.parse(ims)

        creder, prefixer, seqner, saider = agent.rgy.reger.cloneCred(said=qvisaid)
        acdc = signing.serialize(creder, prefixer, seqner, saider)

        iss = next(agent.rgy.reger.clonePreIter(pre=creder.said))
        anc = next(agent.hby.db.clonePreIter(pre=issuerHab.pre, fn=1))
        embeds = dict(acdc=acdc, iss=iss, anc=anc)

        exn, end = exchanging.exchange(
            route="/ipex/grant",
            payload=dict(),
            sender=le["i"],
            embeds=embeds,
            recipient=verifier["i"],
            date=helping.nowIso8601(),
        )
        assert exn.ked == {
            "a": {"i": "EEtaMHCGi83N3IJN05DRDhkpIo5S03LOX5_8IgdvMaVq"},
            "d": "ELkQART3yXFd8C6ImzGyqlDrgVUDtCfh1Goqr1PCbi9r",
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "e": {
                "acdc": {
                    "a": {
                        "LEI": "78I9GKEFM361IFY3PIN0",
                        "d": "ELJ7Emhi0Bhxz3s7HyhZ45qcsgpvsT8p8pxwWkG362n3",
                        "dt": "2021-06-27T21:26:21.233257+00:00",
                        "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
                    },
                    "d": "EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N",
                    "i": "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze",
                    "ri": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
                    "s": "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
                    "v": "ACDC10JSON000197_",
                },
                "anc": {
                    "a": [
                        {
                            "d": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
                            "i": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
                            "s": "0",
                        }
                    ],
                    "d": "EJd2vLCnlcIb4ZLOhSHZOag4_FD-pxI96-r7e6_FT7CU",
                    "i": "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze",
                    "p": "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze",
                    "s": "1",
                    "t": "ixn",
                    "v": "KERI10JSON00013a_",
                },
                "d": "EKE374o9DAg9GIiFaDzk0g85sx2IV89cA8Iu4E_84Vug",
                "iss": {
                    "d": "EO83mwXWqiGxovpTXE6QQUBP05xkP9c1xc88xvMwkWWZ",
                    "dt": "2021-06-27T21:26:21.233257+00:00",
                    "i": "EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N",
                    "ri": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
                    "s": "0",
                    "t": "iss",
                    "v": "KERI10JSON0000ed_",
                },
            },
            "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
            "rp": "EEtaMHCGi83N3IJN05DRDhkpIo5S03LOX5_8IgdvMaVq",
            "p": "",
            "q": {},
            "r": "/ipex/grant",
            "t": "exn",
            "v": "KERI10JSON00054b_",
        }
        assert end == (
            b"-LAg4AACA-e-acdc-IABEBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N"
            b"0AAAAAAAAAAAAAAAAAAAAAAAEO83mwXWqiGxovpTXE6QQUBP05xkP9c1xc88xvMw"
            b"kWWZ-LAW5AACAA-e-iss-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAACEKZtbklUNPLO"
            b"f9soxY6nLGAbqCDDfEMJRvJQfpcoYUdW-LAr5AACAA-e-anc-VAn-AABAAB8FdrC"
            b"kf1kImQ8zRvKNWv2X_yElspb6bJ7eMg1B6Ly6wyLcDlfAkK5NnyB_qUaGVSilz63"
            b"D2n4mJ8w_8AAo2wN-EAB0AAAAAAAAAAAAAAAAAAAAAAB1AAG2021-06-27T21c26"
            b"c21d233257p00c00"
        )
        sigs = [
            "AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"
        ]

        # Test with unknown recipient
        unknownRecipient = "EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"
        unknownExn, _ = exchanging.exchange(
            route="/ipex/grant",
            payload=dict(),
            sender=le["i"],
            embeds=embeds,
            recipient=unknownRecipient,
            date=helping.nowIso8601(),
        )

        body = dict(
            exn=unknownExn.ked,
            sigs=sigs,
            atc=end.decode("utf-8"),
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/grant", body=data)
        assert res.status_code == 404

        res = client.simulate_post(
            path="/identifiers/legal-entity/ipex/grant", body=data
        )
        assert res.status_code == 400
        assert res.json == {
            "description": "attempt to send to unknown "
            "AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM",
            "title": "400 Bad Request",
        }

        body = dict(exn=exn.ked, sigs=sigs, atc=end.decode("utf-8"))

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(
            path="/identifiers/legal-entity/ipex/grant", body=data
        )
        assert res.status_code == 200
        assert res.json == {
            "done": False,
            "error": None,
            "metadata": {"said": "ELkQART3yXFd8C6ImzGyqlDrgVUDtCfh1Goqr1PCbi9r"},
            "name": "exchange.ELkQART3yXFd8C6ImzGyqlDrgVUDtCfh1Goqr1PCbi9r",
            "response": None,
        }
        assert len(agent.exchanges) == 1
        assert len(agent.grants) == 1


def test_granter(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        grants = decking.Deck()
        granter = agenting.Granter(
            hby=agent.hby,
            rgy=agent.rgy,
            agentHab=agent.agentHab,
            exc=agent.exc,
            grants=grants,
        )

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        deeds = doist.enter(doers=[granter])

        said = "EHwjDEsub6XT19ISLft1m1xMNvVXnSfH0IsDGllox4Y8"
        msg = dict(said=said)

        grants.append(msg)

        doist.recur(deeds=deeds)

        assert len(grants) == 1


def test_ipex_apply(helpers, mockHelpingNowIso8601):
    with helpers.openKeria() as (_, agent, app, client):
        applyEnd = ipexing.IpexApplyCollectionEnd()
        app.add_route("/identifiers/{name}/ipex/apply", applyEnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid["i"]
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        salt2 = b"0123456789abcdeg"
        op = helpers.createAid(client, "recp", salt2)
        aid1 = op["response"]
        pre1 = aid1["i"]
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"

        applySerder, end = exchanging.exchange(
            route="/ipex/apply",
            payload={
                "m": "Applying for a credential",
                "s": "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                "a": {"LEI": "78I9GKEFM361IFY3PIN0"},
            },
            sender=pre,
            embeds=dict(),
            recipient=pre1,
            date=helping.nowIso8601(),
        )
        assert applySerder.ked == {
            "a": {
                "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
                "m": "Applying for a credential",
                "s": "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                "a": {"LEI": "78I9GKEFM361IFY3PIN0"},
            },
            "d": "EPAThHL_ExMdhQoLTxsMWdsDo-aunDFZPkK_UKlCVe2d",
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "e": {},
            "i": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
            "rp": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
            "p": "",
            "q": {},
            "r": "/ipex/apply",
            "t": "exn",
            "v": "KERI10JSON0001bb_",
        }
        assert end == b""
        sigs = [
            "AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"
        ]

        # Test with unknown recipient
        unknownRecipient = "EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"
        unknownApplySerder, _ = exchanging.exchange(
            route="/ipex/apply",
            payload=dict(),
            sender=pre,
            embeds=dict(),
            recipient=unknownRecipient,
            date=helping.nowIso8601(),
        )

        body = dict(
            exn=unknownApplySerder.ked,
            sigs=sigs,
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/apply", body=data)

        assert res.status_code == 400
        assert res.json == {
            "description": "attempt to send to unknown "
            "AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM",
            "title": "400 Bad Request",
        }

        body = dict(exn=applySerder.ked, sigs=sigs)

        # Bad Sender
        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/BAD/ipex/apply", body=data)
        assert res.status_code == 404
        assert res.json == {
            "description": "BAD is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/apply", body=data)
        assert res.json == {
            "done": False,
            "error": None,
            "metadata": {"said": "EPAThHL_ExMdhQoLTxsMWdsDo-aunDFZPkK_UKlCVe2d"},
            "name": "exchange.EPAThHL_ExMdhQoLTxsMWdsDo-aunDFZPkK_UKlCVe2d",
            "response": None,
        }

        assert res.status_code == 200
        assert len(agent.exchanges) == 1


def test_ipex_offer(helpers, mockHelpingNowIso8601):
    with helpers.openKeria() as (_, agent, app, client):
        offerEnd = ipexing.IpexOfferCollectionEnd()
        app.add_route("/identifiers/{name}/ipex/offer", offerEnd)

        end0 = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end0)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid["i"]
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        salt2 = b"0123456789abcdeg"
        op = helpers.createAid(client, "recp", salt2)
        aid1 = op["response"]
        pre1 = aid1["i"]
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"

        # This should be a metadata ACDC in reality
        acdc = b'{"v":"ACDC10JSON000197_","d":"EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N","i":"EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze","ri":"EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4","s":"EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs","a":{"d":"ELJ7Emhi0Bhxz3s7HyhZ45qcsgpvsT8p8pxwWkG362n3","dt":"2021-06-27T21:26:21.233257+00:00","i":"EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm","LEI":"78I9GKEFM361IFY3PIN0"}}'
        embeds = dict(acdc=acdc)

        # First an offer initiated by discloser (no apply)
        offer0Serder, end0 = exchanging.exchange(
            route="/ipex/offer",
            payload={"m": "Offering this"},
            sender=pre,
            embeds=embeds,
            recipient=pre1,
            date=helping.nowIso8601(),
        )
        assert offer0Serder.ked == {
            "a": {
                "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
                "m": "Offering this",
            },
            "d": "ECa9XU2648ryO8PXKEcWkS7V-hvpj86Nh3rjGv93g6jT",
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "e": {
                "acdc": {
                    "a": {
                        "d": "ELJ7Emhi0Bhxz3s7HyhZ45qcsgpvsT8p8pxwWkG362n3",
                        "dt": "2021-06-27T21:26:21.233257+00:00",
                        "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
                        "LEI": "78I9GKEFM361IFY3PIN0",
                    },
                    "d": "EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N",
                    "i": "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze",
                    "ri": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
                    "s": "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
                    "v": "ACDC10JSON000197_",
                },
                "d": "EEcYZMP-zilz2w1w2hEFm6tF0eaX_1KaPEWhNfY3kf8i",
            },
            "i": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
            "rp": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
            "p": "",
            "q": {},
            "r": "/ipex/offer",
            "t": "exn",
            "v": "KERI10JSON00032a_",
        }
        assert end0 == b""
        sigs = [
            "AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"
        ]

        # Test with unknown recipient
        unknownRecipient = "EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"
        unknownOfferSerder, _ = exchanging.exchange(
            route="/ipex/offer",
            payload=dict(),
            sender=pre,
            embeds=embeds,
            recipient=unknownRecipient,
            date=helping.nowIso8601(),
        )

        body = dict(
            exn=unknownOfferSerder.ked,
            sigs=sigs,
            atc=end0.decode("utf-8"),
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/offer", body=data)

        assert res.status_code == 400
        assert res.json == {
            "description": "attempt to send to unknown "
            "AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM",
            "title": "400 Bad Request",
        }

        body = dict(exn=offer0Serder.ked, sigs=sigs, atc=end0.decode("utf-8"))

        # Bad Sender
        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/BAD/ipex/offer", body=data)
        assert res.status_code == 404
        assert res.json == {
            "description": "BAD is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/offer", body=data)
        assert res.json == {
            "done": False,
            "error": None,
            "metadata": {"said": "ECa9XU2648ryO8PXKEcWkS7V-hvpj86Nh3rjGv93g6jT"},
            "name": "exchange.ECa9XU2648ryO8PXKEcWkS7V-hvpj86Nh3rjGv93g6jT",
            "response": None,
        }

        assert res.status_code == 200
        assert len(agent.exchanges) == 1

        # Now an offer in response to an agree
        dig = "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT"
        offer1Serder, end1 = exchanging.exchange(
            route="/ipex/offer",
            payload={"m": "How about this"},
            sender=pre,
            embeds=embeds,
            dig=dig,
            recipient=pre1,
            date=helping.nowIso8601(),
        )
        assert offer1Serder.ked == {
            "a": {
                "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
                "m": "How about this",
            },
            "d": "EM79tlKrG142-jcaglGnIXKRfLW_DKOK5pnTwN60yz5U",
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "e": {
                "acdc": {
                    "a": {
                        "d": "ELJ7Emhi0Bhxz3s7HyhZ45qcsgpvsT8p8pxwWkG362n3",
                        "dt": "2021-06-27T21:26:21.233257+00:00",
                        "i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
                        "LEI": "78I9GKEFM361IFY3PIN0",
                    },
                    "d": "EBg1YzKmwZIDzZsMslTFwQARB6nUN85sRJF5oywlJr3N",
                    "i": "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze",
                    "ri": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
                    "s": "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
                    "v": "ACDC10JSON000197_",
                },
                "d": "EEcYZMP-zilz2w1w2hEFm6tF0eaX_1KaPEWhNfY3kf8i",
            },
            "i": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
            "rp": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
            "p": "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT",
            "q": {},
            "r": "/ipex/offer",
            "t": "exn",
            "v": "KERI10JSON000357_",
        }
        assert end1 == b""
        sigs = [
            "AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"
        ]

        body = dict(exn=offer1Serder.ked, sigs=sigs, atc=end1.decode("utf-8"))

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/offer", body=data)
        assert res.json == {
            "done": False,
            "error": None,
            "metadata": {"said": "EM79tlKrG142-jcaglGnIXKRfLW_DKOK5pnTwN60yz5U"},
            "name": "exchange.EM79tlKrG142-jcaglGnIXKRfLW_DKOK5pnTwN60yz5U",
            "response": None,
        }

        assert res.status_code == 200
        assert len(agent.exchanges) == 2


def test_ipex_agree(helpers, mockHelpingNowIso8601):
    with helpers.openKeria() as (_, agent, app, client):
        agreeEnd = ipexing.IpexAgreeCollectionEnd()
        app.add_route("/identifiers/{name}/ipex/agree", agreeEnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", aidEnd)

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid["i"]
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        salt2 = b"0123456789abcdeg"
        op = helpers.createAid(client, "recp", salt2)
        aid1 = op["response"]
        pre1 = aid1["i"]
        assert pre1 == "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm"
        dig = "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT"

        agreeSerder, end = exchanging.exchange(
            route="/ipex/agree",
            payload={"m": "Agreed"},
            sender=pre,
            embeds=dict(),
            dig=dig,
            recipient=pre1,
            date=helping.nowIso8601(),
        )
        assert agreeSerder.ked == {
            "a": {"i": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm", "m": "Agreed"},
            "d": "ENMBCgTGXxiMuTMcfGWp4uqnsiso1Jm3tAAn1x7ZPRox",
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "e": {},
            "i": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
            "rp": "EFnYGvF_ENKJ_4PGsWsvfd_R6m5cN-3KYsz_0mAuNpCm",
            "p": "EB_Lr3fHezn1ygn-wbBT5JjzaCMxTmhUoegXeZzWC2eT",
            "q": {},
            "r": "/ipex/agree",
            "t": "exn",
            "v": "KERI10JSON00017e_",
        }
        assert end == b""
        sigs = [
            "AAAa70b4QnTOtGOsMqcezMtVzCFuRJHGeIMkWYHZ5ZxGIXM0XDVAzkYdCeadfPfzlKC6dkfiwuJ0IzLOElaanUgH"
        ]

        # Test with unknown recipient
        unknownRecipient = "EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM"
        unknownAgreeSerder, _ = exchanging.exchange(
            route="/ipex/agree",
            payload={"m": "Agreed"},
            sender=pre,
            embeds=dict(),
            dig=dig,
            recipient=unknownRecipient,
            date=helping.nowIso8601(),
        )

        body = dict(
            exn=unknownAgreeSerder.ked,
            sigs=sigs,
        )

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/agree", body=data)

        assert res.status_code == 400
        assert res.json == {
            "description": "attempt to send to unknown "
            "AID=EZ-i0d8JZAoTNZH3ULaU6JR2nmwyvYAfSVPzhzS6b5CM",
            "title": "400 Bad Request",
        }

        body = dict(exn=agreeSerder.ked, sigs=sigs)

        # Bad Sender
        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/BAD/ipex/agree", body=data)
        assert res.status_code == 404
        assert res.json == {
            "description": "BAD is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        data = json.dumps(body).encode("utf-8")
        res = client.simulate_post(path="/identifiers/test/ipex/agree", body=data)
        assert res.json == {
            "done": False,
            "error": None,
            "metadata": {"said": "ENMBCgTGXxiMuTMcfGWp4uqnsiso1Jm3tAAn1x7ZPRox"},
            "name": "exchange.ENMBCgTGXxiMuTMcfGWp4uqnsiso1Jm3tAAn1x7ZPRox",
            "response": None,
        }

        assert res.status_code == 200
        assert len(agent.exchanges) == 1
