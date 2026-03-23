import datetime
from types import SimpleNamespace

from keri.help import helping
from keri.core import coring
from keri.db import dbing
from keri.vdr import eventing

import pytest
from keria.app import aiding
from keri.kering import ValidationError
from keria.core import longrunning


def test_operations(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)
        locSchemesEnd = aiding.LocSchemeCollectionEnd()
        app.add_route("/identifiers/{name}/locschemes", locSchemesEnd)
        opColEnd = longrunning.OperationCollectionEnd()
        app.add_route("/operations", opColEnd)
        opResEnd = longrunning.OperationResourceEnd()
        app.add_route("/operations/{name}", opResEnd)

        # operations is empty

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 0

        res = client.simulate_get(path="/operations?type=endrole")
        assert isinstance(res.json, list)
        assert len(res.json) == 0

        # create aid

        salt = b"C6X8UfJqYrOmJQHKqnI5a"
        op = helpers.createAid(client, "user1", salt)
        assert op["done"] is True
        assert op["name"] == "done.EAF7geUfHm-M5lA-PI6Jv-4708a-KknnlMlA7U1_Wduv"
        aid = op["response"]
        recp = aid["i"]
        assert recp == "EAF7geUfHm-M5lA-PI6Jv-4708a-KknnlMlA7U1_Wduv"

        # operations has 1 element

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 1
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r == op

        res = client.simulate_get(path="/operations?type=endrole")
        assert isinstance(res.json, list)
        assert len(res.json) == 0
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r is None

        # add endrole

        rpy = helpers.endrole(recp, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)
        res = client.simulate_post(path="/identifiers/user1/endroles", json=body)
        op = res.json
        assert op["done"] is True
        assert (
            op["name"]
            == "endrole.EAF7geUfHm-M5lA-PI6Jv-4708a-KknnlMlA7U1_Wduv.agent.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"
        )

        # operations has 2 elements

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 2
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r == op

        res = client.simulate_get(path="/operations?type=endrole")
        assert isinstance(res.json, list)
        assert len(res.json) == 1
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r == op

        # create aid

        salt = b"tRkaivxZkQPfqjlDY6j1K"
        op = helpers.createAid(client, "user2", salt)
        assert op["done"] is True
        assert op["name"] == "done.EAyXphfc0qOLqEDAe0cCYCj-ovbSaEFgVgX6MrC_b5ZO"
        aid = op["response"]
        recp = aid["i"]
        assert recp == "EAyXphfc0qOLqEDAe0cCYCj-ovbSaEFgVgX6MrC_b5ZO"

        # operations has 3 elements

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 3
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r == op

        res = client.simulate_get(path="/operations?type=endrole")
        assert isinstance(res.json, list)
        assert len(res.json) == 1
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r is None

        # add endrole

        rpy = helpers.endrole(recp, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)
        res = client.simulate_post(path="/identifiers/user2/endroles", json=body)
        op = res.json
        assert op["done"] is True
        assert (
            op["name"]
            == "endrole.EAyXphfc0qOLqEDAe0cCYCj-ovbSaEFgVgX6MrC_b5ZO.agent.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"
        )

        # operations has 4 elements

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 4
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r == op

        res = client.simulate_get(path="/operations?type=endrole")
        assert isinstance(res.json, list)
        assert len(res.json) == 2
        r = next(filter(lambda i: i["name"] == op["name"], res.json), None)
        assert r == op

        # GET /operations returns same as each GET /operations/{name}

        res = client.simulate_get(path="/operations")
        for i in res.json:
            t = client.simulate_get(path=f"/operations/{i['name']}")
            assert i == t.json

        # delete by type

        res = client.simulate_get(path="/operations?type=endrole")
        for i in res.json:
            t = client.simulate_delete(path=f"/operations/{i['name']}")
            assert t.status_code == 204

        # operations has 2 remaining

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 2

        # delete remaining

        res = client.simulate_get(path="/operations")
        for i in res.json:
            t = client.simulate_delete(path=f"/operations/{i['name']}")
            assert t.status_code == 204

        # operations has 0 remaining

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 0

        op = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.query,
                oid=f"{recp}.0",
                start=helping.nowIso8601(),
                metadata={"pre": recp, "sn": "0"},
            )
        )
        assert op.name == f"query.{recp}.0"
        assert op.done is True

        op = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.query,
                oid=f"{recp}.4",
                start=helping.nowIso8601(),
                metadata={"pre": recp, "sn": "4"},
            )
        )
        assert op.name == f"query.{recp}.4"
        assert op.done is False

        # add loc scheme

        rpy = helpers.locscheme(recp, "http://testurl.com")
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)
        res = client.simulate_post(path="/identifiers/user2/locschemes", json=body)
        op = res.json
        assert op["done"] is True
        assert (
            op["name"] == "locscheme.EAyXphfc0qOLqEDAe0cCYCj-ovbSaEFgVgX6MrC_b5ZO.http"
        )


