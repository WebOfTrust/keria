# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.indirecting module

Testing the Mark II Agent
"""
import falcon.testing
from hio.help import Hict
from keri import core
from keri.app import habbing, httping
from keri.core import coring, serdering
from keri.core.coring import MtrDex
from keri.core.signing import Salter
from keri.vdr import eventing
from keria.end import ending

from keria.app import indirecting, aiding


def test_indirecting(helpers):
    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)
    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:

        indirecting.loadEnds(app, agency)
        end = aiding.IdentifierCollectionEnd()
        resend = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers", end)
        app.add_route("/identifiers/{name}", resend)
        op = helpers.createAid(client, "recipient", salt)
        aid = op["response"]

        assert aid["i"] == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        hab = hby.makeHab("test")
        icp = hab.makeOwnInception()
        serder = serdering.SerderKERI(raw=icp)
        atc = icp[:serder.size]

        client = falcon.testing.TestClient(app)

        res = client.post("/", body=serder.raw)
        assert res.status_code == 400
        assert res.json == {'title': 'CESR request destination header missing'}

        badaid = "EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3"
        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{serder.size}"),
            ("connection", "close"),
            (httping.CESR_ATTACHMENT_HEADER, bytearray(atc).decode("utf-8")),
            (httping.CESR_DESTINATION_HEADER, badaid)
        ])

        res = client.post("/", body=serder.raw, headers=dict(headers))
        assert res.status_code == 404
        assert res.json == {'title': 'unknown destination AID EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3'}

        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{serder.size}"),
            ("connection", "close"),
            (httping.CESR_ATTACHMENT_HEADER, bytearray(atc).decode("utf-8")),
            (httping.CESR_DESTINATION_HEADER, aid["i"])
        ])

        res = client.post("/", body=serder.raw, headers=dict(headers))
        assert res.status_code == 204

        # Regular (non-mbx) query messages accepted
        msg = hab.query(pre=hab.pre, src=hab.pre, route="ksn")
        serder = serdering.SerderKERI(raw=msg)
        atc = msg[:serder.size]

        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{serder.size}"),
            ("connection", "close"),
            (httping.CESR_ATTACHMENT_HEADER, bytearray(atc).decode("utf-8")),
            (httping.CESR_DESTINATION_HEADER, aid["i"])
        ])

        res = client.post("/", body=serder.raw, headers=dict(headers))
        assert res.status_code == 204

        # Mailbox query not found
        msg = hab.query(pre=hab.pre, src=hab.pre, route="mbx")
        serder = serdering.SerderKERI(raw=msg)
        atc = msg[:serder.size]

        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{serder.size}"),
            ("connection", "close"),
            (httping.CESR_ATTACHMENT_HEADER, bytearray(atc).decode("utf-8")),
            (httping.CESR_DESTINATION_HEADER, aid["i"])
        ])

        res = client.post("/", body=serder.raw, headers=dict(headers))
        assert res.status_code == 404
        assert res.json == {'title': 'no mailbox support in KERIA'}

        # Try credential event (registry inception)
        regser = eventing.incept(hab.pre,
                                 baks=[],
                                 toad="0",
                                 nonce=Salter().qb64,
                                 cnfg=[],
                                 code=MtrDex.Blake3_256)
        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{regser.size}"),
            ("connection", "close"),
            (httping.CESR_ATTACHMENT_HEADER, bytearray(atc).decode("utf-8")),
            (httping.CESR_DESTINATION_HEADER, aid["i"])
        ])

        res = client.post("/", body=regser.raw, headers=dict(headers))
        assert res.status_code == 204

        # Test PUT method
        res = client.put("/", body=serder.raw)
        assert res.status_code == 400
        assert res.json == {'title': 'CESR request destination header missing'}

        badaid = "EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3"
        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{serder.size}"),
            ("connection", "close"),
            (httping.CESR_DESTINATION_HEADER, badaid)
        ])

        body = serder.raw + atc
        res = client.put("/", body=body, headers=dict(headers))
        assert res.status_code == 404
        assert res.json == {'title': 'unknown destination AID EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3'}

        headers = Hict([
            ("Content-Type", httping.CESR_CONTENT_TYPE),
            ("Content-Length", f"{serder.size}"),
            ("connection", "close"),
            (httping.CESR_ATTACHMENT_HEADER, bytearray(atc).decode("utf-8")),
            (httping.CESR_DESTINATION_HEADER, aid["i"])
        ])

        res = client.put("/", body=serder.raw, headers=dict(headers))
        assert res.status_code == 204

        # Test ending
        oobiEnd = ending.OOBIEnd(agency)
        app.add_route("/oobi", oobiEnd)
        app.add_route("/oobi/{aid}", oobiEnd)
        app.add_route("/oobi/{aid}/{role}", oobiEnd)
        app.add_route("/oobi/{aid}/{role}/{eid}", oobiEnd)

        result = client.simulate_get(path="/oobi/EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY/role")
        assert result.status == falcon.HTTP_200

        result = client.simulate_get(path="/oobi/EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3")
        assert result.status == falcon.HTTP_404

