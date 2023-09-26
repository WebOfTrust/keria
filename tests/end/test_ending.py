# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ending module

Testing the Mark II Agent Grouping endpoints

"""
from keri.core import coring

from keria.app import aiding
from keria.end import ending


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        ending.loadEnds(app=app, agency=agency)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/oobi")
        assert isinstance(end, ending.OOBIEnd)
        (end, *_) = app._router.find("/oobi/AID")
        assert isinstance(end, ending.OOBIEnd)
        (end, *_) = app._router.find("/oobi/AID/ROLE")
        assert isinstance(end, ending.OOBIEnd)
        (end, *_) = app._router.find("/oobi/AID/ROLE/EID")
        assert isinstance(end, ending.OOBIEnd)


def test_oobi_end(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        ending.loadEnds(app=app, agency=agency)

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)

        # First create participants (aid1, aid2) in a multisig AID
        salt = b'0123456789abcdef'
        op = helpers.createAid(client, "aid1", salt)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        recp = aid['i']
        rpy = helpers.endrole(recp, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)

        res = client.simulate_post(path=f"/identifiers/aid1/endroles", json=body)
        op = res.json
        ked = op["response"]
        serder = coring.Serder(ked=ked)
        assert serder.raw == rpy.raw

        res = client.simulate_get(path=f"/oobi")
        assert res.status_code == 404
        assert res.json == {'description': 'no blind oobi for this node', 'title': '404 Not Found'}

        # Use a bad AID
        res = client.simulate_get(path=f"/oobi/EHXXXXXT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSys")
        assert res.status_code == 404
        assert res.json == {'description': 'AID not found for this OOBI', 'title': '404 Not Found'}

        # Use valid AID
        res = client.simulate_get(path=f"/oobi/{pre}")
        assert res.status_code == 200
        assert res.headers['Content-Type'] == "application/json+cesr"

        # Use valid AID, role and EID
        res = client.simulate_get(path=f"/oobi/{pre}/agent/{agent.agentHab.pre}")
        assert res.status_code == 200
        assert res.headers['Content-Type'] == "application/json+cesr"