def test_operation_bad_metadata(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        # Witness
        witop = longrunning.Op(
            type=longrunning.OpTypes.witness,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )

        with pytest.raises(ValidationError) as err:
            witop.metadata = {"pre": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1"}
            agent.monitor.status(witop)
        assert (
            str(err.value)
            == "invalid long running witness operation, metadata missing required fields ('pre', 'sn')"
        )

        with pytest.raises(ValidationError) as err:
            witop.metadata = {"sn": "0"}
            agent.monitor.status(witop)
        assert (
            str(err.value)
            == "invalid long running witness operation, metadata missing required fields ('pre', 'sn')"
        )

        # Oobi
        oobiop = longrunning.Op(
            type=longrunning.OpTypes.oobi,
            oid="oobioid",
            start=helping.nowIso8601(),
            metadata={},
        )
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(oobiop)
        assert str(err.value) == "invalid OOBI long running operation, missing oobi"

        # Delegation
        delop = longrunning.Op(
            type=longrunning.OpTypes.delegation,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(delop)
        assert (
            str(err.value)
            == "invalid long running delegation operation, metadata missing required field 'pre'"
        )

        # Group
        groupop = longrunning.Op(
            type=longrunning.OpTypes.group,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )

        with pytest.raises(ValidationError) as err:
            groupop.metadata = {"pre": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1"}
            agent.monitor.status(groupop)
        assert (
            str(err.value)
            == "invalid long running group operation, metadata missing required fields ('pre', 'sn')"
        )

        with pytest.raises(ValidationError) as err:
            groupop.metadata = {"sn": "0"}
            agent.monitor.status(groupop)
        assert (
            str(err.value)
            == "invalid long running group operation, metadata missing required fields ('pre', 'sn')"
        )

        # Query
        queryop = longrunning.Op(
            type=longrunning.OpTypes.query,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(queryop)
        assert (
            str(err.value)
            == "invalid long running query operation, metadata missing required field 'pre'"
        )

        # Registry
        registryop = longrunning.Op(
            type=longrunning.OpTypes.registry,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )

        with pytest.raises(ValidationError) as err:
            registryop.metadata = {
                "pre": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1"
            }
            agent.monitor.status(registryop)
        assert (
            str(err.value)
            == "invalid long running registry operation, metadata missing required fields ('pre', 'anchor')"
        )

        with pytest.raises(ValidationError) as err:
            registryop.metadata = {
                "anchor": {
                    "i": "EKQSWRXh_JHX61NdrL6wJ8ELMwG4zFY8y-sU1nymYzXZ",
                    "s": "1",
                    "d": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY",
                }
            }
            agent.monitor.status(registryop)
        assert (
            str(err.value)
            == "invalid long running registry operation, metadata missing required fields ('pre', 'anchor')"
        )

        # Credential
        credop = longrunning.Op(
            type=longrunning.OpTypes.credential,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(credop)
        assert (
            str(err.value)
            == "invalid long running credential operation, metadata missing 'ced' field"
        )

        # End role
        endop = longrunning.Op(
            type=longrunning.OpTypes.endrole,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )

        with pytest.raises(ValidationError) as err:
            endop.metadata = {
                "cid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                "role": "agent",
            }
            agent.monitor.status(endop)
        assert (
            str(err.value)
            == "invalid long running endrole operation, metadata missing required fields ('cid', 'role', 'eid')"
        )

        with pytest.raises(ValidationError) as err:
            endop.metadata = {
                "cid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                "eid": "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9",
            }
            agent.monitor.status(endop)
        assert (
            str(err.value)
            == "invalid long running endrole operation, metadata missing required fields ('cid', 'role', 'eid')"
        )

        with pytest.raises(ValidationError) as err:
            endop.metadata = {
                "role": "agent",
                "eid": "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9",
            }
            agent.monitor.status(endop)
        assert (
            str(err.value)
            == "invalid long running endrole operation, metadata missing required fields ('cid', 'role', 'eid')"
        )

        # LocScheme
        locop = longrunning.Op(
            type=longrunning.OpTypes.locscheme,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )

        with pytest.raises(ValidationError) as err:
            locop.metadata = {
                "eid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                "scheme": "http",
            }
            agent.monitor.status(locop)
        assert (
            str(err.value)
            == "invalid long running locscheme operation, metadata missing required fields ('eid', 'scheme', 'url')"
        )

        with pytest.raises(ValidationError) as err:
            locop.metadata = {
                "eid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                "url": "http://testurl.com",
            }
            agent.monitor.status(locop)
        assert (
            str(err.value)
            == "invalid long running locscheme operation, metadata missing required fields ('eid', 'scheme', 'url')"
        )

        with pytest.raises(ValidationError) as err:
            locop.metadata = {"scheme": "http", "url": "http://testurl.com"}
            agent.monitor.status(locop)
        assert (
            str(err.value)
            == "invalid long running locscheme operation, metadata missing required fields ('eid', 'scheme', 'url')"
        )

        # Challenge
        challengeop = longrunning.Op(
            type=longrunning.OpTypes.challenge,
            oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
            start=helping.nowIso8601(),
            metadata={},
        )
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(challengeop)
        assert (
            str(err.value)
            == "invalid long running challenge operation, metadata missing 'words' field"
        )


def test_error(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        opColEnd = longrunning.OperationCollectionEnd()
        app.add_route("/operations", opColEnd)
        opResEnd = longrunning.OperationResourceEnd()
        app.add_route("/operations/{name}", opResEnd)

        err = None
        try:
            # submitting an invalid non-existing witness operation to mock error condition
            agent.monitor.submit(
                "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
                longrunning.OpTypes.witness,
                dict(),
            )
        except ValidationError as e:
            err = e

        assert err is not None

        res = client.simulate_get(path="/operations")
        assert isinstance(res.json, list)
        assert len(res.json) == 1

        op = res.json[0]
        assert op["done"]
        assert op["error"]["code"] == 500
        assert op["error"]["message"] == f"{err}"

        res = client.simulate_get(path=f"/operations/{op['name']}")
        assert res.status_code == 500

        # Test other error conditions
        res = client.simulate_get(
            path="/operations/exchange.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
        )
        assert res.status_code == 404
        assert res.json == {
            "title": "long running operation 'exchange.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao' not found"
        }


def test_regsync_status(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        pre = agent.agentHab.pre
        regk = "ERegsyncRegistry0000000000000000000000000000000000000"
        agent.registrar.rgy.reger._tevers = {}
        base = dict(
            pre=pre,
            source="ESource000000000000000000000000000000000000000",
            request="ERequest00000000000000000000000000000000000000",
            targets=[],
            error=None,
        )

        pending_catalog = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.regsync,
                oid=pre,
                start=helping.nowIso8601(),
                metadata={
                    **base,
                    "phase": "catalog",
                    "phase_start": helping.nowIso8601(),
                },
            )
        )
        assert pending_catalog.name == f"regsync.{pre}"
        assert pending_catalog.done is False

        timed_out_catalog = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.regsync,
                oid=pre,
                start=helping.nowIso8601(),
                metadata={
                    **base,
                    "phase": "catalog",
                    "phase_start": helping.toIso8601(
                        helping.nowUTC() - datetime.timedelta(seconds=11)
                    ),
                },
            )
        )
        assert timed_out_catalog.done is True
        assert timed_out_catalog.error.code == 504

        agent.rgy.regs[regk] = SimpleNamespace(name="registry", regk=regk)
        agent.rgy.tevers[regk] = SimpleNamespace(sn=0)
        pending_replay = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.regsync,
                oid=pre,
                start=helping.nowIso8601(),
                metadata={
                    **base,
                    "phase": "replay",
                    "phase_start": helping.nowIso8601(),
                    "targets": [dict(name="registry", regk=regk, sn=1)],
                },
            )
        )
        assert pending_replay.done is False

        agent.rgy.tevers[regk] = SimpleNamespace(sn=1)
        completed_replay = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.regsync,
                oid=pre,
                start=helping.nowIso8601(),
                metadata={
                    **base,
                    "phase": "replay",
                    "phase_start": helping.nowIso8601(),
                    "targets": [dict(name="registry", regk=regk, sn=1)],
                },
            )
        )
        assert completed_replay.done is True
        assert completed_replay.response == {
            "pre": pre,
            "source": base["source"],
            "synced": [dict(name="registry", regk=regk, sn=1)],
        }

        failed = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.regsync,
                oid=pre,
                start=helping.nowIso8601(),
                metadata={
                    **base,
                    "phase": "catalog",
                    "phase_start": helping.nowIso8601(),
                    "error": dict(code=424, message="bad response", details={"regk": regk}),
                },
            )
        )
        assert failed.done is True
        assert failed.error.code == 424
        assert failed.error.details == {"regk": regk}


