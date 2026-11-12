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
from keri.core import eventing, parsing
from keri.end import httpsigning

from keria.app import agenting
from keria.core import authing, httping

VECTORS = os.path.join(os.path.dirname(__file__), "..", "vectors", "keri-rfc9421")
PROFILE = "https://github.com/bakobo/fiki/blob/keri-profile-v1.1/docs/keri-profile.md"


def loadVectors(name):
    with open(os.path.join(VECTORS, f"{name}.json"), encoding="utf-8") as f:
        vectors = json.load(f)
    assert vectors["keri_vectors_format"] == 7
    assert vectors["profile"]["version"] == "1.1"
    assert vectors["profile"]["where"] == PROFILE
    return vectors


def b64(value):
    """Decode base64url or standard base64, padded or not."""
    value = value.replace("-", "+").replace("_", "/")
    return base64.b64decode(value + "=" * (-len(value) % 4))


# Stand-ins for an agent and its key state, so the vectors' synthetic AIDs can
# be served by KERIA's real authenticator without real KELs.


def stubKever(verfer):
    return SimpleNamespace(verfers=[verfer], tholder=core.Tholder(sith="1"))


def stateKever(keyState):
    """Key state as a vector's key_state gives it: current keys as qb64
    verfers and the signing threshold in keripy's form (profile R4)."""
    return SimpleNamespace(
        verfers=[core.Verfer(qb64=k) for k in keyState["keys"]],
        tholder=core.Tholder(sith=keyState["threshold"]),
    )


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
    vector key, and signs with the vectors' agent key. A keyid absent from
    the vectors' key table has no agent here."""
    keys = {k["keyid"]: k for k in vectors["keys"]}
    kevers = {
        keyid: stateKever(k["key_state"])
        for keyid, k in keys.items()
        if k["kind"] == "transferable"
    }
    for keyid, k in keys.items():
        if k["effective_key"] is not None:
            # the key state reduces to the vectors' effective key
            kever = kevers.get(keyid)
            if kever is not None:
                verfer = httpsigning.effectiveVerfer(kever.verfers, kever.tholder)
                assert verfer.raw == b64(k["effective_key"]), keyid
    agentKey = keys["EIhwv8kMnCY92GevqHtBlMT8cQD96m3XkNav--Ti-4Q6"]
    hab = StubHab(agentKey["keyid"], agentKey["seed_hex"], kevers)
    agent = SimpleNamespace(agentHab=hab)
    return StubAgency(agent, keys), agent


def falconRequest(method, url, headers, body, rawUri=True):
    """A ModifiableRequest as KERIA's hio server would hand it over: PATH_INFO
    re-encoded by hio, CONTENT_LENGTH always set to the body read, and
    RAW_URI carrying the request target as sent. A URL without a host is
    sent to the case's Host field."""
    split = urlsplit(url)
    if not split.netloc:
        host = next(v for k, v in headers.items() if k.lower() == "host")
        split = urlsplit(f"http://{host}{url}")
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
    # hio's buildEnviron also passes every received field through as HTTP_*,
    # after CONTENT_LENGTH, so falcon's headers show Content-Length as sent
    # rather than create_environ's parsed number.
    env["HTTP_CONTENT_LENGTH"] = next(
        v for k, v in headers.items() if k.lower() == "content-length"
    )
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


def casePolicy(case):
    """The verifier policy a case asks for: the default, or one serving the
    case's authorities and so requiring @authority."""
    authorities = (case.get("policy") or {}).get("authorities")
    if not authorities:
        return None
    return httpsigning.Policy(requireAuthority=True, authorities=frozenset(authorities))


def caseAuthenticator(agency, case):
    return authenticator(agency, case["now"], policy=casePolicy(case))


# Shared vectors through KERIA's verifier wiring


