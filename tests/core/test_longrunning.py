from keri.help import helping

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
        recp = aid['i']
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
        res = client.simulate_post(
            path="/identifiers/user1/endroles", json=body)
        op = res.json
        assert op["done"] is True
        assert op["name"] == "endrole.EAF7geUfHm-M5lA-PI6Jv-4708a-KknnlMlA7U1_Wduv.agent.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"

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
        recp = aid['i']
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
        res = client.simulate_post(
            path="/identifiers/user2/endroles", json=body)
        op = res.json
        assert op["done"] is True
        assert op["name"] == "endrole.EAyXphfc0qOLqEDAe0cCYCj-ovbSaEFgVgX6MrC_b5ZO.agent.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"

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
            longrunning.Op(type=longrunning.OpTypes.query, oid=f"{recp}.0", start=helping.nowIso8601(), metadata={'pre': recp, 'sn': '0'}))
        assert op.name == f"query.{recp}.0"
        assert op.done is True

        op = agent.monitor.status(
            longrunning.Op(type=longrunning.OpTypes.query, oid=f"{recp}.4", start=helping.nowIso8601(), metadata={'pre': recp, 'sn': '4'}))
        assert op.name == f"query.{recp}.4"
        assert op.done is False

        # add loc scheme

        rpy = helpers.locscheme(recp, "http://testurl.com")
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)
        res = client.simulate_post(
            path="/identifiers/user2/locschemes", json=body)
        op = res.json
        assert op["done"] is True
        assert op["name"] == "locscheme.EAyXphfc0qOLqEDAe0cCYCj-ovbSaEFgVgX6MrC_b5ZO.http"


def test_operation_bad_metadata(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        # Witness
        witop = longrunning.Op(type=longrunning.OpTypes.witness, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                               start=helping.nowIso8601(), metadata={})

        with pytest.raises(ValidationError) as err:
            witop.metadata = {"pre": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1"}
            agent.monitor.status(witop)
        assert str(err.value) == "invalid long running witness operation, metadata missing required fields ('pre', 'sn')"

        with pytest.raises(ValidationError) as err:
            witop.metadata = {"sn": "0"}
            agent.monitor.status(witop)
        assert str(err.value) == "invalid long running witness operation, metadata missing required fields ('pre', 'sn')"

        # Oobi
        oobiop = longrunning.Op(type=longrunning.OpTypes.oobi, oid="oobioid",
                               start=helping.nowIso8601(), metadata={})
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(oobiop)
        assert str(err.value) == "invalid OOBI long running operation, missing oobi"

        # Delegation
        delop = longrunning.Op(type=longrunning.OpTypes.delegation, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                                start=helping.nowIso8601(), metadata={})
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(delop)
        assert str(err.value) == "invalid long running delegation operation, metadata missing required field 'pre'"

        # Group
        groupop = longrunning.Op(type=longrunning.OpTypes.group, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                               start=helping.nowIso8601(), metadata={})

        with pytest.raises(ValidationError) as err:
            groupop.metadata = {"pre": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1"}
            agent.monitor.status(groupop)
        assert str(err.value) == "invalid long running group operation, metadata missing required fields ('pre', 'sn')"

        with pytest.raises(ValidationError) as err:
            groupop.metadata = {"sn": "0"}
            agent.monitor.status(groupop)
        assert str(err.value) == "invalid long running group operation, metadata missing required fields ('pre', 'sn')"

        # Query
        queryop = longrunning.Op(type=longrunning.OpTypes.query, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                               start=helping.nowIso8601(), metadata={})
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(queryop)
        assert str(err.value) == "invalid long running query operation, metadata missing required field 'pre'"

        # Registry
        registryop = longrunning.Op(type=longrunning.OpTypes.registry, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                                 start=helping.nowIso8601(), metadata={})

        with pytest.raises(ValidationError) as err:
            registryop.metadata = {"pre": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1"}
            agent.monitor.status(registryop)
        assert str(err.value) == "invalid long running registry operation, metadata missing required fields ('pre', 'anchor')"

        with pytest.raises(ValidationError) as err:
            registryop.metadata = {"anchor":
                                       {"i": "EKQSWRXh_JHX61NdrL6wJ8ELMwG4zFY8y-sU1nymYzXZ",
                                        "s": "1",
                                        "d": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"}}
            agent.monitor.status(registryop)
        assert str(err.value) == "invalid long running registry operation, metadata missing required fields ('pre', 'anchor')"

        # Credential
        credop = longrunning.Op(type=longrunning.OpTypes.credential, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                               start=helping.nowIso8601(), metadata={})
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(credop)
        assert str(err.value) == "invalid long running credential operation, metadata missing 'ced' field"

        # End role
        endop = longrunning.Op(type=longrunning.OpTypes.endrole, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                               start=helping.nowIso8601(), metadata={})

        with pytest.raises(ValidationError) as err:
            endop.metadata = {"cid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1", "role": "agent"}
            agent.monitor.status(endop)
        assert str(err.value) == "invalid long running endrole operation, metadata missing required fields ('cid', 'role', 'eid')"

        with pytest.raises(ValidationError) as err:
            endop.metadata = {"cid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1", "eid": "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"}
            agent.monitor.status(endop)
        assert str(err.value) == "invalid long running endrole operation, metadata missing required fields ('cid', 'role', 'eid')"

        with pytest.raises(ValidationError) as err:
            endop.metadata = {"role": "agent", "eid": "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"}
            agent.monitor.status(endop)
        assert str(err.value) == "invalid long running endrole operation, metadata missing required fields ('cid', 'role', 'eid')"

        # LocScheme
        locop = longrunning.Op(type=longrunning.OpTypes.locscheme, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                               start=helping.nowIso8601(), metadata={})

        with pytest.raises(ValidationError) as err:
            locop.metadata = {"eid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1", "scheme": "http"}
            agent.monitor.status(locop)
        assert str(err.value) == "invalid long running locscheme operation, metadata missing required fields ('eid', 'scheme', 'url')"

        with pytest.raises(ValidationError) as err:
            locop.metadata = {"eid": "EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1", "url": "http://testurl.com"}
            agent.monitor.status(locop)
        assert str(err.value) == "invalid long running locscheme operation, metadata missing required fields ('eid', 'scheme', 'url')"

        with pytest.raises(ValidationError) as err:
            locop.metadata = {"scheme": "http", "url": "http://testurl.com"}
            agent.monitor.status(locop)
        assert str(err.value) == "invalid long running locscheme operation, metadata missing required fields ('eid', 'scheme', 'url')"

        # Challenge
        challengeop = longrunning.Op(type=longrunning.OpTypes.challenge, oid="EIsavDv6zpJDPauh24RSCx00jGc6VMe3l84Y8pPS8p-1",
                                  start=helping.nowIso8601(), metadata={})
        with pytest.raises(ValidationError) as err:
            agent.monitor.status(challengeop)
        assert str(err.value) == "invalid long running challenge operation, metadata missing 'words' field"


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
                "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao", longrunning.OpTypes.witness, dict())
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
        res = client.simulate_get(path="/operations/exchange.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        assert res.status_code == 404
        assert res.json == {
            'title': "long running operation 'exchange.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao' not found"
        }

        res = client.simulate_get(path="/operations/query.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        assert res.status_code == 404
        assert res.json == {'title': 'long running operation '
                                     "'query.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao' not found"}
