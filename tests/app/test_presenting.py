import json

from keri.app import habbing
from keri.core import parsing
from keri.peer import exchanging
from keri.vdr.credentialing import Regery, Registrar

from keria.app import aiding, credentialing
from keria.app.presenting import PresentationCollectionEnd, loadEnds, PresentationRequestsCollectionEnd


def test_loadends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/identifiers/NAME/credentials/SAID/presentations")
        assert isinstance(end, PresentationCollectionEnd)
        (end, *_) = app._router.find("/identifiers/NAME/requests")
        assert isinstance(end, PresentationRequestsCollectionEnd)


def test_presentation(helpers, seeder, mockHelpingNowUTC):
    salt = b'0123456789abcdef'

    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHab(name="issuer", salt=salt, temp=True) as (hby, hab), \
            helpers.withIssuer(name="issuer", hby=hby) as issuer:

        presentationEnd = PresentationCollectionEnd()
        app.add_route("/identifiers/{name}/credentials/{said}/presentations", presentationEnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        issuee = aid['i']
        assert issuee == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        seeder.seedSchema(hby.db)
        seeder.seedSchema(agent.hby.db)

        rgy = Regery(hby=hby, name="issuer", temp=True)
        registrar = Registrar(hby=hby, rgy=rgy, counselor=None)

        conf = dict(nonce='AGu8jwfkyvVXQ2nqEb5yVigEtR31KSytcpe2U2f7NArr')

        registry = registrar.incept(name="issuer", pre=hab.pre, conf=conf)
        assert registry.regk == "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4"

        issuer.createRegistry(hab.pre, name="issuer")

        said = issuer.issueQVIvLEI("issuer", hab, issuee, "984500E5DEFDBQ1O9038")

        ims = bytearray()
        ims.extend(credentialing.CredentialResourceEnd.outputCred(hby, issuer.rgy, said))
        parsing.Parser(kvy=agent.kvy, rvy=agent.rvy, tvy=agent.tvy, vry=agent.verifier).parse(ims)

        creder = agent.rgy.reger.creds.get(keys=(said,))

        assert creder is not None

        data = dict(
            i=creder.issuer,
            s=creder.schema,
            n=said,
        )

        body = dict()
        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'description': "required field 'exn' missing from request",
                            'title': '400 Bad Request'}

        res = client.simulate_post(path=f"/identifiers/BadUser/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'title': 'Invalid alias BadUser for credential presentation'}

        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'description': "required field 'exn' missing from request",
                            'title': '400 Bad Request'}

        exn = exchanging.exchange(route="/presentation", payload=data)
        sigs = helpers.sign(bran=salt, pidx=0, ridx=0, ser=exn.raw)

        body = dict(exn=exn.ked)
        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'description': "required field 'sigs' missing from request",
                            'title': '400 Bad Request'}

        body = dict(exn=exn.ked, sigs=sigs)
        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'description': "required field 'recipient' missing from request",
                            'title': '400 Bad Request'}

        body = dict(exn=exn.ked, sigs=sigs, recipient="BadRecipient")
        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'description': 'invalid recipient BadRecipient', 'title': '400 Bad Request'}

        body = dict(exn=exn.ked, sigs=sigs, recipient=hab.pre)
        res = client.simulate_post(path=f"/identifiers/test/credentials/BADCREDENTIALSAID/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 404
        assert res.json == {'description': 'credential BADCREDENTIALSAID not found',
                            'title': '404 Not Found'}

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            recipient=hab.pre,
            include=False
        )

        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 202
        assert len(agent.postman.evts) == 1

        evt = agent.postman.evts.popleft()
        assert evt == {'attachment': bytearray(b'-AABAAC1MeGERqHDiff6IBbeYJwXJlXFriDhrQrWYyfef7jnAjMx'
                                               b'wNrMLEoPZjUJtIrsrch46maUizdJnmgNWWR-9VAP'),
                       'dest': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                       'serder': {'a': {'i': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                                        'n': 'EIO9uC3K6MvyjFD-RB3RYW3dfL49kCyz3OPqv3gi1dek',
                                        's': 'EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs'},
                                  'd': 'EOkCRLwEjc7Bkn3wVZkoUXneD0ZiAX6R0MI-CcGaLdfE',
                                  'dt': '2021-01-01T00:00:00.000000+00:00',
                                  'q': {},
                                  'r': '/presentation',
                                  't': 'exn',
                                  'v': 'KERI10JSON000138_'},
                       'src': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                       'topic': 'credential'}

        body["include"] = True
        res = client.simulate_post(path=f"/identifiers/test/credentials/{said}/presentations",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 202
        assert len(agent.postman.evts) == 9

        evt = agent.postman.evts[7]
        assert evt["serder"].raw == creder.raw

        evt = agent.postman.evts[8]
        assert evt == {'attachment': bytearray(b'-AABAAC1MeGERqHDiff6IBbeYJwXJlXFriDhrQrWYyfef7jnAjMx'
                                               b'wNrMLEoPZjUJtIrsrch46maUizdJnmgNWWR-9VAP'),
                       'dest': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                       'serder': {'a': {'i': 'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze',
                                        'n': 'EIO9uC3K6MvyjFD-RB3RYW3dfL49kCyz3OPqv3gi1dek',
                                        's': 'EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs'},
                                  'd': 'EOkCRLwEjc7Bkn3wVZkoUXneD0ZiAX6R0MI-CcGaLdfE',
                                  'dt': '2021-01-01T00:00:00.000000+00:00',
                                  'q': {},
                                  'r': '/presentation',
                                  't': 'exn',
                                  'v': 'KERI10JSON000138_'},
                       'src': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                       'topic': 'credential'}


def test_presentation_request(helpers):
    salt = b'0123456789abcdef'
    with helpers.openKeria() as (agency, agent, app, client):
        requestsEnd = PresentationRequestsCollectionEnd()
        app.add_route("/identifiers/{name}/requests", requestsEnd)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        issuee = aid['i']
        assert issuee == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        issuer = "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4"
        pl = dict(
            s=schema,
            i=issuer
        )

        exn = exchanging.exchange(route="/presentation/request", payload=pl)
        sigs = helpers.sign(bran=salt, pidx=0, ridx=0, ser=exn.raw)

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            recipient=issuee
        )

        res = client.simulate_post(path=f"/identifiers/test/requests",
                                   body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 202