def test_vector_requests_accepted():
    vectors = loadVectors("requests")
    agency, agent = vectorAgency(vectors)
    count = 0
    for case in vectors["cases"]:
        authn = caseAuthenticator(agency, case)
        req = caseRequest(case)
        authn.inbound(req)
        verified = req.context.verified
        assert verified.mode == httpsigning.Canonical, case["id"]
        assert verified.keyid == case["expected"]["keyid"], case["id"]
        assert list(verified.covered) == case["expected"]["covered"], case["id"]
        assert verified.bodyOwed is False, case["id"]
        assert req.context.mode == authing.AuthMode.CANONICAL
        assert req.context.agent is agent
        body = case["request"]["body"]
        # the body is still there for the resource to read
        assert req.bounded_stream.read() == (body or "").encode("utf-8")
        count += 1
    assert count == len(vectors["cases"]) == 21


def test_vector_refusals():
    vectors = loadVectors("refusals")
    agency, _ = vectorAgency(vectors)
    applied = 0
    for case in vectors["cases"]:
        if case["kind"] != "request":
            # response verification and signer-side refusals are the
            # client's; KERIA's own responses are checked below
            assert case["kind"] in ("response", "sign-request"), case["id"]
            continue
        authn = caseAuthenticator(agency, case)
        req = caseRequest(case)
        with pytest.raises(httpsigning.HttpSigError) as e:
            authn.inbound(req)
        assert e.value.code == case["error"], case["id"]
        assert isinstance(e.value, kering.AuthNError)
        assert not hasattr(req.context, "agent"), case["id"]
        applied += 1
    assert applied == 45


def test_vector_refusals_through_middleware():
    """Every refusal is a bare, unsigned 401."""
    vectors = loadVectors("refusals")
    agency, _ = vectorAgency(vectors)
    refused = 0
    for case in vectors["cases"]:
        if case["kind"] != "request":
            continue
        authn = caseAuthenticator(agency, case)
        mw = authing.AuthenticationMiddleware(agency=agency, authn=authn)
        req = caseRequest(case)
        rep = falcon.Response()
        mw.process_request(req, rep)
        assert rep.complete is True, case["id"]
        assert rep.status == falcon.HTTP_401, case["id"]
        mw.process_response(req, rep, None, False)
        assert "signature" not in {k.lower() for k in rep.headers}
        refused += 1
    assert refused == 45


def test_vector_responses():
    """KERIA's canonical response to each vector request binds the same
    request values fiki does: with fiki's covered list and parameters it
    reproduces fiki's signature byte for byte, and with its own defaults it
    verifies against the request as sent."""
    vectors = loadVectors("responses")
    agency, agent = vectorAgency(vectors)
    responses = 0
    for case in vectors["cases"]:
        authn = caseAuthenticator(agency, case)
        req = caseRequest(case)
        authn.inbound(req)

        response = case["response"]
        body = (response["body"] or "").encode("utf-8")
        _, inner = next(iter(_parseInput(response["headers"]["Signature-Input"])))
        params = inner.params
        added = httpsigning.signResponse(
            status=response["status"],
            request=req.context.verified.request,
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
                # the request as sent; a record without its body is refused
                body=sent["body"] if sent["body"] is not None else b"",
            ),
            resolver=httpsigning.keverResolver(
                {agent.agentHab.pre: agent.agentHab.kever}
            ),
            keyid=agent.agentHab.pre,
        )
        assert set(verified.covered) == set(case["expected"]["covered"]), case["id"]
        responses += 1
    assert responses == len(vectors["cases"]) == 4


def _parseInput(value):
    import http_sfv

    d = http_sfv.Dictionary()
    d.parse(value.encode("utf-8"))
    return d.items()


def test_vector_legacy():
    """Today's traffic still verifies: legacy requests go through KERIA's
    unchanged legacy path, and legacy responses verify over the pinned bases.
    The generated cases, which carry key_state, are
    test_vector_legacy_effective_signer's."""
    vectors = loadVectors("legacy")
    requests = 0
    for case in vectors["cases"]:
        if "key_state" in case:
            continue
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
            with pytest.raises(kering.HttpSigMalformedSignatureError):
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


