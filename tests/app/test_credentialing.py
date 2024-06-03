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
from keri.core import scheming, coring, parsing, serdering
from keri.core.eventing import SealEvent
from keri.core.signing import Salter
from keri.kering import TraitCodex
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
        registryResEnd = credentialing.RegistryResourceEnd()
        app.add_route("/identifiers/{name}/registries/{registryName}", registryResEnd)
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

        nonce = Salter().qb64
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
        op2 = result.json
        metadata = op2["metadata"]

        assert op2["done"] is True
        assert metadata["anchor"] == anchor
        assert result.status == falcon.HTTP_202

        result = client.simulate_get(path="/identifiers/test/registries")
        assert result.status == falcon.HTTP_200
        assert result.json == []

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        deeds = doist.enter(doers=[agent])
        doist.recur(deeds=deeds)

        while regser.pre not in agent.tvy.tevers:
            doist.recur(deeds=deeds)

        assert regser.pre in agent.tvy.tevers

        result = client.simulate_get(path="/identifiers/test/registries")
        assert result.status == falcon.HTTP_200
        assert len(result.json) == 1
        result = client.simulate_post(path="/identifiers/test/registries", body=json.dumps(body).encode("utf-8"))
        assert result.status == falcon.HTTP_400
        assert result.json == {'description': 'registry name test already in use', 'title': '400 Bad Request'}

        body = dict(name="test", alias="test", vcp=regser.ked, ixn=serder.ked, sigs=sigers)
        result = client.simulate_post(path="/identifiers/bad_test/registries", body=json.dumps(body).encode("utf-8"))
        assert result.status == falcon.HTTP_404
        assert result.json == {'description': 'alias is not a valid reference to an identifier',
                              'title': '404 Not Found'}

        # Try with bad identifier name
        body = b'{"name": "new-name"}'
        result = client.simulate_put(path="/identifiers/test-bad/registries/test", body=body)
        assert result.status == falcon.HTTP_404
        assert result.json == {'description': 'test-bad is not a valid reference to an identifier',
                               'title': '404 Not Found'}

        result = client.simulate_put(path="/identifiers/test/registries/test", body=body)
        assert result.status == falcon.HTTP_200
        regk = result.json['regk']

        # Try to rename a the now used name
        result = client.simulate_put(path="/identifiers/test/registries/new-name", body=b'{}')
        assert result.status == falcon.HTTP_400
        assert result.json == {'description': "'name' is required in body", 'title': '400 Bad Request'}

        # Try to rename a the now used name
        result = client.simulate_put(path="/identifiers/test/registries/test", body=body)
        assert result.status == falcon.HTTP_400
        assert result.json == {'description': 'new-name is already in use for a registry',
                               'title': '400 Bad Request'}

        # Try to rename a now non-existant registry
        body = b'{"name": "newnew-name"}'
        result = client.simulate_put(path="/identifiers/test/registries/test", body=body)
        assert result.status == falcon.HTTP_404
        assert result.json == {'description': 'test is not a valid reference to a credential registry',
                               'title': '404 Not Found'}
        # Rename registry by SAID
        body = b'{"name": "newnew-name"}'
        result = client.simulate_put(path=f"/identifiers/test/registries/{regk}", body=body)
        assert result.status == falcon.HTTP_200

        result = client.simulate_get(path="/identifiers/not_test/registries")
        assert result.status == falcon.HTTP_404
        assert result.json == {'description': 'name is not a valid reference to an identifier', 'title': '404 Not Found'}

        # Test Operation Resource
        result = client.simulate_get(path=f"/operations/{op['name']}")
        assert result.status == falcon.HTTP_200
        assert result.json["done"] == True

        result = client.simulate_get(path=f"/operations/{op2['name']}")
        assert result.status == falcon.HTTP_200
        assert result.json["done"] == True

        result = client.simulate_get(path=f"/operations/bad_name")
        assert result.status == falcon.HTTP_404
        assert result.json == {'title': "long running operation 'bad_name' not found"}

        result = client.simulate_delete(path=f"/operations/{op['name']}")
        assert result.status == falcon.HTTP_204

        result = client.simulate_delete(path=f"/operations/bad_name")
        assert result.status == falcon.HTTP_404
        assert result.json == {'title': "long running operation 'bad_name' not found"}


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
            acdc=creder.sad,
            csigs=csigers,
            path=pather.qb64)
        
        result = client.simulate_post(path="/identifiers/badname/credentials", body=json.dumps(body).encode("utf-8"))
        assert result.status_code == 404
        assert result.json == {'description': "name is not a valid reference to an identifier",
                               'title': '404 Not Found'}
        
        result = client.simulate_post(path="/identifiers/issuer/credentials", body=json.dumps(body).encode("utf-8"))
        op = result.json

        assert 'ced' in op['metadata']
        assert op['metadata']['ced'] == creder.sad

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        assert agent.credentialer.complete(creder.said) is True

        body["acdc"]["a"]["LEI"] = "ACDC10JSON000197_"
        result = client.simulate_post(path="/identifiers/issuer/credentials", body=json.dumps(body).encode("utf-8"))
        assert result.status_code == 400

