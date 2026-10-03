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
from keri.app.habbing import SignifyGroupHab
from keri.core import eventing as keventing, scheming, coring, parsing, serdering
from keri.db import dbing
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
        sce = scheming.Schemer(
            sed=sed, typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256
        )
        agent.hby.db.schema.pin(sce.said, sce)

        sed = dict()
        sed["$id"] = ""
        sed["$schema"] = "http://json-schema.org/draft-07/schema#"
        sed.update(
            dict(
                type="object",
                properties=dict(
                    b=dict(type="number"),
                ),
            )
        )
        sce = scheming.Schemer(
            sed=sed, typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256
        )
        agent.hby.db.schema.pin(sce.said, sce)

        sed = dict()
        sed["$id"] = ""
        sed["$schema"] = "http://json-schema.org/draft-07/schema#"
        sed.update(
            dict(
                type="object",
                properties=dict(c=dict(type="string", format="date-time")),
            )
        )
        sce = scheming.Schemer(
            sed=sed, typ=scheming.JSONSchema(), code=coring.MtrDex.Blake3_256
        )
        agent.hby.db.schema.pin(sce.said, sce)

        response = client.simulate_get("/schema")
        assert response.status == falcon.HTTP_200
        assert len(response.json) == 3
        assert response.json[0]["$id"] == "EHoMjhY-5V5jdSXr0yHEYWxSH8MeFfNEqnmhXbClTepe"
        schema0id = "EHoMjhY-5V5jdSXr0yHEYWxSH8MeFfNEqnmhXbClTepe"
        assert response.json[1]["$id"] == "ELrCCNUmu7t9OS5XX6MYwuyLHY13IWuJoFVPfBkjkGAd"
        assert response.json[2]["$id"] == "ENW0ZoANRhLAHczo7BwgzBlkDMZWFU2QilCCIbg98PK6"

        assert response.json[2]["properties"] == {"b": {"type": "number"}}
        assert response.json[0]["properties"] == {
            "c": {"format": "date-time", "type": "string"}
        }
        assert response.json[1]["properties"] == {"a": {"type": "string"}}

        badschemaid = "EH1MjhY-5V5jdSXr0yHEYWxSH8MeFfNEqnmhXbClTepe"
        response = client.simulate_get(f"/schema/{badschemaid}")
        assert response.status == falcon.HTTP_404

        response = client.simulate_get(f"/schema/{schema0id}")
        assert response.status == falcon.HTTP_200
        assert response.json["$id"] == schema0id
        assert response.json["properties"] == {
            "c": {"format": "date-time", "type": "string"}
        }


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
        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        pre = aid["i"]
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        result = client.simulate_post(path="/identifiers/test/registries", body=b"{}")
        assert result.status == falcon.HTTP_400  # Bad request, missing name

        result = client.simulate_post(
            path="/identifiers/test123/registries", body=b'{"name": "test"}'
        )
        assert result.status == falcon.HTTP_400  # Bad Request, invalid aid name

        nonce = Salter().qb64
        regser = eventing.incept(
            pre,
            baks=[],
            toad="0",
            nonce=nonce,
            cnfg=[TraitCodex.NoBackers],
            code=coring.MtrDex.Blake3_256,
        )
        anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(
            pre=pre, bran=salt, pidx=0, ridx=0, dig=aid["d"], sn="1", data=[anchor]
        )
        body = dict(
            name="test", alias="test", vcp=regser.ked, ixn=serder.ked, sigs=sigers
        )
        result = client.simulate_post(
            path="/identifiers/test/registries", body=json.dumps(body).encode("utf-8")
        )
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
        result = client.simulate_post(
            path="/identifiers/test/registries", body=json.dumps(body).encode("utf-8")
        )
        assert result.status == falcon.HTTP_400
        assert result.json == {
            "description": "registry name test already in use",
            "title": "400 Bad Request",
        }

        body = dict(
            name="test", alias="test", vcp=regser.ked, ixn=serder.ked, sigs=sigers
        )
        result = client.simulate_post(
            path="/identifiers/bad_test/registries",
            body=json.dumps(body).encode("utf-8"),
        )
        assert result.status == falcon.HTTP_404
        assert result.json == {
            "description": "bad_test is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        # Try with bad identifier name
        body = b'{"name": "new-name"}'
        result = client.simulate_put(
            path="/identifiers/test-bad/registries/test", body=body
        )
        assert result.status == falcon.HTTP_404
        assert result.json == {
            "description": "test-bad is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        result = client.simulate_put(
            path="/identifiers/test/registries/test", body=body
        )
        assert result.status == falcon.HTTP_200
        regk = result.json["regk"]

        # Try to rename a the now used name
        result = client.simulate_put(
            path="/identifiers/test/registries/new-name", body=b"{}"
        )
        assert result.status == falcon.HTTP_400
        assert result.json == {
            "description": "'name' is required in body",
            "title": "400 Bad Request",
        }

        # Try to rename a the now used name
        result = client.simulate_put(
            path="/identifiers/test/registries/test", body=body
        )
        assert result.status == falcon.HTTP_400
        assert result.json == {
            "description": "new-name is already in use for a registry",
            "title": "400 Bad Request",
        }

        # Try to rename a now non-existant registry
        body = b'{"name": "newnew-name"}'
        result = client.simulate_put(
            path="/identifiers/test/registries/test", body=body
        )
        assert result.status == falcon.HTTP_404
        assert result.json == {
            "description": "test is not a valid reference to a credential registry",
            "title": "404 Not Found",
        }
        # Rename registry by SAID
        body = b'{"name": "newnew-name"}'
        result = client.simulate_put(
            path=f"/identifiers/test/registries/{regk}", body=body
        )
        assert result.status == falcon.HTTP_200

        result = client.simulate_get(path="/identifiers/not_test/registries")
        assert result.status == falcon.HTTP_404
        assert result.json == {
            "description": "not_test is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        # Test Operation Resource
        result = client.simulate_get(path=f"/operations/{op['name']}")
        assert result.status == falcon.HTTP_200
        assert result.json["done"]

        result = client.simulate_get(path=f"/operations/{op2['name']}")
        assert result.status == falcon.HTTP_200
        assert result.json["done"]

        result = client.simulate_get(path="/operations/bad_name")
        assert result.status == falcon.HTTP_404
        assert result.json == {"title": "long running operation 'bad_name' not found"}

        result = client.simulate_delete(path=f"/operations/{op['name']}")
        assert result.status == falcon.HTTP_204

        result = client.simulate_delete(path="/operations/bad_name")
        assert result.status == falcon.HTTP_404
        assert result.json == {"title": "long running operation 'bad_name' not found"}


def test_issue_credential(helpers, seeder):
    with (
        helpers.openKeria() as (agency, agent, app, client),
        helpers.openKeria() as (agency1, agent1, app1, client1),
    ):
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
        seeder.seedSchema(agent1.hby.db)

        # create the server that will receive the credential issuance messages
        serverDoer = helpers.server(agency, httpPort=3903)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        isalt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, isalt, doist, deeds)

        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]

        rsalt = b"abcdef0123456789"
        op = helpers.createAid(client, "recipient", rsalt)
        aid = op["response"]
        recp = aid["i"]
        assert recp == "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"

        helpers.createEndRole(client, agent, recp, "recipient", rsalt)

        dt = "2021-01-01T00:00:00.000000+00:00"
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        data = dict(LEI="254900DA0GOGCFVWB618", dt=dt)
        creder = proving.credential(
            issuer=iaid,
            schema=schema,
            recipient=recp,
            data=data,
            source={},
            status=registry["regk"],
        )

        csigers = helpers.sign(bran=isalt, pidx=0, ridx=0, ser=creder.raw)

        # Test no backers... backers would use backerIssue
        regser = eventing.issue(vcdig=creder.said, regk=registry["regk"], dt=dt)

        anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(
            pre=iaid, bran=isalt, pidx=0, ridx=0, dig=idig, sn="2", data=[anchor]
        )

        pather = coring.Pather(path=[])

        body = dict(
            iss=regser.ked,
            ixn=serder.ked,
            sigs=sigers,
            acdc=creder.sad,
            csigs=csigers,
            path=pather.qb64,
        )

        result = client.simulate_post(
            path="/identifiers/badname/credentials",
            body=json.dumps(body).encode("utf-8"),
        )
        assert result.status_code == 404
        assert result.json == {
            "description": "badname is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        result = client.simulate_post(
            path="/identifiers/issuer/credentials",
            body=json.dumps(body).encode("utf-8"),
        )
        op = result.json

        assert "ced" in op["metadata"]
        assert op["metadata"]["ced"] == creder.sad

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        assert agent.credentialer.complete(creder.said) is True

        body["acdc"]["a"]["LEI"] = "ACDC10JSON000197_"
        result = client.simulate_post(
            path="/identifiers/issuer/credentials",
            body=json.dumps(body).encode("utf-8"),
        )
        assert result.status_code == 400

        # Try to load into another agent after TEL query without IPEX
        agent1.parser.parse(ims=agent.hby.habByName("issuer").replay())
        assert iaid in agent1.hby.kevers

        agent1.parser.parse(ims=agent.rgy.reger.cloneTvtAt(registry["regk"]))
        assert registry["regk"] in agent1.rgy.tevers

        agent1.parser.parse(ims=agent.rgy.reger.cloneTvtAt(creder.said))
        assert agent1.rgy.tevers[registry["regk"]].vcSn(creder.said) is not None

        credVerifyEnd = credentialing.CredentialVerificationCollectionEnd()
        app1.add_route("/credentials/verify", credVerifyEnd)

        body = dict(acdc=creder.sad, iss=regser.ked)  # still has changed LEI
        result = client1.simulate_post(
            path="/credentials/verify", body=json.dumps(body).encode("utf-8")
        )
        assert result.status_code == 400

        body["acdc"]["a"]["LEI"] = "254900DA0GOGCFVWB618"  # change back
        result = client1.simulate_post(
            path="/credentials/verify", body=json.dumps(body).encode("utf-8")
        )
        assert result.status_code == 202

        deeds = doist.enter(doers=[agent1])
        while not agent1.rgy.reger.creds.get(keys=(creder.said,)):
            doist.recur(deeds=deeds)