def test_vector_legacy_effective_signer():
    """Legacy requests from controllers with more than one current key go
    through KERIA's legacy path against the key state each case states, and
    verify with its single effective signer (profile version 1.1, section 8):
    accepted, or refused with the case's code."""
    vectors = loadVectors("legacy")
    generated = 0
    for case in vectors["cases"]:
        if "key_state" not in case:
            continue
        keyid = case["headers"]["Signify-Resource"]
        hab = SimpleNamespace(kevers={keyid: stateKever(case["key_state"])})
        agency = StubAgency(SimpleNamespace(agentHab=hab), [keyid])
        authn = authing.SignedHeaderAuthenticator(agency=agency)
        req = falconRequest(
            case["method"], f"http://127.0.0.1{case['path']}", case["headers"], None
        )
        if "error" in case:
            with pytest.raises(httpsigning.HttpSigError) as e:
                authn.inbound(req)
            assert e.value.code == case["error"], case["id"]
            assert not hasattr(req.context, "agent"), case["id"]
        else:
            authn.inbound(req)
            assert req.context.mode == authing.AuthMode.SIGNED_HEADERS, case["id"]
        generated += 1
    assert generated == 4


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
        caseAuthenticator(agency, case).inbound(req)
        # routing still sees the decoded path
        assert req.path == unquote(split.path)

        # hio's own environ has only the re-encoded path, which fails
        env = plain.buildEnviron(requestant)
        assert "RAW_URI" not in env
        req = authing.ModifiableRequest(env)
        assert httping.rawPath(req) != split.path
        with pytest.raises(kering.HttpSigSignatureMismatchError):
            caseAuthenticator(agency, case).inbound(req)


def serveOnce(server, target, headers):
    """Sends one GET for target to server over a real socket, servicing the
    server until the response is complete. Returns (status, headers, body)."""
    import socket
    import time

    assert server.reopen()
    try:
        sock = socket.create_connection(("127.0.0.1", server.servant.ha[1]))
        sock.setblocking(False)
        lines = [f"GET {target} HTTP/1.1", "Connection: close"]
        lines.extend(f"{k}: {v}" for k, v in headers.items())
        sock.sendall(("\r\n".join(lines) + "\r\n\r\n").encode("utf-8"))
        data = b""
        end = time.monotonic() + 10
        while time.monotonic() < end:
            server.service()
            try:
                chunk = sock.recv(65536)
            except BlockingIOError:
                time.sleep(0.005)
                continue
            if not chunk:
                break
            data += chunk
        sock.close()
    finally:
        server.close()
    head, _, body = data.partition(b"\r\n\r\n")
    lines = head.decode("utf-8").split("\r\n")
    status = int(lines[0].split()[1])
    fields = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        fields[name.strip().lower()] = value.strip()
    return status, fields, body


def freePort():
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.mark.parametrize("path", ["/echo/a%7Eb", "/echo/a:b"])
def test_raw_uri_end_to_end(keria, path):
    """Over a real socket, a canonical request whose path hio would re-encode
    (%7E decoded to ~, ':' encoded to %3A) verifies through KERIA's server,
    because RAW_URI carries the path as sent to @path, and is refused by a
    plain hio server, whose PATH_INFO no longer matches the signature."""
    app = falcon.App(request_type=authing.ModifiableRequest)
    authn = authing.SignedHeaderAuthenticator(agency=keria.agency, clock=lambda: NOW)
    app.add_middleware(
        authing.AuthenticationMiddleware(agency=keria.agency, authn=authn)
    )
    app.add_route("/echo/{name}", EchoEnd(), suffix="named")
    headers = signed(keria.controller, "GET", path)

    server = httping.createHttpServer(freePort(), app)
    status, fields, body = serveOnce(server, path, headers)
    assert status == 200
    assert json.loads(body) == dict(name=unquote(path).rsplit("/", 1)[1])
    verified = httpsigning.verifyResponse(
        status=status,
        headers=fields,
        body=body,
        request=httpsigning.Requestage(
            method="GET",
            authority="falconframework.org",
            path=path,
            query="",
            headers=headers,
            body=b"",
        ),
        resolver=lambda keyid: keria.agent.agentHab.kever.verfers[0],
        keyid=keria.agent.agentHab.pre,
        now=NOW,
    )
    assert '"@path";req' in verified.covered

    plain = httping.http.Server(port=freePort(), app=app)
    status, _, _ = serveOnce(plain, path, headers)
    assert status == 401


