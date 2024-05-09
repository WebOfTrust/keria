# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.notifying module

Testing the Mark II Agent notification endpoint
"""
from builtins import isinstance

from keri.core.signing import Salter

from keria.app import notifying, grouping


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        notifying.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/notifications")
        assert isinstance(end, notifying.NotificationCollectionEnd)
        (end, *_) = app._router.find("/notifications/SAID")
        assert isinstance(end, notifying.NotificationResourceEnd)


def test_notifications(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        notifying.loadEnds(app=app)

        assert agent.notifier.add(attrs=dict(a=1, b=2, c=3)) is True

        assert agent.notifier.add(attrs=dict(a=1)) is True
        assert agent.notifier.add(attrs=dict(a=2)) is True
        assert agent.notifier.add(attrs=dict(a=3)) is True

        res = client.simulate_get(path="/notifications")
        assert res.status_code == 200
        notes = res.json
        assert len(notes) == 4
        assert notes[0]['a'] == dict(a=1, b=2, c=3)
        assert notes[3]['a'] == dict(a=3)

        headers = dict(Range=f"notes=0-2")
        res = client.simulate_get(path="/notifications", headers=headers)
        assert res.status_code == 200
        notes = res.json
        assert len(notes) == 3
        assert notes[0]['a'] == dict(a=1, b=2, c=3)
        assert notes[2]['a'] == dict(a=2)
        assert res.headers["Accept-Ranges"] == "notes"
        assert res.headers["Content-Range"] == "notes 0-2/4"

        # Load since the last one seen
        headers = dict(Range=f"notes=1-2")
        res = client.simulate_get(path=f"/notifications", headers=headers)
        assert res.status_code == 200
        notes = res.json
        assert len(notes) == 2
        assert notes[0]['a'] == dict(a=1)
        assert notes[1]['a'] == dict(a=2)

        # Load with a non-existance last
        last = Salter().qb64
        # Not found for deleting or marking as read a non-existent note
        res = client.simulate_delete(path=f"/notifications/{last}")
        assert res.status_code == 404
        res = client.simulate_put(path=f"/notifications/{last}")
        assert res.status_code == 404

        last = notes[1]['i']
        res = client.simulate_delete(path=f"/notifications/{last}")
        assert res.status_code == 202

        res = client.simulate_get(path="/notifications")
        assert res.status_code == 200
        notes = res.json
        assert len(notes) == 3
        assert notes[1]['a'] == dict(a=1)

        last = notes[1]['i']
        res = client.simulate_put(path=f"/notifications/{last}")
        assert res.status_code == 202

        res = client.simulate_get(path="/notifications")
        assert res.status_code == 200
        notes = res.json
        assert len(notes) == 3
        assert notes[0]['r'] is False
        assert notes[1]['r'] is True
        assert notes[2]['r'] is not True  # just for fun
