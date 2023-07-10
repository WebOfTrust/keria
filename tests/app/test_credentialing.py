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
from keri.vc import proving
from keri.vdr import eventing
from keri.vdr.credentialing import Regery, Registrar

from keria.app import credentialing, aiding
from keria.core import longrunning


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
        (end, *_) = app._router.find("/identifiers/NAME/registries")
        assert isinstance(end, credentialing.RegistryCollectionEnd)


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
        registryEnd = credentialing.RegistryCollectionEnd(idResEnd)
        app.add_route("/identifiers/{name}/registries", registryEnd)
        opEnd = longrunning.OperationResourceEnd()
        app.add_route("/operations/{name}", opEnd)

        seeder.seedSchema(agent.hby.db)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        result = client.simulate_post(path="/identifiers/test/registries", body=b'{}')
        assert result.status == falcon.HTTP_400  # Bad request, missing name

        result = client.simulate_post(path="/identifiers/test123/registries", body=b'{"name": "test"}')
        assert result.status == falcon.HTTP_400  # Bad Request, invalid aid name

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
        result = client.simulate_post(path="/identifiers/test/registries", body=json.dumps(body).encode("utf-8"))
        op = result.json
        metadata = op["metadata"]

        assert op["done"] is True
        assert metadata["anchor"] == anchor
        assert result.status == falcon.HTTP_202

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        deeds = doist.enter(doers=[agent])
        doist.recur(deeds=deeds)

        while regser.pre not in agent.tvy.tevers:
            doist.recur(deeds=deeds)

        assert regser.pre in agent.tvy.tevers


def test_issue_credential(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}", idResEnd)
        registryEnd = credentialing.RegistryCollectionEnd(idResEnd)
        app.add_route("/identifiers/{name}/registries", registryEnd)
        credEnd = credentialing.CredentialCollectionEnd(idResEnd)
        app.add_route("/identifiers/{name}/credentials", credEnd)
        opEnd = longrunning.OperationResourceEnd()
        app.add_route("/operations/{name}", opEnd)
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)

        seeder.seedSchema(agent.hby.db)

        # create the server that will receive the credential issuance messages
        serverDoer = helpers.server(agency)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        isalt = b'0123456789abcdef'
        registry, issuer = helpers.createRegistry(client, agent, isalt, doist, deeds)

        iaid = issuer["prefix"]
        idig = issuer['state']['d']

        rsalt = b'abcdef0123456789'
        op = helpers.createAid(client, "recipient", rsalt)
        aid = op["response"]
        recp = aid['i']
        assert recp == "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"

        helpers.createEndRole(client, agent, recp, "recipient", rsalt)

        dt = "2021-01-01T00:00:00.000000+00:00"
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        data = dict(LEI="254900DA0GOGCFVWB618", dt=dt)
        creder = proving.credential(issuer=iaid,
                                    schema=schema,
                                    recipient=recp,
                                    data=data,
                                    source={},
                                    status=registry["regk"])

        csigers = helpers.sign(bran=isalt, pidx=0, ridx=0, ser=creder.raw)

        # Test no backers... backers would use backerIssue
        regser = eventing.issue(vcdig=creder.said, regk=registry["regk"], dt=dt)

        anchor = dict(i=regser.ked['i'], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(pre=iaid, bran=isalt, pidx=0, ridx=0, dig=idig, sn='2', data=[anchor])

        pather = coring.Pather(path=[])

        body = dict(
            iss=regser.ked,
            ixn=serder.ked,
            sigs=sigers,
            cred=creder.ked,
            csigs=csigers,
            path=pather.qb64)
        result = client.simulate_post(path="/identifiers/issuer/credentials", body=json.dumps(body).encode("utf-8"))
        op = result.json

        assert 'ced' in op['metadata']
        assert op['metadata']['ced'] == creder.ked

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        assert agent.credentialer.complete(creder.said) is True


def test_credentialing_ends(helpers, seeder):
    salt = b'0123456789abcdef'

    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHab(name="issuer", salt=salt, temp=True) as (hby, hab), \
            helpers.withIssuer(name="issuer", hby=hby) as issuer:
        idResEnd = aiding.IdentifierResourceEnd()
        credEnd = credentialing.CredentialCollectionEnd(idResEnd)
        app.add_route("/identifiers/{name}/credentials", credEnd)
        credResEnd = credentialing.CredentialResourceEnd()
        app.add_route("/identifiers/{name}/credentials/{said}", credResEnd)

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

        saids = [
            issuer.issueQVIvLEI("issuer", hab, issuee, "984500E5DEFDBQ1O9038"),
            issuer.issueQVIvLEI("issuer", hab, issuee, "984500AAFEB59DDC0E43"),
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "254900OPPU84GM83MG36"),
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "9845004CC7884BN85018"),
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "98450030F6X9EC7C8336")
        ]

        ims = bytearray()
        for said in saids:
            ims.extend(credentialing.CredentialResourceEnd.outputCred(hby, issuer.rgy, said))

        parsing.Parser(kvy=agent.kvy, rvy=agent.rvy, tvy=agent.tvy, vry=agent.verifier).parse(ims)

        for said in saids:
            agent.seeker.index(said)

        res = client.simulate_get(f"/identifiers/{hab.name}/credentials")
        assert res.status_code == 404
        assert res.json == {'description': 'name is not a valid reference to an identfier',
                            'title': '404 Not Found'}

        res = client.simulate_get(f"/identifiers/test/credentials")
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({'filter': {'-i': issuee}}).encode("utf-8")
        res = client.simulate_get(f"/identifiers/test/credentials", body=body)
        assert res.status_code == 200
        assert res.json == []

        body = json.dumps({'filter': {'-a-i': issuee}}).encode("utf-8")
        res = client.simulate_get(f"/identifiers/test/credentials", body=body)
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({'filter': {'-i': hab.pre}}).encode("utf-8")
        res = client.simulate_get(f"/identifiers/test/credentials", body=body)
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({'filter': {'-s': {'$eq': issuer.LE}}}).encode("utf-8")
        res = client.simulate_get(f"/identifiers/test/credentials", body=body)
        assert res.status_code == 200
        assert len(res.json) == 3

        body = json.dumps({'filter': {'-s': {'$eq': issuer.QVI}}}).encode("utf-8")
        res = client.simulate_get(f"/identifiers/test/credentials", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        res = client.simulate_get(f"/identifiers/test/credentials/{saids[0]}")
        assert res.status_code == 200
        assert res.headers['content-type'] == "application/json"
        assert res.json['sad']['d'] == saids[0]

        headers = {"Accept": "application/json+cesr"}
        res = client.simulate_get(f"/identifiers/{hab.name}/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 404

        res = client.simulate_get(f"/identifiers/test/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 200
        assert res.headers['content-type'] == "application/json+cesr"