@pytest.mark.parametrize(
    "target", ["//other.example/echo/victim", "///echo/victim", "//echo/victim"]
)
def test_raw_uri_unrouted_path_refused(keria, target):
    """A target that begins with "//" is signed as @path verbatim, but the
    server parses what follows the slashes as an authority and routes on the
    rest. The signature would then name a path other than the one served, so
    it is refused."""
    app = falcon.App(request_type=authing.ModifiableRequest)
    authn = authing.SignedHeaderAuthenticator(agency=keria.agency, clock=lambda: NOW)
    app.add_middleware(
        authing.AuthenticationMiddleware(agency=keria.agency, authn=authn)
    )
    app.add_route("/echo/{name}", EchoEnd(), suffix="named")
    headers = signed(keria.controller, "GET", target)

    server = httping.createHttpServer(freePort(), app)
    status, _, _ = serveOnce(server, target, headers)
    assert status == 401


def test_helper_server_passes_raw_uri():
    """The test helper's server is built the way KERIA builds its own, so
    tests that go through it see RAW_URI too."""
    from keria.testing.testing_helper import Helpers

    doer = Helpers.server(agency=None, httpPort=freePort())
    assert isinstance(doer.server, httping.rawUriServerType(httping.http.Server))


def test_raw_path():
    def req(**env):
        return SimpleNamespace(env=env, path="/decoded")

    assert httping.rawPath(req()) == "/decoded"
    assert httping.rawPath(req(RAW_URI="/a%3Ab?x=1")) == "/a%3Ab"
    assert httping.rawPath(req(RAW_URI="/a#frag")) == "/a"
    assert httping.rawPath(req(RAW_URI="https://h.example/%7Eb?q")) == "/%7Eb"
    assert httping.rawPath(req(RAW_URI="https://h.example")) == "/"
    assert httping.rawPath(req(RAW_URI="//double/slash")) == "//double/slash"


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


class GeneratorStreamEnd:
    """Streams its body from a generator, as the contact image endpoint does
    (aiding.py, rep.stream = agent.org.getImg(...), which yields 4k chunks)."""

    def on_get(self, req, rep):
        chunks = [b"\x89PNG chunk one ", b"chunk two ", b"chunk three"]
        rep.set_header("Content-Type", "image/png")
        rep.set_header("Content-Length", str(len(b"".join(chunks))))
        rep.stream = (chunk for chunk in chunks)


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
            app.add_route("/imggen", GeneratorStreamEnd())
            return testing.TestClient(app)

        yield SimpleNamespace(
            controller=controller, agent=agent, agency=agency, app=app
        )


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
            body=body if body is not None else b"",  # b"" when none was sent
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


def test_canonical_generator_streamed_response(keria):
    """A body streamed from a generator, which has no read(), is buffered,
    digested, covered and still sent."""
    client = keria.app()
    headers = signed(keria.controller, "GET", "/imggen")
    result = client.simulate_get("/imggen", headers=headers)
    assert result.status_code == 200
    assert result.content == b"\x89PNG chunk one chunk two chunk three"
    assert result.headers["content-digest"] == httpsigning.contentDigest(result.content)
    verified = verifyReply(keria, "GET", "/imggen", "", headers, None, result)
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
    client = keria.app(policy=httpsigning.Policy(maxAge=10, skew=1))
    headers = signed(keria.controller, "GET", "/echo", created=NOW - 11)
    assert client.simulate_get("/echo", headers=headers).status_code == 200
    headers = signed(keria.controller, "GET", "/echo", created=NOW - 12)
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


