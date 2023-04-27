# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.credentialing module

Testing credentialing endpoint in the Mark II Agent
"""
import falcon
from falcon import testing
from keri.core import scheming, coring

from keria.app import credentialing, aiding


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        credentialing.loadEnds(app=app)
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

        client = testing.TestClient(app)
        registryEnd = credentialing.RegistryEnd()
        app.add_route("/registries", registryEnd)

        seeder.seedSchema(agent.hby.db)
        result = client.simulate_post(path="/registries", body=b'{}')
        assert result.status == falcon.HTTP_400  # Bad request, missing name

        result = client.simulate_post(path="/registries", body=b'{"name": "test"}')
        assert result.status == falcon.HTTP_400  # Bad Request, missing alias

        result = client.simulate_post(path="/registries", body=b'{"name": "test", "alias": "test123"}')
        assert result.status == falcon.HTTP_404  # Bad Request, invalid alias

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        salt = b'0123456789abcdef'
        aid = helpers.createAid(client, "test", salt)
        assert aid['i'] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        # Test all the parameters
        result = client.simulate_post(path="/registries",
                                      body=b'{"name": "test-full", "alias": "test",'
                                           b' "noBackers": true, "baks": [], "toad": 0, "estOnly": false}')
        assert result.status == falcon.HTTP_202
        agent.rgy.processEscrows()

        result = client.simulate_post(path="/registries", body=b'{"name": "test", "alias": "test"}')
        assert result.status == falcon.HTTP_202
        agent.rgy.processEscrows()

        result = client.simulate_get(path="/registries")
        assert result.status == falcon.HTTP_200
        # assert len(result.json) == 2
        assert len(result.json) == 0