def test_credentialing_ends(helpers, seeder):
    salt = b"0123456789abcdef"

    with (
        helpers.openKeria() as (agency, agent, app, client),
        habbing.openHab(name="issuer", salt=salt, temp=True) as (hby, hab),
        helpers.withIssuer(name="issuer", hby=hby) as issuer,
    ):
        idResEnd = aiding.IdentifierResourceEnd()
        credEnd = credentialing.CredentialCollectionEnd(idResEnd)
        app.add_route("/identifiers/{name}/credentials", credEnd)
        credResEnd = credentialing.CredentialQueryCollectionEnd()
        app.add_route("/credentials/query", credResEnd)
        credResEnd = credentialing.CredentialResourceEnd()
        app.add_route("/credentials/{said}", credResEnd)
        credentialRegistryResEnd = credentialing.CredentialRegistryResourceEnd()
        app.add_route("/registries/{ri}/{credential_said}", credentialRegistryResEnd)

        assert hab.pre == "EIqTaQiZw73plMOq8pqHTi9BDgDrrE7iE9v2XfN2Izze"

        seeder.seedSchema(hby.db)
        seeder.seedSchema(agent.hby.db)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        issuee = aid["i"]
        assert issuee == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        rgy = Regery(hby=hby, name="issuer", temp=True)
        registrar = Registrar(hby=hby, rgy=rgy, counselor=None)

        conf = dict(nonce="AGu8jwfkyvVXQ2nqEb5yVigEtR31KSytcpe2U2f7NArr")

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
            issuer.issueLegalEntityvLEI("issuer", hab, issuee, "98450030F6X9EC7C8336"),
        ]

        ims = bytearray()
        for said in saids:
            ims.extend(
                credentialing.CredentialResourceEnd.outputCred(hby, issuer.rgy, said)
            )

        parsing.Parser(
            kvy=agent.kvy, rvy=agent.rvy, tvy=agent.tvy, vry=agent.verifier
        ).parse(ims)

        for said in saids:
            agent.seeker.index(said)

        res = client.simulate_post("/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({"filter": {"-i": issuee}}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert res.json == []

        body = json.dumps({"filter": {"-a-i": issuee}}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({"filter": {"-i": hab.pre}}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 5

        body = json.dumps({"filter": {"-s": {"$eq": issuer.LE}}}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 3

        body = json.dumps({"filter": {"-s": {"$eq": issuer.QVI}}}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        body = json.dumps({"limit": 1}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 1

        body = json.dumps({"limit": 2}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 2

        body = json.dumps({"limit": 4, "skip": 0}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 4

        body = json.dumps({"limit": 4, "skip": 4}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 1

        body = json.dumps({"limit": 4, "skip": 0, "sort": ["-i"]}).encode("utf-8")
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 4

        res = client.simulate_get(f"/credentials/{saids[0]}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/json"
        assert res.json["sad"]["d"] == saids[0]

        res = client.simulate_get(
            "/credentials/EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy"
        )

        # Non-existent credential should return 404 (not found)
        assert res.status_code == 404
        assert res.json == {
            "description": "credential for said EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy not found.",
            "title": "404 Not Found",
        }

        # Same credential with application/json+cesr should also return 404 (not found)
        headers = {"Accept": "application/json+cesr"}
        res = client.simulate_get(
            "/credentials/EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy", headers=headers
        )
        assert res.status_code == 404

        headers = {"Accept": "application/json+cesr"}
        res = client.simulate_get(f"/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/json+cesr"

        res = client.simulate_get(f"/registries/{registry.regk}/{saids[0]}")
        assert res.status_code == 200
        assert res.json == {
            "vn": [1, 0],
            "i": "EIO9uC3K6MvyjFD-RB3RYW3dfL49kCyz3OPqv3gi1dek",
            "s": "0",
            "d": "EBVaw6pCqfMIiZGkA6qevzRUGsxTRuZXxl6YG1neeCGF",
            "ri": "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
            "ra": {},
            "a": {"s": 3, "d": "EO_rknKiU14E0I-rN6yttRE0OSDKaQpVSozAcghjS4dj"},
            "dt": "2021-06-27T21:26:21.233257+00:00",
            "et": "iss",
        }

        res = client.simulate_get(
            f"/registries/{registry.regk}/EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy"
        )
        assert res.status_code == 404
        assert res.json == {
            "description": "credential EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy not found in registry EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4",
            "title": "404 Not Found",
        }

        res = client.simulate_get(
            f"/registries/EBVaw6pCqfMIiZGkA6qevzRUGsxTRuZXxl6YG1neeCGF/{saids[0]}"
        )
        assert res.status_code == 404
        assert res.json == {
            "description": "registry EBVaw6pCqfMIiZGkA6qevzRUGsxTRuZXxl6YG1neeCGF not found",
            "title": "404 Not Found",
        }

        res = client.simulate_delete("/credentials/doesnotexist")
        assert res.status_code == 404
        assert res.json == {
            "description": "credential for said doesnotexist not found.",
            "title": "404 Not Found",
        }

        res = client.simulate_delete(f"/credentials/{saids[0]}")
        assert res.status_code == 204

        res = client.simulate_get(f"/credentials/{saids[0]}")
        # Deleted credential should return 404 (not found)
        assert res.status_code == 404
        assert res.json == {
            "description": f"credential for said {saids[0]} not found.",
            "title": "404 Not Found",
        }

        # Deleted credential with application/json+cesr should also return 404 (not found)
        headers = {"Accept": "application/json+cesr"}
        res = client.simulate_get(f"/credentials/{saids[0]}", headers=headers)
        assert res.status_code == 404

        res = client.simulate_post("/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 4

        # Query using specific filter to check indexes
        body = json.dumps({"filter": {"-a-LEI": "984500E5DEFDBQ1O9038"}}).encode(
            "utf-8"
        )
        res = client.simulate_post("/credentials/query", body=body)
        assert res.status_code == 200
        assert len(res.json) == 0

        # Check db directly to make sure all indices are gone too (GET endpoints don't cover all indices)
        assert agent.rgy.reger.creds.get(keys=saids[0]) is None
        assert agent.rgy.reger.cancs.get(keys=saids[0]) is None
        assert agent.rgy.reger.saved.get(keys=saids[0]) is None
        assert agent.rgy.reger.issus.cnt(keys=hab.pre) == 4
        assert (
            agent.rgy.reger.schms.cnt(
                keys="EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
            )
            == 1
        )
        assert agent.rgy.reger.subjs.cnt(keys=issuee) == 4


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
        credentialRegistryResEnd = credentialing.CredentialRegistryResourceEnd()
        app.add_route("/registries/{ri}/{credential_said}", credentialRegistryResEnd)

        seeder.seedSchema(agent.hby.db)

        # create the server that will receive the credential issuance messages
        serverDoer = helpers.server(agency, httpPort=3904)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        isalt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, isalt, doist, deeds)

        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]

        rsalt = b"abcdef0123456789"
        op = helpers.createAid(client, "recipient", rsalt)
        aid = op["response"]
        recp = aid["i"]
        assert recp == "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"

        helpers.createEndRole(client, agent, recp, "recipient", rsalt)

        dt = "2021-01-01T00:00:00.000000+00:00"
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        data = dict(LEI="254900DA0GOGCFVWB618", dt=dt)
        creder = proving.credential(
            issuer=iaid,
            schema=schema,
            recipient=recp,
            data=data,
            source={},
            status=registry["regk"],
        )

        csigers = helpers.sign(bran=isalt, pidx=0, ridx=0, ser=creder.raw)

        # Test no backers... backers would use backerIssue
        regser = eventing.issue(vcdig=creder.said, regk=registry["regk"], dt=dt)

        anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(
            pre=iaid, bran=isalt, pidx=0, ridx=0, dig=idig, sn="2", data=[anchor]
        )

        pather = coring.Pather(path=[])

        body = dict(
            iss=regser.ked,
            ixn=serder.ked,
            sigs=sigers,
            acdc=creder.sad,
            csigs=csigers,
            path=pather.qb64,
        )

        result = client.simulate_post(
            path="/identifiers/badname/credentials",
            body=json.dumps(body).encode("utf-8"),
        )
        assert result.status_code == 404
        assert result.json == {
            "description": "badname is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        result = client.simulate_post(
            path="/identifiers/issuer/credentials",
            body=json.dumps(body).encode("utf-8"),
        )
        op = result.json

        assert "ced" in op["metadata"]
        assert op["metadata"]["ced"] == creder.sad

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        assert agent.credentialer.complete(creder.said) is True

        res = client.simulate_post("/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]["sad"]["d"] == creder.said
        assert res.json[0]["status"]["s"] == "0"

        res = client.simulate_post("/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]["sad"]["d"] == creder.said
        assert res.json[0]["status"]["s"] == "0"

        regser = eventing.revoke(
            vcdig=creder.said, regk=registry["regk"], dig=regser.said, dt=dt
        )
        anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(
            pre=iaid, bran=isalt, pidx=0, ridx=0, dig=serder.said, sn="3", data=[anchor]
        )

        body = dict(rev=regser.ked, ixn=serder.ked, sigs=sigers)
        res = client.simulate_delete(
            path=f"/identifiers/badname/credentials/{creder.said}",
            body=json.dumps(body).encode("utf-8"),
        )
        assert res.status_code == 404
        assert res.json == {
            "description": "badname is not a valid reference to an identifier",
            "title": "404 Not Found",
        }

        res = client.simulate_delete(
            path=f"/identifiers/issuer/credentials/{regser.said}",
            body=json.dumps(body).encode("utf-8"),
        )
        assert res.status_code == 404
        assert res.json == {
            "description": f"credential for said {regser.said} not found.",
            "title": "404 Not Found",
        }

        badrev = regser.ked.copy()
        badrev["ri"] = "EIVtei3pGKGUw8H2Ri0h1uOevtSA6QGAq5wifbtHIaNI"
        _, sad = coring.Saider.saidify(badrev)

        badbody = dict(rev=sad, ixn=serder.ked, sigs=sigers)
        res = client.simulate_delete(
            path=f"/identifiers/issuer/credentials/{creder.said}",
            body=json.dumps(badbody).encode("utf-8"),
        )
        assert res.status_code == 404
        assert res.json == {
            "description": "revocation against invalid registry SAID "
            "EIVtei3pGKGUw8H2Ri0h1uOevtSA6QGAq5wifbtHIaNI",
            "title": "404 Not Found",
        }

        badrev = regser.ked.copy()
        badrev["i"] = "EMgdjM1qALk3jlh4P2YyLRSTcjSOjLXD3e_uYpxbdbg6"
        _, sad = coring.Saider.saidify(badrev)

        badbody = dict(rev=sad, ixn=serder.ked, sigs=sigers)
        res = client.simulate_delete(
            path=f"/identifiers/issuer/credentials/{creder.said}",
            body=json.dumps(badbody).encode("utf-8"),
        )
        assert res.status_code == 400
        assert res.json == {
            "description": "invalid revocation event.",
            "title": "400 Bad Request",
        }

        res = client.simulate_delete(
            path=f"/identifiers/issuer/credentials/{creder.said}",
            body=json.dumps(body).encode("utf-8"),
        )
        assert res.status_code == 200

        while not agent.registrar.complete(creder.said, sn=1):
            doist.recur(deeds=deeds)

        res = client.simulate_post("/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]["sad"]["d"] == creder.said
        assert res.json[0]["status"]["s"] == "1"

        res = client.simulate_post("/credentials/query")
        assert res.status_code == 200
        assert len(res.json) == 1
        assert res.json[0]["sad"]["d"] == creder.said
        assert res.json[0]["status"]["s"] == "1"

        res = client.simulate_get(f"/registries/{registry['regk']}/{creder.said}")
        assert res.status_code == 200
        assert res.json["s"] == "1"
        assert res.json["et"] == "rev"


def _setup_credential_issue_routes(app, idResEnd):
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
    credentialRegistryResEnd = credentialing.CredentialRegistryResourceEnd()
    app.add_route("/registries/{ri}/{credential_said}", credentialRegistryResEnd)


def _create_group_member(client, helpers, name, salt):
    helpers.createAid(client, name, salt)
    member = client.simulate_get(f"/identifiers/{name}").json
    _, signers = helpers.incept(salt, "signify:aid", pidx=0)
    return member, signers[0]


def _share_identifier(source, target, name):
    target.parser.parse(ims=source.hby.habByName(name).replay())


def _join_group(client, member, members, group_icp, group_sigs, keys, ndigs):
    prefixes = [record["prefix"] for record in members]
    result = client.simulate_post(
        "/identifiers",
        body=json.dumps(
            dict(
                name="group",
                icp=group_icp.ked,
                sigs=group_sigs,
                smids=prefixes,
                rmids=prefixes,
                group=dict(mhab=member, keys=keys, ndigs=ndigs),
            )
        ),
    )
    assert result.status_code == 202


def _group_interaction(ghab, signers, data):
    serder = keventing.interact(
        pre=ghab.pre,
        dig=ghab.kever.serder.said,
        sn=ghab.kever.sn + 1,
        data=data,
    )
    sigs = [
        signer.sign(ser=serder.raw, index=index).qb64
        for index, signer in enumerate(signers)
    ]
    return serder, sigs


def _run_until(doist, deeds, predicate):
    for _ in range(100):
        doist.recur(deeds=deeds)
        if predicate():
            return
    assert predicate()


def _create_group_registry(client, ghab, signers, agent, doist, deeds, registry=None):
    if registry is None:
        registry = eventing.incept(
            ghab.pre,
            baks=[],
            toad="0",
            nonce=Salter().qb64,
            cnfg=[TraitCodex.NoBackers],
            code=coring.MtrDex.Blake3_256,
        )
    anchor = dict(i=registry.ked["i"], s=registry.ked["s"], d=registry.said)
    kel, sigs = _group_interaction(ghab, signers, [anchor])
    result = client.simulate_post(
        "/identifiers/group/registries",
        body=json.dumps(
            dict(
                name="group-registry",
                vcp=registry.ked,
                ixn=kel.ked,
                sigs=sigs,
                group={},
            )
        ),
    )
    assert result.status_code == 202
    _run_until(doist, deeds, lambda: registry.pre in agent.tvy.tevers)
    return registry


def _build_group_issuance(ghab, signers, registry, recipient, lei):
    dt = "2021-01-01T00:00:00.000000+00:00"
    credential = proving.credential(
        issuer=ghab.pre,
        schema="EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
        recipient=recipient,
        data=dict(LEI=lei, dt=dt),
        source={},
        status=registry.pre,
    )
    tel, kel, body = _build_group_credential_request(
        ghab, signers, registry, credential
    )
    return credential, tel, kel, body


def _build_group_credential_request(ghab, signers, registry, credential):
    tel = eventing.issue(
        vcdig=credential.said,
        regk=registry.pre,
        dt=credential.sad["a"]["dt"],
    )
    anchor = dict(i=tel.ked["i"], s=tel.ked["s"], d=tel.said)
    kel, sigs = _group_interaction(ghab, signers, [anchor])
    body = dict(acdc=credential.sad, iss=tel.ked, ixn=kel.ked, sigs=sigs, group={})
    return tel, kel, body


def _build_issuance_body(
    helpers, registry, iaid, idig, isalt, recp, lei, sn, dig, dt, schema
):
    data = dict(LEI=lei, dt=dt)
    creder = proving.credential(
        issuer=iaid,
        schema=schema,
        recipient=recp,
        data=data,
        source={},
        status=registry["regk"],
    )
    csigers = helpers.sign(bran=isalt, pidx=0, ridx=0, ser=creder.raw)
    regser = eventing.issue(vcdig=creder.said, regk=registry["regk"], dt=dt)
    anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
    serder, sigers = helpers.interact(
        pre=iaid, bran=isalt, pidx=0, ridx=0, dig=dig, sn=sn, data=[anchor]
    )
    pather = coring.Pather(path=[])
    body = dict(
        iss=regser.ked,
        ixn=serder.ked,
        sigs=sigers,
        acdc=creder.sad,
        csigs=csigers,
        path=pather.qb64,
    )
    return creder, body, serder


def test_duplicate_issuance_rejection(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        _setup_credential_issue_routes(app, idResEnd)
        seeder.seedSchema(agent.hby.db)

        serverDoer = helpers.server(agency, httpPort=3905)
        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        isalt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, isalt, doist, deeds)
        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]

        rsalt = b"abcdef0123456789"
        op = helpers.createAid(client, "recipient", rsalt)
        recp = op["response"]["i"]
        helpers.createEndRole(client, agent, recp, "recipient", rsalt)

        dt = "2021-01-01T00:00:00.000000+00:00"
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        creder, body, _ = _build_issuance_body(
            helpers,
            registry,
            iaid,
            idig,
            isalt,
            recp,
            "254900DA0GOGCFVWB618",
            "2",
            idig,
            dt,
            schema,
        )
        issuance_body = json.dumps(body).encode("utf-8")

        result = client.simulate_post(
            path="/identifiers/issuer/credentials", body=issuance_body
        )
        assert result.status_code == 200

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        res = client.simulate_get(f"/credentials/{creder.said}")
        assert res.status_code == 200

        result = client.simulate_post(
            path="/identifiers/issuer/credentials", body=issuance_body
        )
        assert result.status_code == 409
        assert "already issued" in result.json["description"]

        res = client.simulate_get(f"/credentials/{creder.said}")
        assert res.status_code == 200


def test_issuance_rejects_stale_and_persisted_tel_events(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        _setup_credential_issue_routes(app, idResEnd)
        seeder.seedSchema(agent.hby.db)

        serverDoer = helpers.server(agency, httpPort=3906)
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        salt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, salt, doist, deeds)
        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]
        creder, body, _ = _build_issuance_body(
            helpers,
            registry,
            iaid,
            idig,
            salt,
            iaid,
            "254900DA0GOGCFVWB618",
            "2",
            idig,
            "2021-01-01T00:00:00.000000+00:00",
            "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
        )

        staleKed = dict(body["iss"], s="1", d="")
        stale = serdering.SerderKERI(sad=staleKed, makify=True)
        staleBody = dict(body, iss=stale.ked)
        result = client.simulate_post(
            "/identifiers/issuer/credentials", body=json.dumps(staleBody)
        )
        assert result.status_code == 409
        assert "does not chain to current TEL head" in result.json["description"]

        iserder = serdering.SerderKERI(sad=body["iss"])
        assert agent.rgy.reger.putTvt(
            dbing.dgKey(creder.said, iserder.said), iserder.raw
        )
        result = client.simulate_post(
            "/identifiers/issuer/credentials", body=json.dumps(body)
        )
        assert result.status_code == 409
        assert "has already been processed" in result.json["description"]


def test_credential_issuance_requires_interaction_anchor(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        _setup_credential_issue_routes(app, idResEnd)
        seeder.seedSchema(agent.hby.db)

        serverDoer = helpers.server(agency, httpPort=3907)
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        salt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, salt, doist, deeds)
        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]
        creder, body, _ = _build_issuance_body(
            helpers,
            registry,
            iaid,
            idig,
            salt,
            iaid,
            "254900DA0GOGCFVWB618",
            "2",
            idig,
            "2021-01-01T00:00:00.000000+00:00",
            "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
        )
        issuer_hab = agent.hby.habByName("issuer")
        kel_sn = issuer_hab.kever.sn

        without_anchor = dict(body)
        without_anchor.pop("ixn")
        rotation_anchor = dict(body)
        rotation_anchor["rot"] = rotation_anchor.pop("ixn")
        both_anchors = dict(body, rot=body["ixn"])

        for payload, description in (
            (without_anchor, "require an interaction anchor"),
            (rotation_anchor, "only support interaction anchors"),
            (both_anchors, "only support interaction anchors"),
        ):
            result = client.simulate_post(
                "/identifiers/issuer/credentials", body=json.dumps(payload)
            )
            assert result.status_code == 400
            assert description in result.json["description"]
            assert issuer_hab.kever.sn == kel_sn
            assert agent.rgy.tevers[registry["regk"]].vcState(creder.said) is None


def test_duplicate_issuance_rejection_registry_advanced(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        _setup_credential_issue_routes(app, idResEnd)
        seeder.seedSchema(agent.hby.db)

        serverDoer = helpers.server(agency, httpPort=3908)
        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        isalt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, isalt, doist, deeds)
        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]

        rsalt = b"abcdef0123456789"
        op = helpers.createAid(client, "recipient", rsalt)
        recp = op["response"]["i"]
        helpers.createEndRole(client, agent, recp, "recipient", rsalt)

        dt = "2021-01-01T00:00:00.000000+00:00"
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        creder_a, body_a, ixn_a = _build_issuance_body(
            helpers,
            registry,
            iaid,
            idig,
            isalt,
            recp,
            "254900DA0GOGCFVWB618",
            "2",
            idig,
            dt,
            schema,
        )
        issuance_body_a = json.dumps(body_a).encode("utf-8")
        result = client.simulate_post(
            path="/identifiers/issuer/credentials", body=issuance_body_a
        )
        assert result.status_code == 200

        while not agent.credentialer.complete(creder_a.said):
            doist.recur(deeds=deeds)

        res = client.simulate_get(f"/credentials/{creder_a.said}")
        assert res.status_code == 200

        creder_b, body_b, _ = _build_issuance_body(
            helpers,
            registry,
            iaid,
            idig,
            isalt,
            recp,
            "9845004CC7884BN85018",
            "3",
            ixn_a.said,
            dt,
            schema,
        )
        result = client.simulate_post(
            path="/identifiers/issuer/credentials",
            body=json.dumps(body_b).encode("utf-8"),
        )
        assert result.status_code == 200

        while not agent.credentialer.complete(creder_b.said):
            doist.recur(deeds=deeds)

        result = client.simulate_post(
            path="/identifiers/issuer/credentials", body=issuance_body_a
        )
        assert result.status_code == 409
        assert "already issued" in result.json["description"]

        res = client.simulate_get(f"/credentials/{creder_a.said}")
        assert res.status_code == 200

        res = client.simulate_get(f"/credentials/{creder_b.said}")
        assert res.status_code == 200


def test_duplicate_revocation_rejection(helpers, seeder):
    with helpers.openKeria() as (agency, agent, app, client):
        idResEnd = aiding.IdentifierResourceEnd()
        _setup_credential_issue_routes(app, idResEnd)
        seeder.seedSchema(agent.hby.db)

        serverDoer = helpers.server(agency, httpPort=3909)
        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        deeds = doist.enter(doers=[agent, serverDoer])

        isalt = b"0123456789abcdef"
        registry, issuer = helpers.createRegistry(client, agent, isalt, doist, deeds)
        iaid = issuer["prefix"]
        idig = issuer["state"]["d"]

        rsalt = b"abcdef0123456789"
        op = helpers.createAid(client, "recipient", rsalt)
        recp = op["response"]["i"]
        helpers.createEndRole(client, agent, recp, "recipient", rsalt)

        dt = "2021-01-01T00:00:00.000000+00:00"
        schema = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
        creder, body, ixn = _build_issuance_body(
            helpers,
            registry,
            iaid,
            idig,
            isalt,
            recp,
            "254900DA0GOGCFVWB618",
            "2",
            idig,
            dt,
            schema,
        )
        result = client.simulate_post(
            path="/identifiers/issuer/credentials",
            body=json.dumps(body).encode("utf-8"),
        )
        assert result.status_code == 200

        while not agent.credentialer.complete(creder.said):
            doist.recur(deeds=deeds)

        res = client.simulate_get(f"/credentials/{creder.said}")
        assert res.status_code == 200

        iss_regser = eventing.issue(vcdig=creder.said, regk=registry["regk"], dt=dt)
        regser = eventing.revoke(
            vcdig=creder.said, regk=registry["regk"], dig=iss_regser.said, dt=dt
        )
        anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
        serder, sigers = helpers.interact(
            pre=iaid, bran=isalt, pidx=0, ridx=0, dig=ixn.said, sn="3", data=[anchor]
        )
        revoke_body = dict(rev=regser.ked, ixn=serder.ked, sigs=sigers)
        revoke_payload = json.dumps(revoke_body).encode("utf-8")

        res = client.simulate_delete(
            path=f"/identifiers/issuer/credentials/{creder.said}",
            body=revoke_payload,
        )
        assert res.status_code == 200

        while not agent.registrar.complete(creder.said, sn=1):
            doist.recur(deeds=deeds)

        res = client.simulate_delete(
            path=f"/identifiers/issuer/credentials/{creder.said}",
            body=revoke_payload,
        )
        assert res.status_code == 409
        assert "already revoked" in res.json["description"]

        res = client.simulate_get(f"/credentials/{creder.said}")
        assert res.status_code == 200

        res = client.simulate_get(f"/registries/{registry['regk']}/{creder.said}")
        assert res.status_code == 200
        assert res.json["et"] == "rev"


def test_second_member_retry_does_not_block_in_flight_credential(helpers, seeder):
    with (
        helpers.openKeria(salter=Salter(raw=b"0123456789abcM01")) as (
            _,
            agent_one,
            app_one,
            client_one,
        ),
        helpers.openKeria(salter=Salter(raw=b"0123456789abcM02")) as (
            _,
            agent_two,
            app_two,
            client_two,
        ),
    ):
        for app in (app_one, app_two):
            _setup_credential_issue_routes(app, aiding.IdentifierResourceEnd())
        for agent in (agent_one, agent_two):
            seeder.seedSchema(agent.hby.db)

        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        deeds = doist.enter(doers=[agent_one, agent_two])

        member_one, signer_one = _create_group_member(
            client_one, helpers, "member-one", b"0123456789abcM11"
        )
        member_two, signer_two = _create_group_member(
            client_two, helpers, "member-two", b"0123456789abcM12"
        )
        _share_identifier(agent_one, agent_two, "member-one")
        _share_identifier(agent_two, agent_one, "member-two")

        members = [member_one, member_two]
        keys = [member["state"]["k"][0] for member in members]
        ndigs = [member["state"]["n"][0] for member in members]
        group_icp = keventing.incept(
            keys=keys,
            isith="2",
            nsith="2",
            ndigs=ndigs,
            code=coring.MtrDex.Blake3_256,
            toad=0,
            wits=[],
        )
        signers = [signer_one, signer_two]
        group_sigs = [
            signer.sign(ser=group_icp.raw, index=index).qb64
            for index, signer in enumerate(signers)
        ]
        _join_group(client_one, member_one, members, group_icp, group_sigs, keys, ndigs)
        _join_group(client_two, member_two, members, group_icp, group_sigs, keys, ndigs)
        ghab_one = agent_one.hby.habByName("group")
        ghab_two = agent_two.hby.habByName("group")
        assert isinstance(ghab_one, SignifyGroupHab)
        assert isinstance(ghab_two, SignifyGroupHab)

        registry = _create_group_registry(
            client_one, ghab_one, signers, agent_one, doist, deeds
        )
        _share_identifier(agent_one, agent_two, "group")
        _create_group_registry(
            client_two, ghab_two, signers, agent_two, doist, deeds, registry
        )

        holder_one = helpers.createAid(client_one, "holder-one", b"0123456789abcM13")[
            "response"
        ]["i"]
        holder_two = helpers.createAid(client_one, "holder-two", b"0123456789abcM14")[
            "response"
        ]["i"]

        credential_one, _, _, issue_one = _build_group_issuance(
            ghab_one, signers, registry, holder_one, "254900DA0GOGCFVWB618"
        )
        result = client_one.simulate_post(
            "/identifiers/group/credentials", body=json.dumps(issue_one)
        )
        assert result.status_code == 202
        issue_one_op = result.json
        _run_until(
            doist,
            deeds,
            lambda: agent_one.credentialer.complete(credential_one.said),
        )

        # M2 accepts credential 1 from its ACDC, not M1's original request.
        _share_identifier(agent_one, agent_two, "group")
        _, _, accept_one = _build_group_credential_request(
            ghab_two, signers, registry, credential_one
        )
        result = client_two.simulate_post(
            "/identifiers/group/credentials", body=json.dumps(accept_one)
        )
        assert result.status_code == 202
        accept_one_op = result.json
        _run_until(
            doist,
            deeds,
            lambda: agent_two.credentialer.complete(credential_one.said),
        )
        for client, op in (
            (client_one, issue_one_op),
            (client_two, accept_one_op),
        ):
            result = client.simulate_get(f"/operations/{op['name']}")
            assert result.status_code == 200
            assert result.json["done"]
            result = client.simulate_get(f"/credentials/{credential_one.said}")
            assert result.status_code == 200
            assert result.json["iss"]

        # M1 starts credential 2, but M2 has not yet accepted its exchange.
        _share_identifier(agent_two, agent_one, "group")
        credential_two, _, _, issue_two = _build_group_issuance(
            ghab_one, signers, registry, holder_two, "9845004CC7884BN85018"
        )
        result = client_one.simulate_post(
            "/identifiers/group/credentials", body=json.dumps(issue_two)
        )
        assert result.status_code == 202
        issue_two_op = result.json
        assert not agent_two.credentialer.complete(credential_two.said)

        # A stale credential-1 acceptance must be idempotent and leave M2 able
        # to accept the credential-2 exchange afterwards.
        _, _, stale_accept = _build_group_credential_request(
            ghab_two, signers, registry, credential_one
        )
        result = client_two.simulate_post(
            "/identifiers/group/credentials", body=json.dumps(stale_accept)
        )
        assert result.status_code == 202
        assert result.json["done"]

        _share_identifier(agent_one, agent_two, "group")
        _, _, accept_two = _build_group_credential_request(
            ghab_two, signers, registry, credential_two
        )
        result = client_two.simulate_post(
            "/identifiers/group/credentials", body=json.dumps(accept_two)
        )
        assert result.status_code == 202
        accept_two_op = result.json
        _run_until(
            doist,
            deeds,
            lambda: (
                agent_one.credentialer.complete(credential_two.said)
                and agent_two.credentialer.complete(credential_two.said)
            ),
        )

        for client, op in (
            (client_one, issue_two_op),
            (client_two, accept_two_op),
        ):
            result = client.simulate_get(f"/operations/{op['name']}")
            assert result.status_code == 200
            assert result.json["done"]
            result = client.simulate_get(f"/credentials/{credential_two.said}")
            assert result.status_code == 200
            assert result.json["iss"]