def test_regsync_backfills_registry_anchor(helpers, monkeypatch):
    with helpers.openKeria() as (agency, agent, app, client):
        pre = agent.agentHab.pre
        regk = "ERegsyncAnchor00000000000000000000000000000000000000"
        regd = "ERegsyncAnchorSaid0000000000000000000000000000000000"
        seal = dict(i=regk, s="0", d=regd)
        source_serder = agent.agentHab.kever.serder

        agent.registrar.rgy.reger._tevers = {}
        agent.rgy.regs[regk] = SimpleNamespace(name="registry", regk=regk)
        agent.rgy.tevers[regk] = SimpleNamespace(sn=0)

        monkeypatch.setattr(
            agent.hby.db,
            "fetchLastSealingEventByEventSeal",
            lambda pre, seal: source_serder,
        )

        op = agent.monitor.status(
            longrunning.Op(
                type=longrunning.OpTypes.regsync,
                oid=pre,
                start=helping.nowIso8601(),
                metadata=dict(
                    pre=pre,
                    source="ESource000000000000000000000000000000000000000",
                    phase="replay",
                    phase_start=helping.nowIso8601(),
                    request="ERequest00000000000000000000000000000000000000",
                    targets=[dict(name="registry", regk=regk, regd=regd, anc=seal, sn=0)],
                    error=None,
                ),
            )
        )

        assert op.done is True
        assert (
            agent.rgy.reger.getAnc(dbing.dgKey(regk, regd))
            == coring.Seqner(sn=source_serder.sn).qb64b
            + coring.Saider(qb64=source_serder.said).qb64b
        )


