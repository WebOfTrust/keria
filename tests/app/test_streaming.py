# -*- encoding: utf-8 -*-
"""
Generic agent SSE streaming tests.
"""

import json
from types import SimpleNamespace

import falcon
import pytest
from hio.help import decking
from keri.core import indexing, serdering

from keria.app import streaming


def test_sse_broadcaster_uses_independent_subscriber_queues():
    broadcaster = streaming.SseBroadcaster()
    left = iter(broadcaster.subscribe())
    right = iter(broadcaster.subscribe())

    assert next(left) == b"retry: 5000\n\n"
    assert next(right) == b"retry: 5000\n\n"

    broadcaster.publish(event="topic", data={"value": 1}, event_id="event-1")

    left_frame = next(left).decode("utf-8")
    right_frame = next(right).decode("utf-8")
    assert "id: event-1" in left_frame
    assert "event: topic" in left_frame
    assert json.loads(left_frame.split("data: ", 1)[1].split("\n\n", 1)[0]) == {
        "value": 1
    }
    assert right_frame == left_frame


def test_signed_reply_envelope_is_signed_by_agent(helpers):
    with helpers.openKeria() as (_agency, agent, _app, _client):
        envelope = streaming.signedReplyEnvelope(
            agent, "/test/route", {"subject": "value"}
        )

        rserder = serdering.SerderKERI(sad=envelope["rpy"])
        siger = indexing.Siger(qb64=envelope["sigs"][0])
        assert rserder.ked["r"] == "/test/route"
        assert rserder.ked["a"]["agent"] == agent.agentHab.pre
        assert rserder.ked["a"]["subject"] == "value"
        assert agent.agentHab.kever.verfers[0].verify(sig=siger.raw, ser=rserder.raw)


def test_sse_broadcaster_doer_drains_queued_signed_reply(helpers):
    with helpers.openKeria() as (_agency, agent, _app, _client):
        doer = agent.sseBroadcasterDoer
        left = iter(agent.sseBroadcaster.subscribe())
        right = iter(agent.sseBroadcaster.subscribe())
        assert next(left) == b"retry: 5000\n\n"
        assert next(right) == b"retry: 5000\n\n"

        streaming.enqueueSignedReplyCue(
            agent.signalCues,
            event="topic",
            route="/test/route",
            payload={"subject": "value"},
            event_id="event-1",
        )

        assert next(left) == b""

        doer.recur(0)
        left_frame = next(left).decode("utf-8")
        right_frame = next(right).decode("utf-8")
        assert "id: event-1" in left_frame
        assert "event: topic" in left_frame
        assert right_frame == left_frame

        envelope = json.loads(left_frame.split("data: ", 1)[1].split("\n\n", 1)[0])
        rserder = serdering.SerderKERI(sad=envelope["rpy"])
        siger = indexing.Siger(qb64=envelope["sigs"][0])
        assert rserder.ked["r"] == "/test/route"
        assert rserder.ked["a"]["agent"] == agent.agentHab.pre
        assert rserder.ked["a"]["subject"] == "value"
        assert agent.agentHab.kever.verfers[0].verify(sig=siger.raw, ser=rserder.raw)


def test_agent_wires_sse_broadcaster_doer_without_topic_config(helpers):
    with helpers.openKeria() as (_agency, agent, _app, _client):
        assert isinstance(agent.sseBroadcaster, streaming.SseBroadcaster)
        assert isinstance(agent.sseBroadcasterDoer, streaming.SseBroadcasterDoer)
        assert agent.sseBroadcasterDoer in agent.doers
        assert agent.sseBroadcasterDoer.cues is agent.signalCues
        assert agent.sseBroadcasterDoer.broadcaster is agent.sseBroadcaster


def test_sse_broadcaster_doer_requires_explicit_cues_and_broadcaster():
    with pytest.raises(ValueError, match="cues is required"):
        streaming.SseBroadcasterDoer(
            SimpleNamespace(), broadcaster=streaming.SseBroadcaster()
        )

    with pytest.raises(ValueError, match="broadcaster is required"):
        streaming.SseBroadcasterDoer(SimpleNamespace(), cues=decking.Deck())


def test_signals_stream_endpoint_returns_sse_stream(helpers):
    with helpers.openKeria() as (_agency, agent, _app, _client):
        req = SimpleNamespace(context=SimpleNamespace(agent=agent))
        headers = {}
        rep = SimpleNamespace(
            status=None,
            content_type=None,
            stream=None,
            set_header=lambda name, value: headers.__setitem__(name, value),
        )

        streaming.SignalsStreamEnd().on_get(req, rep)

        assert rep.status == falcon.HTTP_200
        assert rep.content_type == "text/event-stream"
        assert headers["Cache-Control"] == "no-cache"
        assert headers["connection"] == "close"
        assert rep.stream.broadcaster is agent.sseBroadcaster
        assert next(iter(rep.stream)) == b"retry: 5000\n\n"
