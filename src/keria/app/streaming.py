# -*- encoding: utf-8 -*-
"""Generic signed agent event streaming helpers for KERIA.

This module owns the reusable transport contract between one KERIA agent and
its connected edge clients. Topic modules may publish events here, but topic
modules must not own SSE framing, subscriber fan-out, or KERI ``rpy`` envelope
signing.
"""

import json
import time
from collections import deque

import falcon
from hio.base import doing
from keri.core import eventing

from .. import log_name, ogler

logger = ogler.getLogger(log_name)


class SseBroadcaster:
    """In-memory per-agent SSE broadcaster with independent subscriber queues."""

    def __init__(self):
        self.subscribers = {}
        self._index = 0

    def subscribe(self):
        self._index += 1
        sid = str(self._index)
        queue = deque()
        self.subscribers[sid] = queue
        return SseEventIterable(self, sid, queue)

    def unsubscribe(self, sid: str):
        self.subscribers.pop(sid, None)

    def publish(self, event: str, data: dict, event_id: str):
        payload = json.dumps(data).encode("utf-8")
        frame = {
            "id": event_id,
            "event": event,
            "data": payload,
        }
        for queue in list(self.subscribers.values()):
            queue.append(frame)


class SseEventIterable:
    """SSE iterable modeled after KERIpy signaling without shared draining."""

    TimeoutSSE = 300  # seconds

    def __init__(self, broadcaster: SseBroadcaster, sid: str, queue, retry=5000):
        self.broadcaster = broadcaster
        self.sid = sid
        self.queue = queue
        self.retry = retry
        self.start = None
        self.end = None

    def __iter__(self):
        self.start = self.end = time.perf_counter()
        return self

    def __next__(self):
        if self.end - self.start >= self.TimeoutSSE:
            self.broadcaster.unsubscribe(self.sid)
            raise StopIteration

        if self.start == self.end:
            self.end = time.perf_counter()
            return bytes(f"retry: {self.retry}\n\n".encode("utf-8"))

        data = bytearray()
        while self.queue:
            event = self.queue.popleft()
            data.extend(
                bytearray(
                    "id: {}\nretry: {}\nevent: {}\ndata: ".format(
                        event["id"], self.retry, event["event"]
                    ).encode("utf-8")
                )
            )
            data.extend(event["data"])
            data.extend(b"\n\n")

        self.end = time.perf_counter()
        return bytes(data)


class SseBroadcasterDoer(doing.Doer):
    """Drain generic agent signal cues into the Agent-owned broadcaster."""

    def __init__(self, agent, cues=None, broadcaster=None, tock=0.0):
        self.agent = agent
        if cues is None:
            raise ValueError("cues is required")
        if broadcaster is None:
            raise ValueError("broadcaster is required")
        self.cues = cues
        self.broadcaster = broadcaster
        super().__init__(tock=tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        while self.cues:
            cue = self.cues.popleft()
            try:
                self.broadcaster.publish(
                    event=cue["event"],
                    data=signedReplyEnvelope(
                        self.agent,
                        route=cue["route"],
                        payload=cue["payload"],
                    ),
                    event_id=cue["event_id"],
                )
            except Exception:  # pragma: no cover - defensive transient logging
                logger.exception("failed to publish SSE signal cue %s", cue)

        return False


def enqueueSignedReplyCue(cues, event: str, route: str, payload: dict, event_id: str):
    """Queue one agent-signed reply for live SSE publication."""
    cues.append(
        {
            "event": event,
            "route": route,
            "payload": payload,
            "event_id": event_id,
        }
    )


def signedReplyEnvelope(agent, route: str, payload: dict) -> dict:
    """Create a KERI ``rpy`` envelope signed by the KERIA agent AID."""
    data = dict(payload)
    data.setdefault("agent", agent.agentHab.pre)
    rserder = eventing.reply(route=route, data=data)
    sigs = agent.agentHab.sign(ser=rserder.raw)
    return {"rpy": rserder.ked, "sigs": [siger.qb64 for siger in sigs]}


def loadEnds(app):
    """Register generic signed agent event streaming routes."""
    app.add_route("/signals/stream", SignalsStreamEnd())


class SignalsStreamEnd:
    """Signed admin SSE endpoint for agent-to-edge-controller events."""

    def on_get(self, req, rep):
        """Signal stream GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
        ---
        summary: Open authenticated agent signal stream
        description: |
          Opens an authenticated Server-Sent Events stream for live agent signals.
          The stream sends an initial retry frame and later event frames whose
          data is a KERI rpy envelope signed by the connected agent.
        tags:
          - Signals
        responses:
          200:
            description: Server-Sent Events stream for generic agent signals.
            content:
              text/event-stream:
                schema:
                  type: string
                  description: SSE frames with id, retry, event, and JSON data fields.
        """
        agent = req.context.agent
        rep.status = falcon.HTTP_200
        rep.content_type = "text/event-stream"
        rep.set_header("Cache-Control", "no-cache")
        rep.set_header("connection", "close")
        rep.stream = agent.sseBroadcaster.subscribe()