def test_credsync_backfills_tel_anchor(helpers, monkeypatch):
    with helpers.openKeria() as (agency, agent, app, client):
        gid = agent.agentHab.pre
        source_serder = agent.agentHab.kever.serder
        rserder = eventing.revoke(
            vcdig=source_serder.said,
            regk=source_serder.said,
            dig=source_serder.said,
            dt="2023-09-27T16:27:14.376928+00:00",
        )
        seal = dict(i=rserder.pre, s=rserder.snh, d=rserder.said)

        monkeypatch.setattr(
            agent.hby.db,
            "fetchLastSealingEventByEventSeal",
            lambda pre, seal: source_serder,
        )

        assert (
            longrunning.ensure_tel_anchor(
                hby=agent.hby,
                reger=agent.rgy.reger,
                gid=gid,
                pre=rserder.pre,
                said=rserder.said,
                anchor=seal,
            )
            is True
        )
        assert (
            agent.rgy.reger.getAnc(dbing.dgKey(rserder.pre, rserder.said))
            == coring.Seqner(sn=source_serder.sn).qb64b
            + coring.Saider(qb64=source_serder.said).qb64b
        )


def test_credsync_status(helpers, monkeypatch):
    with helpers.openKeria() as (agency, agent, app, client):
        pre = agent.agentHab.pre
        regk = "ECredsyncRegistry00000000000000000000000000000000000"
        said = "ECredsyncCredential0000000000000000000000000000000"
        base = dict(
            pre=pre,
            source="ESource000000000000000000000000000000000000000",
            phase="replay",
            phase_start=helping.nowIso8601(),
            request="ERequest00000000000000000000000000000000000000",
            saids=[said],
            synced=[],
            error=None,
        )

        original_saved = agent.registrar.rgy.reger.saved
        original_clone_cred = agent.registrar.rgy.reger.cloneCred
        original_tevers = agent.registrar.rgy.reger._tevers
        try:
            agent.registrar.rgy.reger._tevers = {}
            agent.registrar.rgy.reger.saved = SimpleNamespace(get=lambda keys: None)
            pending = agent.monitor.status(
                longrunning.Op(
                    type=longrunning.OpTypes.credsync,
                    oid=pre,
                    start=helping.nowIso8601(),
                    metadata=base,
                )
            )
            assert pending.name == f"credsync.{pre}"
            assert pending.done is False

            agent.registrar.rgy.reger.saved = SimpleNamespace(
                get=lambda keys: said if keys == (said,) else None
            )
            agent.registrar.rgy.reger.cloneCred = lambda said: (
                SimpleNamespace(regi=regk, sad={"ri": regk}),
                None,
                None,
                None,
            )
            agent.rgy.regs[regk] = SimpleNamespace(name="registry", regk=regk)
            ready = False
            escrow_calls = []

            monkeypatch.setattr(
                agent.registrar.rgy,
                "processEscrows",
                lambda: escrow_calls.append("rgy"),
            )
            monkeypatch.setattr(
                agent.credentialer.verifier,
                "processEscrows",
                lambda: escrow_calls.append("verifier"),
            )
            monkeypatch.setattr(
                agent.registrar,
                "processEscrows",
                lambda: escrow_calls.append("registrar"),
            )
            monkeypatch.setattr(
                agent.credentialer,
                "processEscrows",
                lambda: escrow_calls.append("credentialer"),
            )
            agent.registrar.rgy.reger._tevers[regk] = SimpleNamespace(
                vcState=lambda vci: SimpleNamespace(sn=0, et="iss") if ready else None
            )

            pending_tel = agent.monitor.status(
                longrunning.Op(
                    type=longrunning.OpTypes.credsync,
                    oid=pre,
                    start=helping.nowIso8601(),
                    metadata=base,
                )
            )
            assert pending_tel.done is False
            assert escrow_calls == ["rgy", "verifier", "registrar", "credentialer"]

            ready = True
            escrow_calls.clear()
            completed = agent.monitor.status(
                longrunning.Op(
                    type=longrunning.OpTypes.credsync,
                    oid=pre,
                    start=helping.nowIso8601(),
                    metadata={**base, "synced": [said]},
                )
            )
            assert completed.done is True
            assert escrow_calls == ["rgy", "verifier", "registrar", "credentialer"]
            assert completed.response == {
                "pre": pre,
                "source": base["source"],
                "synced": [said],
            }

            failed = agent.monitor.status(
                longrunning.Op(
                    type=longrunning.OpTypes.credsync,
                    oid=pre,
                    start=helping.nowIso8601(),
                    metadata={
                        **base,
                        "error": dict(code=424, message="bad response", details={"said": said}),
                    },
                )
            )
            assert failed.done is True
            assert failed.error.code == 424
            assert failed.error.details == {"said": said}
        finally:
            agent.registrar.rgy.reger.saved = original_saved
            agent.registrar.rgy.reger.cloneCred = original_clone_cred
            agent.registrar.rgy.reger._tevers = original_tevers