def test_credentialing_ends(helpers, seeder):
    salt = b'0123456789abcdef'

    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHab(name="issuer", salt=salt, temp=True) as (hby, hab), \
            helpers.withIssuer(name="issuer", hby=hby) as issuer:
        idResEnd = aiding.IdentifierResourceEnd()
        credEnd = credentialing.CredentialCollectionEnd(idResEnd)
        app.add_route("/identifiers/{name}/credentials", credEnd)
        credResEnd = credentialing.CredentialQueryCollectionEnd()
        app.add_route("/credentials/query", credResEnd)
        credResEnd = credentialing.CredentialResourceEnd()
        app.add_route("/credentials/{said}", credResEnd)

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

        registry = rgy.makeRegistry(name="issuer", prefix=hab.pre, **conf)
        assert registry.regk == "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4"

        rseal = SealEvent(registry.regk, "0", registry.regd)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)
        anc = hab.interact(data=[rseal])

        aserder = serdering.SerderKERI(raw=bytes(anc))
        registrar.incept(iserder=registry.vcp, anc=aserder)

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

        res = client.simulate_post(f"/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({'filter': {'-i': issuee}}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert res.json == []

        body = json.dumps({'filter': {'-a-i': issuee}}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({'filter': {'-i': hab.pre}}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({'filter': {'-s': {'$eq': issuer.LE}}}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 3

        body = json.dumps({'filter': {'-s': {'$eq': issuer.QVI}}}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        body = json.dumps({'limit': 1}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 1

        body = json.dumps({'limit': 2}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        body = json.dumps({'limit': 4, 'skip':0}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 4

        body = json.dumps({'limit': 4, 'skip':4}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 1

        body = json.dumps({'limit': 4, 'skip':0, 'sort': ['-i']}).encode("utf-8")
        res = client.simulate_post(f"/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 4

        res = client.simulate_get(f"/credentials/{saids[0]}")
        assert res.status_code == 200
        assert res.headers['content-type'] == "application/json"
        assert res.json['sad']['d'] == saids[0]

        headers = {"Accept": "application/json+cesr"}
        res = client.simulate_get(f"/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 200
        assert res.headers['content-type'] == "application/json+cesr"


def test_revoke_credential(helpers, seeder):
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
        credResEnd = credentialing.CredentialResourceEnd()
        app.add_route("/credentials/{said}", credResEnd)
        credResDelEnd = credentialing.CredentialResourceDeleteEnd(idResEnd)
        app.add_route("/identifiers/{name}/credentials/{said}", credResDelEnd)
        credResEnd = credentialing.CredentialQueryCollectionEnd()
        app.add_route("/credentials/query", credResEnd)

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
            acdc=creder.sad,
            csigs=csigers,
            path=pather.qb64)
        
        result = client.simulate_post(path="/identifiers/badname/credentials", body=json.dumps(body).encode("utf-8"))
        assert result.status_code == 404
        assert result.json == {'description': "name is not a valid reference to an identifier",
                               'title': '404 Not Found'}
        
        result = client.simulate_post(path="/identifiers/issuer/credentials", body=json.dumps(body).encode("utf-8"))
        op = result.json

        assert 'ced' in op['metadata']
        assert op['metadata']['ced'] == creder.sad

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        assert agent.credentialer.complete(creder.said) is True

        res = client.simulate_post(f"/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]['sad']['d'] == creder.said
        assert res.json[0]['status']['s'] == "0"

        res = client.simulate_post(f"/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]['sad']['d'] == creder.said
        assert res.json[0]['status']['s'] == "0"

        regser = eventing.revoke(vcdig=creder.said, regk=registry["regk"], dig=regser.said, dt=dt)
        anchor = dict(i=regser.ked['i'], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(pre=iaid, bran=isalt, pidx=0, ridx=0, dig=serder.said, sn='3', data=[anchor])

        body = dict(
            rev=regser.ked,
            ixn=serder.ked,
            sigs=sigers)
        res = client.simulate_delete(path=f"/identifiers/badname/credentials/{creder.said}", body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 404
        assert res.json == {'description': "name is not a valid reference to an identifier",
                            'title': '404 Not Found'}
        
        res = client.simulate_delete(path=f"/identifiers/issuer/credentials/{regser.said}", body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 404
        assert res.json == {'description': f"credential for said {regser.said} not found.",
                            'title': '404 Not Found'}

        badrev = regser.ked.copy()
        badrev["ri"] = "EIVtei3pGKGUw8H2Ri0h1uOevtSA6QGAq5wifbtHIaNI"
        _, sad = coring.Saider.saidify(badrev)

        badbody = dict(
            rev=sad,
            ixn=serder.ked,
            sigs=sigers)
        res = client.simulate_delete(path=f"/identifiers/issuer/credentials/{creder.said}",
                                     body=json.dumps(badbody).encode("utf-8"))
        assert res.status_code == 404
        assert res.json == {'description': 'revocation against invalid registry SAID '
                                           'EIVtei3pGKGUw8H2Ri0h1uOevtSA6QGAq5wifbtHIaNI',
                            'title': '404 Not Found'}

        badrev = regser.ked.copy()
        badrev["i"] = "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"
        _, sad = coring.Saider.saidify(badrev)

        badbody = dict(
            rev=sad,
            ixn=serder.ked,
            sigs=sigers)
        res = client.simulate_delete(path=f"/identifiers/issuer/credentials/{creder.said}",
                                     body=json.dumps(badbody).encode("utf-8"))
        assert res.status_code == 400
        assert res.json == {'description': "invalid revocation event.",
                            'title': '400 Bad Request'}

        res = client.simulate_delete(path=f"/identifiers/issuer/credentials/{creder.said}",
                                     body=json.dumps(body).encode("utf-8"))
        assert res.status_code == 200
        
        while not agent.registrar.complete(creder.said, sn=1):
            doist.recur(deeds=deeds)
        
        res = client.simulate_post(f"/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]['sad']['d'] == creder.said
        assert res.json[0]['status']['s'] == "1"

        res = client.simulate_post(f"/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]['sad']['d'] == creder.said
        assert res.json[0]['status']['s'] == "1"