def test_no_resource_sees_an_unchecked_body(keria):
    """The body check is never owed when a request reaches a resource
    (profile section 5): SignedHeaderAuthenticator.inboundCanonical checks
    the body before it returns, and a body that does not match the covered
    Content-Digest is refused before any resource runs, unsigned."""
    reached = []

    class Recording:
        def on_post(self, req, rep):
            reached.append((req.context.verified.bodyOwed, req.bounded_stream.read()))

    authn = authing.SignedHeaderAuthenticator(agency=keria.agency, clock=lambda: NOW)
    app = falcon.App(request_type=authing.ModifiableRequest)
    app.add_middleware(
        authing.AuthenticationMiddleware(agency=keria.agency, authn=authn)
    )
    app.add_route("/echo", Recording())
    client = testing.TestClient(app)

    body = json.dumps(dict(name="alice")).encode("utf-8")
    headers = signed(keria.controller, "POST", "/echo", body=body)
    swapped = json.dumps(dict(name="mallory")).encode("utf-8")
    result = client.simulate_post("/echo", headers=headers, body=swapped)
    assert result.status_code == 401
    assert "signature" not in result.headers
    assert reached == []

    result = client.simulate_post("/echo", headers=headers, body=body)
    assert result.status_code == 200
    assert reached == [(False, body)]


def test_canonical_authority_from_host_drops_default_port(keria):
    """@authority is taken from Host with :80 or :443 removed whatever the
    scheme, so a proxy's explicit default port does not break a signature."""
    policy = httpsigning.Policy(
        requireAuthority=True, authorities=frozenset({"falconframework.org"})
    )
    client = keria.app(policy=policy)
    for host in ("falconframework.org:443", "FalconFramework.org:80"):
        headers = {"Host": host}
        headers.update(
            httpsigning.signRequest(
                method="GET",
                path="/echo",
                authority="falconframework.org",
                hab=keria.controller,
                created=NOW,
            )
        )
        assert client.simulate_get("/echo", headers=headers).status_code == 200, host


# Configuration


@pytest.mark.parametrize(
    "kwa",
    [
        dict(signatureMaxAge=0),
        dict(signatureMaxAge=-300),
        dict(signatureMaxAge="300"),
        dict(signatureSkew=0),
        dict(signatureSkew=1.5),
        dict(signatureAuthorities="keria.example.com"),
    ],
)
def test_server_config_refuses_a_policy_below_the_profile(kwa):
    """max_age and skew must be positive, and a bad setting stops KERIA at
    startup rather than on the first request (profile section 3)."""
    with pytest.raises(ValueError):
        agenting.KERIAServerConfig(**kwa)


def test_server_config_signature_policy():
    policy = agenting.KERIAServerConfig().signaturePolicy()
    assert policy == httpsigning.DefaultPolicy

    config = agenting.KERIAServerConfig(
        signatureMaxAge=30,
        signatureSkew=5,
        signatureAuthorities=["KERIA.example.com:443", "127.0.0.1:3901"],
    )
    policy = config.signaturePolicy()
    assert policy.maxAge == 30
    assert policy.skew == 5
    assert policy.requireAuthority is True
    assert policy.authorities == frozenset({"keria.example.com", "127.0.0.1:3901"})


# PUT /agent/{caid}: the rotation endpoint verifies its own request


