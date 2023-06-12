# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.credentialing module

Testing credentialing endpoint in the Mark II Agent
"""
import json

import falcon
from falcon import testing
from hio.base import doing
from keri.app import habbing
from keri.core import scheming, coring, parsing
from keri.core.eventing import TraitCodex
from keri.vdr import eventing
from keri.vdr.credentialing import Regery, Registrar

from keria.app import credentialing, aiding


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        credentialing.loadEnds(app=app, identifierResource=None)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/schema")
        assert isinstance(end, credentialing.SchemaCollectionEnd)
        (end, *_) = app._router.find("/schema/SAID")
        assert isinstance(end, credentialing.SchemaResourceEnd)
        (end, *_) = app._router.find("/registries")
        assert isinstance(end, credentialing.RegistryEnd)


def test_schema_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        client = testing.TestClient(app)

        schemaColEnd = credentialing.SchemaCollectionEnd()
        app.add_route("/schema", schemaColEnd)
        schemaResEnd = credentialing.SchemaResourceEnd()
        app.add_route("/schema/{said}", schemaResEnd)

        sed = dict()
        sed["$id"] = ""
        sed["$schema"] = "http://json-schema.org/draft-07/schema#"
        sed.update(dict(type="object", properties=dict(a=dict(type="string"))))
        sce = scheming.Schemer(sed=sed, typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256)
        agent.hby.db.schema.pin(sce.said, sce)

        sed = dict()
        sed["$id"] = ""
        sed["$schema"] = "http://json-schema.org/draft-07/schema#"
        sed.update(dict(type="object", properties=dict(b=dict(type="number"), )))
        sce = scheming.Schemer(sed=sed, typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256)
        agent.hby.db.schema.pin(sce.said, sce)

        sed = dict()
        sed["$id"] = ""
        sed["$schema"] = "http://json-schema.org/draft-07/schema#"
        sed.update(dict(type="object", properties=dict(c=dict(type="string", format="date-time"))))
        sce = scheming.Schemer(sed=sed, typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256)
        agent.hby.db.schema.pin(sce.said, sce)

        response = client.simulate_get("/schema")
        assert response.status == falcon.HTTP_200
        assert len(response.json) == 3
        assert response.json[0]["$id"] == 'EHoMjhY-5V5jdSXr0yHEYWxSH8MeFfNEqnmhXbClTepe'
        schema0id = 'EHoMjhY-5V5jdSXr0yHEYWxSH8MeFfNEqnmhXbClTepe'
        assert response.json[1]["$id"] == 'ELrCCNUmu7t9OS5XX6MYwuyLHY13IWuJoFVPfBkjkGAd'
        assert response.json[2]["$id"] == 'ENW0ZoANRhLAHczo7BwgzBlkDMZWFU2QilCCIbg98PK6'

        assert response.json[2]["properties"] == {'b': {'type': 'number'}}
        assert response.json[0]["properties"] == {'c': {'format': 'date-time', 'type': 'string'}}
        assert response.json[1]["properties"] == {'a': {'type': 'string'}}

        badschemaid = 'EH1MjhY-5V5jdSXr0yHEYWxSH8MeFfNEqnmhXbClTepe'
        response = client.simulate_get(f"/schema/{badschemaid}")
        assert response.status == falcon.HTTP_404

        response = client.simulate_get(f"/schema/{schema0id}")
        assert response.status == falcon.HTTP_200
        assert response.json["$id"] == schema0id
        assert response.json["properties"] == {'c': {'format': 'date-time', 'type': 'string'}}


def test_registry_end(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        registryEnd = credentialing.RegistryEnd(idResEnd)
        app.add_route("/registries", registryEnd)

        seeder.seedSchema(agent.hby.db)
        result = client.simulate_post(path="/registries", body=b'{}')
        assert result.status == falcon.HTTP_400  # Bad request, missing name

        result = client.simulate_post(path="/registries", body=b'{"name": "test"}')
        assert result.status == falcon.HTTP_400  # Bad Request, missing alias

        result = client.simulate_post(path="/registries", body=b'{"name": "test", "alias": "test123"}')
        assert result.status == falcon.HTTP_400  # Bad Request, invalid alias

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        nonce = coring.randomNonce()
        regser = eventing.incept(pre,
                                 baks=[],
                                 toad="0",
                                 nonce=nonce,
                                 cnfg=[TraitCodex.NoBackers],
                                 code=coring.MtrDex.Blake3_256)
        anchor = dict(i=regser.ked['i'], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(pre=pre, bran=salt, pidx=0, ridx=0, dig=aid['d'], sn='1', data=[anchor])
        body = dict(name="test", alias="test", vcp=regser.ked, ixn=serder.ked, sigs=sigers)
        result = client.simulate_post(path="/registries", body=json.dumps(body).encode("utf-8"))
        assert result.status == falcon.HTTP_202
        assert len(agent.registries) == 1
        msg = agent.registries.popleft()

        assert msg["pre"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"
        assert msg["regk"] == regser.pre
        assert msg["sn"] == '0'
        agent.registries.append(msg)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        # doist.do(doers=doers)
        deeds = doist.enter(doers=[agent])
        doist.recur(deeds=deeds)

        while len(agent.registries) == 1:
            doist.recur(deeds=deeds)

        assert len(agent.registries) == 0
        assert regser.pre in agent.tvy.tevers


def test_credentialing_ends(helpers, seeder):
    salt = b'0123456789abcdef'

    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHab(name="issuer", salt=salt, temp=True) as (hby, hab), \
            helpers.withIssuer(name="issuer", hby=hby) as issuer:
        credEnd = credentialing.CredentialCollectionEnd()
        app.add_route("/identifiers/{aid}/credentials", credEnd)
        credResEnd = credentialing.CredentialResourceEnd()
        app.add_route("/identifiers/{aid}/credentials/{said}", credResEnd)

        assert hab.pre == "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze"

        seeder.seedSchema(hby.db)
        seeder.seedSchema(agent.hby.db)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        issuee = aid['i']
        assert issuee == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        rgy = Regery(hby=hby, name="issuer", temp=True)
        registrar = Registrar(hby=hby, rgy=rgy, counselor=None)

        conf = dict(nonce='AGu8jwfkyvVXQ2nqEb5yVigEtR31KSytcpe2U2f7NArr')

        registry = registrar.incept(name="issuer", pre=hab.pre, conf=conf)
        assert registry.regk == "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4"

        issuer.createRegistry(hab.pre, name="issuer")

        print()
        saids = [
            issuer.issueQVIvLEI("issuer", hab, issuee, "984500E5DEFDBQ1O9038"),
            issuer.issueQVIvLEI("issuer", hab, issuee, "984500AAFEB59DDC0E43"),
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "254900OPPU84GM83MG36"),
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "9845004CC7884BN85018"),
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "98450030F6X9EC7C8336")
        ]

        ims = bytearray()
        for said in saids:
            print(said)
            ims.extend(credentialing.CredentialResourceEnd.outputCred(hby, issuer.rgy, said))

        parsing.Parser(kvy=agent.kvy, rvy=agent.rvy, tvy=agent.tvy, vry=agent.verifier).parse(ims)

        res = client.simulate_get(f"/identifiers/{hab.pre}/credentials")
        assert res.status_code == 400
        assert res.json == {'description': 'Invalid identifier '
                                           'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze for credentials',
                            'title': '400 Bad Request'}

        res = client.simulate_get(f"/identifiers/{issuee}/credentials")
        assert res.status_code == 400
        assert res.json == {'description': 'Invalid type None', 'title': '400 Bad Request'}

        res = client.simulate_get(f"/identifiers/{issuee}/credentials?type=issued")
        assert res.status_code == 200
        assert res.json == []

        res = client.simulate_get(f"/identifiers/{issuee}/credentials?type=received")
        assert res.status_code == 200
        assert len(res.json) == 5

        res = client.simulate_get(f"/identifiers/{issuee}/credentials?type=received&schema={issuer.LE}")
        assert res.status_code == 200
        assert len(res.json) == 3

        res = client.simulate_get(f"/identifiers/{issuee}/credentials?type=received&schema={issuer.QVI}")
        assert res.status_code == 200
        assert len(res.json) == 2

        res = client.simulate_get(f"/identifiers/{issuee}/credentials/{saids[0]}")
        assert res.status_code == 200
        print(res.headers)
        assert res.headers['content-type'] == "application/json"
        assert res.json['sad']['d'] == saids[0]

        headers = {"Accepts": "application/json+cesr"}
        res = client.simulate_get(f"/identifiers/{hab.pre}/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 400
        assert res.json == {'description': 'Invalid identifier '
                                           'EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze for credentials',
                            'title': '400 Bad Request'}

        res = client.simulate_get(f"/identifiers/{issuee}/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 200
        assert res.headers['content-type'] == "application/json+cesr"
