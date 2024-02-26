from keri.help import helping

from keria.app import aiding
from keri.kering import ValidationError
from keria.core import longrunning


def test_operations(helpers):
    with helpers.openKeria() as (agency, agent, app, client):

        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        endRolesEnd = aiding.EndRoleCollectionEnd()
        app.add_route("/identifiers/{name}/endroles", endRolesEnd)
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
        assert r == None

        # add endrole

        rpy = helpers.endrole(recp, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)
        res = client.simulate_post(
            path=f"/identifiers/user1/endroles", json=body)
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
        assert r == None

        # add endrole

        rpy = helpers.endrole(recp, agent.agentHab.pre)
        sigs = helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)
        res = client.simulate_post(
            path=f"/identifiers/user2/endroles", json=body)
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
            longrunning.Op(type='query', oid=recp, start=helping.nowIso8601(), metadata={'sn': '0'}))
        assert op.name == f"query.{recp}"
        assert op.done is True

        op = agent.monitor.status(
            longrunning.Op(type='query', oid=recp, start=helping.nowIso8601(), metadata={'sn': '4'}))
        assert op.name == f"query.{recp}"
        assert op.done is False


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
        assert op["done"] == True
        assert op["error"]["code"] == 500
        assert op["error"]["message"] == f"{err}"

        res = client.simulate_get(path=f"/operations/{op['name']}")
        assert res.status_code == 500

        # Test other error conditions
        res = client.simulate_get(path=f"/operations/exchange.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        assert res.status_code == 404
        assert res.json == {
            'title': "long running operation 'exchange.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao' not found"
        }

        res = client.simulate_get(path=f"/operations/query.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao")
        assert res.status_code == 404
        assert res.json == {'title': 'long running operation '
                                     "'query.EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao' not found"}
