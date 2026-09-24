# -*- encoding: utf-8 -*-
"""
KERIA
tests.core.test_authing_canonical module

Canonical-mode (RFC 9421, KERI profile) request and response signing. The
legacy scheme's tests stay in test_authing.py, unchanged.
"""

import base64
import json
import os
from types import SimpleNamespace
from urllib.parse import quote, unquote, urlsplit

import falcon
import pytest
from falcon import testing
from hio.base import doing
from hio.help import Hict
from keri import core, kering
from keri.app import habbing
from keri.core import eventing, parsing, MtrDex
from keri.end import httpsigning

from keria.app import agenting
from keria.core import authing, httping

VECTORS = os.path.join(os.path.dirname(__file__), "..", "vectors", "keri-rfc9421")


def loadVectors(name):
    with open(os.path.join(VECTORS, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def b64(value):
    """Decode base64url or standard base64, padded or not."""
    value = value.replace("-", "+").replace("_", "/")
    return base64.b64decode(value + "=" * (-len(value) % 4))


# Stand-ins for an agent and its key state, so the vectors' synthetic AIDs can
# be served by KERIA's real authenticator without real KELs.


def stubKever(verfer):
    return SimpleNamespace(verfers=[verfer], tholder=core.Tholder(sith="1"))


def rawKever(publicKey):
    return stubKever(core.Verfer(raw=b64(publicKey), code=MtrDex.Ed25519))


class StubHab:
    def __init__(self, pre, seedHex, kevers):
        self.pre = pre
        self.signer = core.Signer(raw=bytes.fromhex(seedHex), transferable=True)
        self.kever = stubKever(self.signer.verfer)
        self.kevers = kevers

    def sign(self, ser, verfers=None, indexed=True):
        return [self.signer.sign(ser)]


class StubAgency:
    """Serves one agent for every keyid in keyids, and none for any other."""

    def __init__(self, agent, keyids):
        self.agent = agent
        self.keyids = set(keyids)

    def get(self, caid):
        return self.agent if caid in self.keyids else None


def vectorAgency(vectors):
    """Agency whose one agent holds the key state of every transferable
    vector key, and signs with the vectors' agent key."""
    keys = {k["keyid"]: k for k in vectors["keys"]}
    kevers = {
        keyid: rawKever(k["public_key"])
        for keyid, k in keys.items()
        if k["kind"] == "transferable"
    }
    agentKey = keys["EIhwv8kMnCY92GevqHtBlMT8cQD96m3XkNav--Ti-4Q6"]
    hab = StubHab(agentKey["keyid"], agentKey["seed_hex"], kevers)
    agent = SimpleNamespace(agentHab=hab)
    return StubAgency(agent, keys), agent


def falconRequest(method, url, headers, body, rawUri=True):
    """A ModifiableRequest as KERIA's hio server would hand it over: PATH_INFO
    re-encoded by hio, CONTENT_LENGTH always set to the body read, and
    RAW_URI carrying the request target as sent."""
    split = urlsplit(url)
    body = b"" if body is None else body.encode("utf-8")
    headers = dict(headers)
    if not any(k.lower() == "content-length" for k in headers):
        headers["Content-Length"] = str(len(body))
    env = testing.create_environ(
        method=method,
        path=unquote(split.path) or "/",
        query_string=split.query,
        headers=headers,
        body=body,
        scheme=split.scheme,
        host=split.hostname,
        port=split.port,
    )
    env["PATH_INFO"] = quote(unquote(split.path) or "/")
    if rawUri:
        env["RAW_URI"] = split.path + (f"?{split.query}" if split.query else "")
    else:
        env.pop("RAW_URI", None)
    return authing.ModifiableRequest(env)


def caseRequest(case, **kwa):
    r = case["request"]
    return falconRequest(r["method"], r["url"], r["headers"], r["body"], **kwa)


def authenticator(agency, now, **kwa):
    return authing.SignedHeaderAuthenticator(agency=agency, clock=lambda: now, **kwa)


# Shared vectors through KERIA's verifier wiring


def test_vector_requests_accepted():
    vectors = loadVectors("requests")
    agency, agent = vectorAgency(vectors)
    count = 0
    for case in vectors["cases"]:
        authn = authenticator(agency, case["now"])
        req = caseRequest(case)
        authn.inbound(req)
        verified = req.context.verified
        assert verified.mode == httpsigning.Canonical, case["id"]
        assert verified.keyid == case["expected"]["keyid"], case["id"]
        assert list(verified.covered) == case["expected"]["covered"], case["id"]
        assert req.context.mode == authing.AuthMode.CANONICAL
        assert req.context.agent is agent
        body = case["request"]["body"]
        # the body is still there for the resource to read
        assert req.bounded_stream.read() == (body or "").encode("utf-8")
        count += 1
    assert count == len(vectors["cases"]) == 18


def test_vector_refusals():
    vectors = loadVectors("refusals")
    agency, _ = vectorAgency(vectors)
    applied = 0
    for case in vectors["cases"]:
        if case["kind"] != "request":
            # response verification and signer-side refusals are the
            # client's; KERIA's own responses are checked below
            continue
        authn = authenticator(agency, case["now"])
        req = caseRequest(case)
        with pytest.raises(httpsigning.HttpSigError) as e:
            authn.inbound(req)
        assert e.value.code == case["error"], case["id"]
        assert isinstance(e.value, kering.AuthNError)
        assert not hasattr(req.context, "agent"), case["id"]
        applied += 1
    assert applied == 32


def test_vector_refusals_through_middleware():
    """Every refusal is a bare, unsigned 401."""
    vectors = loadVectors("refusals")
    agency, _ = vectorAgency(vectors)
    for case in vectors["cases"]:
        if case["kind"] != "request":
            continue
        authn = authenticator(agency, case["now"])
        mw = authing.AuthenticationMiddleware(agency=agency, authn=authn)
        req = caseRequest(case)
        rep = falcon.Response()
        mw.process_request(req, rep)
        assert rep.complete is True, case["id"]
        assert rep.status == falcon.HTTP_401, case["id"]
        mw.process_response(req, rep, None, False)
        assert "signature" not in {k.lower() for k in rep.headers}


def test_vector_responses():
    """KERIA's canonical response to each vector request binds the same
    request values fiki does: with fiki's covered list and parameters it
    reproduces fiki's signature byte for byte, and with its own defaults it
    verifies against the request as sent."""
    vectors = loadVectors("responses")
    agency, agent = vectorAgency(vectors)
    for case in vectors["cases"]:
        authn = authenticator(agency, case["now"])
        req = caseRequest(case)
        authn.inbound(req)

        response = case["response"]
        body = (response["body"] or "").encode("utf-8")
        _, inner = next(iter(_parseInput(response["headers"]["Signature-Input"])))
        params = inner.params
        added = httpsigning.signResponse(
            status=response["status"],
            request=req.context.requestage,
            body=body,
            hab=agent.agentHab,
            covered=case["expected"]["covered"],
            created=params["created"],
            nonce=params["nonce"],
        )
        assert added["Signature"] == response["headers"]["Signature"], case["id"]
        assert added["Signature-Input"] == response["headers"]["Signature-Input"]

        rep = falcon.Response()
        rep.status = response["status"]
        if response["body"] is not None:
            rep.data = body
        authn.outbound(req, rep)
        headers = {k: v for k, v in rep.headers.items()}
        sent = case["request"]
        split = urlsplit(sent["url"])
        verified = httpsigning.verifyResponse(
            status=response["status"],
            headers=headers,
            body=body,
            request=httpsigning.Requestage(
                method=sent["method"],
                authority=split.netloc,
                path=split.path,
                query=split.query,
                headers=sent["headers"],
                body=sent["body"],
            ),
            resolver=httpsigning.keverResolver(
                {agent.agentHab.pre: agent.agentHab.kever}
            ),
            keyid=agent.agentHab.pre,
        )
        assert set(verified.covered) == set(case["expected"]["covered"]), case["id"]


def _parseInput(value):
    import http_sfv

    d = http_sfv.Dictionary()
    d.parse(value.encode("utf-8"))
    return d.items()


def test_vector_legacy():
    """Today's traffic still verifies: legacy requests go through KERIA's
    unchanged legacy path, and legacy responses verify over the pinned bases."""
    vectors = loadVectors("legacy")
    requests = 0
    for case in vectors["cases"]:
        if case["kind"] == "request":
            keyid = case["headers"]["Signify-Resource"]
            hab = SimpleNamespace(
                kevers={keyid: stubKever(core.Verfer(qb64=case["key"]))}
            )
            agency = StubAgency(SimpleNamespace(agentHab=hab), [keyid])
            authn = authing.SignedHeaderAuthenticator(agency=agency)
            req = falconRequest(
                case["method"], f"http://127.0.0.1{case['path']}", case["headers"], None
            )
            authn.inbound(req)
            assert req.context.mode == authing.AuthMode.SIGNED_HEADERS
            requests += 1

            # and is refused once legacy mode is turned off
            authn = authing.SignedHeaderAuthenticator(agency=agency, acceptLegacy=False)
            req = falconRequest(
                case["method"], f"http://127.0.0.1{case['path']}", case["headers"], None
            )
            with pytest.raises(httpsigning.MalformedSignature):
                authn.inbound(req)
        else:
            verified = httpsigning.verifyLegacy(
                method=case["method"],
                path=case["path"],
                headers=case["headers"],
                verfer=core.Verfer(qb64=case["key"]),
            )
            assert verified.mode == httpsigning.Legacy
    assert requests == 2


# RAW_URI


def test_raw_uri_server_environ():
    """KERIA's server passes the request target through as RAW_URI, so @path
    keeps the client's encoding where hio re-encodes PATH_INFO (profile O1)."""
    server = httping.createHttpServer(0, falcon.App())
    plain = httping.http.Server(port=0, app=falcon.App())
    vectors = loadVectors("requests")
    agency, _ = vectorAgency(vectors)
    cases = {c["id"]: c for c in vectors["cases"]}
    for cid in ("path-with-a-colon", "path-with-an-encoded-tilde"):
        case = cases[cid]
        split = urlsplit(case["request"]["url"])
        headers = Hict([("Host", split.netloc), *case["request"]["headers"].items()])
        requestant = SimpleNamespace(
            url=split.path,
            path=unquote(split.path),
            query=split.query,
            method=case["request"]["method"],
            version=(1, 1),
            body=b"",
            length=0,
            headers=headers,
            remoter=SimpleNamespace(ca=("127.0.0.1", 50000)),
        )
        env = server.buildEnviron(requestant)
        assert env["RAW_URI"] == split.path
        req = authing.ModifiableRequest(env)
        assert httping.rawPath(req) == split.path
        authenticator(agency, case["now"]).inbound(req)
        # routing still sees the decoded path
        assert req.path == unquote(split.path)

        # hio's own environ has only the re-encoded path, which fails
        env = plain.buildEnviron(requestant)
        assert "RAW_URI" not in env
        req = authing.ModifiableRequest(env)
        assert httping.rawPath(req) != split.path
        with pytest.raises(httpsigning.SignatureMismatch):
            authenticator(agency, case["now"]).inbound(req)


def test_raw_path():
    def req(**env):
        return SimpleNamespace(env=env, path="/decoded")

    assert httping.rawPath(req()) == "/decoded"
    assert httping.rawPath(req(RAW_URI="/a%3Ab?x=1")) == "/a%3Ab"
    assert httping.rawPath(req(RAW_URI="/a#frag")) == "/a"
    assert httping.rawPath(req(RAW_URI="https://h.example/%7Eb?q")) == "/%7Eb"
    assert httping.rawPath(req(RAW_URI="https://h.example")) == "/"
    assert httping.rawPath(req(RAW_URI="//double/slash")) == "//double/slash"


def test_request_authority():
    def req(host, scheme="http"):
        return falcon.Request(
            testing.create_environ(scheme=scheme, headers={"Host": host})
        )

    assert authing.requestAuthority(req("KERIA.example.com:80")) == "keria.example.com"
    assert (
        authing.requestAuthority(req("keria.example.com:443", "https"))
        == "keria.example.com"
    )
    assert (
        authing.requestAuthority(req("keria.example.com:443"))
        == "keria.example.com:443"
    )
    assert authing.requestAuthority(req("127.0.0.1:3901")) == "127.0.0.1:3901"


# Round trip through the falcon middleware with a real agent


class EchoEnd:
    def on_get(self, req, rep):
        rep.media = dict(query=req.query_string, path=req.path)

    def on_post(self, req, rep):
        rep.media = dict(got=req.get_media(), query=req.query_string)

    def on_get_named(self, req, rep, name):
        rep.media = dict(name=name)


class StreamEnd:
    def on_get(self, req, rep):
        import io

        data = b"\x89PNG not really" * 10
        rep.set_header("Content-Type", "image/png")
        rep.set_header("Content-Length", str(len(data)))
        rep.stream = io.BytesIO(data)


NOW = 1609459200  # the mocked clock, 2021-01-01T00:00:00Z


@pytest.fixture()
def keria(mockHelpingNowUTC):
    """A controller, its agent holding the controller's KEL, and a falcon app
    behind KERIA's AuthenticationMiddleware."""
    salt = b"1111456789abcdef"
    salter = core.Salter(raw=salt)
    with habbing.openHab(name="caid", salt=salt, temp=True) as (_, controller):
        agency = agenting.Agency(name="agency", base="", bran=None, temp=True)
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])
        agent = agency.create(caid=controller.pre, salt=salter.qb64)
        kvy = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        parsing.Parser().parse(ims=bytearray(controller.makeOwnInception()), kvy=kvy)

        def app(**kwa):
            authn = authing.SignedHeaderAuthenticator(
                agency=agency, clock=lambda: NOW, **kwa
            )
            app = falcon.App(request_type=authing.ModifiableRequest)
            app.add_middleware(
                authing.AuthenticationMiddleware(
                    agency=agency, authn=authn, allowed=["/agent"]
                )
            )
            app.add_route("/echo", EchoEnd())
            app.add_route("/echo/{name}", EchoEnd(), suffix="named")
            app.add_route("/img", StreamEnd())
            return testing.TestClient(app)

        yield SimpleNamespace(
            controller=controller, agent=agent, agency=agency, app=app
        )
        agency.shut(agent)