def rotationFixture(**authnKwa):
    """A booted agent whose controller is Signify's, and the rotation Signify
    makes when its passcode changes: keys [new, prior-next] with threshold
    ['1', '0'], signed by the new key and by the prior next key as ondex 0."""
    from keri.app import keeping
    from keri.core import coring
    from keria.app import aiding
    from keria.testing.testing_helper import Helpers

    def signers(bran):
        creator = keeping.SaltyCreator(
            salt=core.Salter(raw=bran).qb64,
            stem="signify:controller",
            tier=coring.Tiers.low,
        )
        current = creator.create(pidx=0, ridx=0, tier=coring.Tiers.low, count=1)[0]
        nxt = creator.create(pidx=0, ridx=1, tier=coring.Tiers.low, count=1)[0]
        return current, nxt

    oldBran, newBran = b"0123456789abcdefghijk", b"abcdefghijk0123456789"
    icp, sigers = Helpers.controller(bran=oldBran)
    old, priorNext = signers(oldBran)
    new, newNext = signers(newBran)

    agency = agenting.Agency(name="agency", base="", bran=None, temp=True)
    doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
    doist.enter(doers=[agency])
    agent = agency.create(caid=icp.pre)
    agent.hby.makeSignifyHab(name=agent.caid, ns="agent", serder=icp, sigers=sigers)
    agent.mgr.sxlt = "sxlt-before"

    rot = eventing.rotate(
        pre=icp.pre,
        keys=[new.verfer.qb64, priorNext.verfer.qb64],
        dig=icp.said,
        isith=["1", "0"],
        nsith="1",
        ndigs=[core.Diger(ser=newNext.verfer.qb64b).qb64],
    )
    sigs = [
        new.sign(ser=rot.raw, index=0).qb64,
        priorNext.sign(ser=rot.raw, index=1, ondex=0).qb64,
    ]
    body = json.dumps(dict(rot=rot.ked, sigs=sigs, sxlt="sxlt-after", keys={})).encode(
        "utf-8"
    )

    authnKwa.setdefault("clock", lambda: NOW)
    authn = authing.SignedHeaderAuthenticator(agency=agency, **authnKwa)
    app = falcon.App(request_type=authing.ModifiableRequest)
    app.add_middleware(
        authing.AuthenticationMiddleware(agency=agency, authn=authn, allowed=["/agent"])
    )
    app.add_route("/agent/{caid}", aiding.AgentResourceEnd(agency=agency, authn=authn))
    return SimpleNamespace(
        agency=agency,
        agent=agent,
        client=testing.TestClient(app),
        caid=icp.pre,
        body=body,
        old=old,
        new=new,
        priorNext=priorNext,
    )


def signedPut(fx, signer, body=None, created=NOW):
    body = fx.body if body is None else body
    path = f"/agent/{fx.caid}"
    headers = {"Host": "falconframework.org", "Content-Type": "application/json"}
    headers.update(
        httpsigning.signRequest(
            method="PUT",
            path=path,
            headers=headers,
            body=body,
            signer=signer,
            keyid=fx.caid,
            created=created,
        )
    )
    return fx.client.simulate_put(path, headers=headers, body=body), headers