def signed(controller, method, path, query="", body=None, created=NOW, **kwa):
    headers = {"Host": "falconframework.org"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    headers.update(
        httpsigning.signRequest(
            method=method,
            path=path,
            query=query,
            headers=headers,
            body=body,
            hab=controller,
            created=created,
            **kwa,
        )
    )
    return headers


def verifyReply(keria, method, path, query, headers, body, result):
    return httpsigning.verifyResponse(
        status=result.status_code,
        headers=result.headers,
        body=result.content,
        request=httpsigning.Requestage(
            method=method,
            authority="falconframework.org",
            path=path,
            query=query,
            headers=headers,
            body=body,
        ),
        resolver=lambda keyid: keria.agent.agentHab.kever.verfers[0],
        keyid=keria.agent.agentHab.pre,
        now=NOW,
    )


def test_canonical_round_trip(keria):
    client = keria.app()
    ctrl = keria.controller

    body = json.dumps(dict(name="alice")).encode("utf-8")
    headers = signed(ctrl, "POST", "/echo", query="type=rot", body=body)
    result = client.simulate_post(
        "/echo", query_string="type=rot", headers=headers, body=body
    )
    assert result.status_code == 200
    assert result.json == dict(got=dict(name="alice"), query="type=rot")
    verified = verifyReply(keria, "POST", "/echo", "type=rot", headers, body, result)
    assert verified.covered == (
        '"@status"',
        '"content-digest"',
        '"@method";req',
        '"@path";req',
        '"@query";req',
        '"content-digest";req',
    )
    # canonical responses carry no legacy fields
    assert "signify-resource" not in result.headers
    assert result.headers["content-digest"] == httpsigning.contentDigest(result.content)

    # a GET with no body and no query
    headers = signed(ctrl, "GET", "/echo")
    result = client.simulate_get("/echo", headers=headers)
    assert result.status_code == 200
    verifyReply(keria, "GET", "/echo", "", headers, None, result)

    # an error response from a resource is signed too
    headers = signed(ctrl, "GET", "/missing")
    result = client.simulate_get("/missing", headers=headers)
    assert result.status_code == 404
    verifyReply(keria, "GET", "/missing", "", headers, None, result)


def test_canonical_percent_encoded_path(keria):
    """A path the client percent-encodes verifies over the encoding as sent
    and routes on the decoded value, as legacy mode does."""
    client = keria.app()
    headers = signed(keria.controller, "GET", "/echo/a%3Ab")
    result = client.simulate_get(
        "/echo/a:b", headers=headers, extras=dict(RAW_URI="/echo/a%3Ab")
    )
    assert result.status_code == 200
    assert result.json == dict(name="a:b")
    verifyReply(keria, "GET", "/echo/a%3Ab", "", headers, None, result)


def test_canonical_streamed_response(keria):
    """A streamed body is buffered, digested and covered (profile section 5)."""
    client = keria.app()
    headers = signed(keria.controller, "GET", "/img")
    result = client.simulate_get("/img", headers=headers)
    assert result.status_code == 200
    assert result.content == b"\x89PNG not really" * 10
    verified = verifyReply(keria, "GET", "/img", "", headers, None, result)
    assert '"content-digest"' in verified.covered


def test_canonical_refusals(keria):
    client = keria.app()
    ctrl = keria.controller
    body = json.dumps(dict(name="alice")).encode("utf-8")

    def refused(result):
        assert result.status_code == 401
        assert "signature" not in result.headers
        assert result.content == b""

    # body swapped after signing: signature holds, digest does not
    headers = signed(ctrl, "POST", "/echo", body=body)
    refused(client.simulate_post("/echo", headers=headers, body=b'{"name": "mallory"}'))

    # digest header rewritten to match the swapped body: signature fails
    headers = signed(ctrl, "POST", "/echo", body=body)
    swapped = b'{"name": "mallory"}'
    headers["Content-Digest"] = httpsigning.contentDigest(swapped)
    refused(client.simulate_post("/echo", headers=headers, body=swapped))

    # query rewritten
    headers = signed(ctrl, "GET", "/echo", query="type=rot")
    refused(client.simulate_get("/echo", query_string="type=ixn", headers=headers))

    # body sent without content-digest coverage
    headers = signed(ctrl, "GET", "/echo")
    refused(client.simulate_post("/echo", headers=headers, body=body))

    # stale and future signatures (defaults: max_age 300, skew 60)
    headers = signed(ctrl, "GET", "/echo", created=NOW - 361)
    refused(client.simulate_get("/echo", headers=headers))
    headers = signed(ctrl, "GET", "/echo", created=NOW + 61)
    refused(client.simulate_get("/echo", headers=headers))
    headers = signed(ctrl, "GET", "/echo", created=NOW - 360)
    assert client.simulate_get("/echo", headers=headers).status_code == 200

    # expired
    headers = signed(ctrl, "GET", "/echo", expires=NOW - 61)
    refused(client.simulate_get("/echo", headers=headers))

    # a controller this KERIA has no agent for
    with habbing.openHab(name="stranger", salt=b"2222456789abcdef", temp=True) as (
        _,
        stranger,
    ):
        headers = signed(stranger, "GET", "/echo")
        refused(client.simulate_get("/echo", headers=headers))

    # unsigned
    refused(client.simulate_get("/echo"))


def test_canonical_freshness_policy(keria):
    """max_age and skew come from configuration."""
    client = keria.app(policy=httpsigning.Policy(maxAge=10, skew=0))
    headers = signed(keria.controller, "GET", "/echo", created=NOW - 10)
    assert client.simulate_get("/echo", headers=headers).status_code == 200
    headers = signed(keria.controller, "GET", "/echo", created=NOW - 11)
    assert client.simulate_get("/echo", headers=headers).status_code == 401


def test_canonical_required_authority(keria):
    policy = httpsigning.Policy(
        requireAuthority=True, authorities=frozenset({"falconframework.org"})
    )
    client = keria.app(policy=policy)
    headers = signed(keria.controller, "GET", "/echo")
    assert client.simulate_get("/echo", headers=headers).status_code == 200

    # signed for a different service
    headers = signed(keria.controller, "GET", "/echo")
    del headers["Host"]
    headers.update(
        httpsigning.signRequest(
            method="GET",
            path="/echo",
            authority="other.example.com",
            hab=keria.controller,
            created=NOW,
        )
    )
    headers["Host"] = "other.example.com"
    assert client.simulate_get("/echo", headers=headers).status_code == 401

    # not covering @authority at all
    headers = signed(
        keria.controller, "GET", "/echo", covered=["@method", "@path", "@query"]
    )
    assert client.simulate_get("/echo", headers=headers).status_code == 401


def test_legacy_off(keria):
    """acceptLegacy=False refuses legacy requests but not canonical ones."""
    from keri.end import ending

    client = keria.app(acceptLegacy=False)
    ctrl = keria.controller
    headers = Hict(
        [
            ("Signify-Resource", ctrl.pre),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ]
    )
    header, qsig = ending.siginput(
        "signify",
        "GET",
        "/echo",
        headers,
        fields=authing.SignedHeaderAuthenticator.DefaultFields,
        hab=ctrl,
        alg="ed25519",
        keyid=ctrl.pre,
    )
    headers.extend(header)
    signage = ending.Signage(
        markers=dict(signify=qsig),
        indexed=False,
        signer=None,
        ordinal=None,
        digest=None,
        kind=None,
    )
    headers.extend(ending.signature([signage]))
    legacy = dict(headers)

    assert keria.app().simulate_get("/echo", headers=legacy).status_code == 200
    assert client.simulate_get("/echo", headers=legacy).status_code == 401
    headers = signed(ctrl, "GET", "/echo")
    assert client.simulate_get("/echo", headers=headers).status_code == 200


def test_legacy_request_gets_legacy_response(keria):
    from keri.end import ending

    ctrl = keria.controller
    headers = Hict(
        [
            ("Signify-Resource", ctrl.pre),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ]
    )
    header, qsig = ending.siginput(
        "signify",
        "GET",
        "/echo",
        headers,
        fields=authing.SignedHeaderAuthenticator.DefaultFields,
        hab=ctrl,
        alg="ed25519",
        keyid=ctrl.pre,
    )
    headers.extend(header)
    headers.extend(
        ending.signature(
            [
                ending.Signage(
                    markers=dict(signify=qsig),
                    indexed=False,
                    signer=None,
                    ordinal=None,
                    digest=None,
                    kind=None,
                )
            ]
        )
    )
    result = keria.app().simulate_get("/echo", headers=dict(headers))
    assert result.status_code == 200
    assert result.headers["signify-resource"] == keria.agent.agentHab.pre
    assert "content-digest" not in result.headers
    verified = httpsigning.verifyLegacy(
        method="GET",
        path="/echo",
        headers=result.headers,
        verfer=keria.agent.agentHab.kever.verfers[0],
    )
    assert verified.mode == httpsigning.Legacy


def test_body_reread_after_request_logger(keria, caplog):
    """RequestLoggerMiddleware reads the body at DEBUG; the body must still
    reach the digest check and the resource intact."""
    import logging

    authn = authing.SignedHeaderAuthenticator(agency=keria.agency, clock=lambda: NOW)
    app = httping.falconApp(logRequests=True, request_type=authing.ModifiableRequest)
    app.add_middleware(
        authing.AuthenticationMiddleware(agency=keria.agency, authn=authn)
    )
    app.add_route("/echo", EchoEnd())
    client = testing.TestClient(app)

    logger = httping.logger
    level = logger.level
    logger.setLevel(logging.DEBUG)
    try:
        body = json.dumps(dict(name="alice")).encode("utf-8")
        headers = signed(keria.controller, "POST", "/echo", body=body)
        result = client.simulate_post("/echo", headers=headers, body=body)
    finally:
        logger.setLevel(level)
    assert result.status_code == 200
    assert result.json["got"] == dict(name="alice")


def test_server_config_defaults():
    config = agenting.KERIAServerConfig()
    assert config.acceptLegacy is True
    assert config.signatureMaxAge == 300
    assert config.signatureSkew == 60
    assert config.signatureAuthorities == []