def legacyPut(fx, signer):
    """PUT /agent/{caid} signed in legacy mode by signer."""
    from keri.end import ending

    path = f"/agent/{fx.caid}"
    headers = Hict(
        [
            ("Content-Type", "application/json"),
            ("Signify-Resource", fx.caid),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ]
    )
    header, qsig = ending.siginput(
        "signify",
        "PUT",
        path,
        headers,
        fields=authing.SignedHeaderAuthenticator.DefaultFields,
        signers=[signer],
        alg="ed25519",
        keyid=fx.caid,
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
    return fx.client.simulate_put(path, headers=dict(headers), body=fx.body)


def test_canonical_agent_rotation(mockHelpingNowUTC):
    """PUT /agent/{caid} is outside the middleware's protection and verifies
    its request itself, before applying the rotation against the key state
    the rotation would establish, and again after it. In canonical mode that
    key state is Signify's
    passcode-rotated state; its single effective signer is the new key
    (profile R4)."""
    fx = rotationFixture()
    result, headers = signedPut(fx, fx.new)
    assert result.status_code == 204

    kever = fx.agent.agentHab.kevers[fx.caid]
    assert kever.sn == 1
    assert [v.qb64 for v in kever.verfers] == [
        fx.new.verfer.qb64,
        fx.priorNext.verfer.qb64,
    ]
    assert kever.tholder.sith == ["1", "0"]
    assert httpsigning.effectiveVerfer(kever.verfers, kever.tholder).qb64 == (
        fx.new.verfer.qb64
    )
    assert fx.agent.mgr.sxlt is None  # the resource ran to the end

    # the 204 is signed in canonical mode and bound to the request
    verified = httpsigning.verifyResponse(
        status=result.status_code,
        headers=result.headers,
        body=result.content,
        request=httpsigning.Requestage(
            method="PUT",
            authority="falconframework.org",
            path=f"/agent/{fx.caid}",
            query="",
            headers=headers,
            body=fx.body,
        ),
        resolver=httpsigning.keverResolver(
            {fx.agent.agentHab.pre: fx.agent.agentHab.kever}
        ),
        keyid=fx.agent.agentHab.pre,
        now=NOW,
    )
    assert '"content-digest";req' in verified.covered


@pytest.mark.parametrize("who", ["old", "priorNext"])
def test_canonical_agent_rotation_wrong_signer(mockHelpingNowUTC, who):
    """Signed by the rotated-away key, or by the prior next key, which does
    not satisfy ['1', '0'] alone: the rotation endpoint answers 401 and the
    resource stops before it touches the salt."""
    fx = rotationFixture()
    result, _ = signedPut(fx, getattr(fx, who))
    assert result.status_code == 401
    assert result.json["description"] == "invalid signature on request"
    assert fx.agent.mgr.sxlt == "sxlt-before"
    assert fx.agent.agentHab.kevers[fx.caid].sn == 0  # not rotated


def test_legacy_agent_rotation(mockHelpingNowUTC):
    """A legacy PUT signed by the rotation's new key verifies, as before."""
    fx = rotationFixture()
    result = legacyPut(fx, fx.new)
    assert result.status_code == 204
    assert fx.agent.agentHab.kevers[fx.caid].sn == 1
    assert fx.agent.mgr.sxlt is None


@pytest.mark.parametrize(
    "case",
    ["stale", "unsigned", "legacy-off", "legacy-old-key"],
)
def test_agent_rotation_refused_before_rotating(mockHelpingNowUTC, case):
    """A refused PUT /agent/{caid} leaves the controller's KEL unrotated.
    The request is verified against the key state the rotation would
    establish before the rotation is applied, so a refusal for any reason
    (freshness, a missing signature, legacy mode turned off, the wrong key)
    cannot leave the agent half-rotated: KEL rotated, salt not updated."""
    fx = rotationFixture(acceptLegacy=case != "legacy-off")
    if case == "stale":
        result, _ = signedPut(fx, fx.new, created=NOW - 3600)
    elif case == "unsigned":
        result = fx.client.simulate_put(
            f"/agent/{fx.caid}",
            headers={"Content-Type": "application/json"},
            body=fx.body,
        )
    elif case == "legacy-off":
        result = legacyPut(fx, fx.new)
    else:
        result = legacyPut(fx, fx.old)
    # an unsigned 401, which a canonical client reports as an authentication
    # failure rather than as missing-signature
    assert result.status_code == 401
    assert "signature" not in result.headers
    assert result.json["description"] == "invalid signature on request"
    assert fx.agent.agentHab.kevers[fx.caid].sn == 0
    assert fx.agent.mgr.sxlt == "sxlt-before"


def test_agent_rotation_reads_the_clock_once(mockHelpingNowUTC):
    """PUT /agent/{caid} is verified before and after the rotation, both times
    against the same now. A clock that moves past the signature's freshness
    window between the two checks cannot leave the KEL rotated and the rest of
    the update undone."""
    times = iter([NOW, NOW + 3600])
    fx = rotationFixture(clock=lambda: next(times))
    result, _ = signedPut(fx, fx.new)
    assert result.status_code == 204
    assert fx.agent.agentHab.kevers[fx.caid].sn == 1
    assert fx.agent.mgr.sxlt is None


def test_canonical_agent_rotation_body_swapped(mockHelpingNowUTC):
    """The body the endpoint acted on is the body the signature covers."""
    fx = rotationFixture()
    signedBody = json.loads(fx.body)
    signedBody["sxlt"] = "sxlt-signed"
    signedBody = json.dumps(signedBody).encode("utf-8")
    path = f"/agent/{fx.caid}"
    headers = {"Host": "falconframework.org", "Content-Type": "application/json"}
    headers.update(
        httpsigning.signRequest(
            method="PUT",
            path=path,
            headers=headers,
            body=signedBody,
            signer=fx.new,
            keyid=fx.caid,
            created=NOW,
        )
    )
    result = fx.client.simulate_put(path, headers=headers, body=fx.body)
    assert result.status_code == 401
    assert fx.agent.mgr.sxlt == "sxlt-before"
    assert fx.agent.agentHab.kevers[fx.caid].sn == 0


@pytest.mark.parametrize("digest", ["swapped", "absent"])
def test_agent_rotation_body_checked_before_parsing(
    mockHelpingNowUTC, monkeypatch, digest
):
    """PUT /agent/{caid} parses its body to find the rotation, so it checks the
    body against Content-Digest first and never parses content that fails."""
    fx = rotationFixture()
    parsed = []
    getMedia = authing.ModifiableRequest.get_media

    def recordingGetMedia(self, *args, **kwargs):
        parsed.append(self.path)
        return getMedia(self, *args, **kwargs)

    monkeypatch.setattr(authing.ModifiableRequest, "get_media", recordingGetMedia)
    path = f"/agent/{fx.caid}"
    headers = {"Host": "falconframework.org", "Content-Type": "application/json"}
    if digest == "swapped":
        headers.update(
            httpsigning.signRequest(
                method="PUT",
                path=path,
                headers=headers,
                body=b'{"other": "content"}',
                signer=fx.new,
                keyid=fx.caid,
                created=NOW,
            )
        )
    result = fx.client.simulate_put(path, headers=headers, body=fx.body)
    assert result.status_code == 401
    assert parsed == []
    assert fx.agent.agentHab.kevers[fx.caid].sn == 0
    assert fx.agent.mgr.sxlt == "sxlt-before"


def test_cors_exposes_canonical_response_fields(keria):
    """A browser shows a script only the CORS-safelisted response headers and
    those in Access-Control-Expose-Headers. A canonical client verifies a
    response from Signature, Signature-Input and Content-Digest, so all three
    must be exposed, or verification fails in the browser alone."""
    app = httping.falconApp(request_type=authing.ModifiableRequest)
    authn = authing.SignedHeaderAuthenticator(agency=keria.agency, clock=lambda: NOW)
    app.add_middleware(
        authing.AuthenticationMiddleware(agency=keria.agency, authn=authn)
    )
    app.add_route("/echo", EchoEnd())
    client = testing.TestClient(app)

    headers = signed(keria.controller, "GET", "/echo")
    headers["Origin"] = "https://wallet.example"
    result = client.simulate_get("/echo", headers=headers)
    assert result.status_code == 200
    exposed = {
        h.strip().lower()
        for h in result.headers["access-control-expose-headers"].split(",")
    }
    for field in ("signature", "signature-input", "content-digest"):
        assert field in result.headers, field
        assert field in exposed, field


def test_signature_mode_peeked_once_per_request(mockHelpingNowUTC, monkeypatch):
    """KERIA reads the Signature header's mode once per request, even on
    PUT /agent/{caid}, where the middleware, the pre-rotation check and the
    post-rotation check each need it."""
    fx = rotationFixture()
    calls = []
    peek = httpsigning.peekMode

    def counting(headers):
        calls.append(1)
        return peek(headers)

    monkeypatch.setattr(httpsigning, "peekMode", counting)
    result, _ = signedPut(fx, fx.new)
    assert result.status_code == 204
    assert len(calls) == 1


def test_server_config_builds_its_policy_once(monkeypatch):
    """The policy validated at startup is the one the authenticator uses."""
    config = agenting.KERIAServerConfig(signatureMaxAge=30)
    assert config.policy == config.signaturePolicy()
    assert config.policy.maxAge == 30

    captured = {}

    class Capturing(authing.SignedHeaderAuthenticator):
        def __init__(self, **kwa):
            captured.update(kwa)
            super().__init__(**kwa)

    monkeypatch.setattr(agenting, "SignedHeaderAuthenticator", Capturing)
    monkeypatch.setattr(
        agenting.KERIAServerConfig,
        "signaturePolicy",
        lambda self: pytest.fail("policy rebuilt after startup"),
    )
    monkeypatch.setattr(agenting, "createHttpServer", lambda *a, **k: None)
    with pytest.raises(AttributeError, match="reopen"):  # the stubbed server
        agenting.createAdminServerDoer(config, SimpleNamespace(tocks={}))
    assert captured["policy"] is config.policy
