# -*- encoding: utf-8 -*-
"""
SIGNIFY
keria.core.authing module

Testing httping utils
"""

import pysodium
from unittest import mock
import json
import falcon
import pytest
from falcon import testing
from hio.base import doing
from hio.help import Hict
from keri import kering
from keri import core
from keri.app import habbing
from keri.core import parsing, eventing, coring, MtrDex
from keri.end import ending

from keria.app import agenting
from keria.core import authing


def create_req(**kwargs):
    return authing.ModifiableRequest(testing.create_environ(**kwargs))


def essr_request(requestLine, headers=(), body=b""):
    head = "\r\n".join([requestLine, *(f"{name}: {value}" for name, value in headers)])
    return head.encode("utf-8") + b"\r\n\r\n" + body


def test_signed_header_authenticator(mockHelpingNowUTC):
    salt = b"1111456789abcdef"
    salter = core.Salter(raw=salt)

    with habbing.openHab(name="caid", salt=salt, temp=True) as (
        controllerHby,
        controller,
    ):
        agency = agenting.Agency(name="agency", base="", bran=None, temp=True)
        authn = authing.SignedHeaderAuthenticator(agency=agency)

        # Initialize Hio so it will allow for the addition of an Agent hierarchy
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        agent = agency.create(caid=controller.pre, salt=salter.qb64)

        # Create authenticater with Agent and controllers AID
        headers = Hict(
            [
                ("Content-Type", "application/json"),
                ("Content-Length", "256"),
                ("Connection", "close"),
                ("Signify-Resource", controller.pre),
                ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
            ]
        )

        header, qsig = ending.siginput(
            "signify",
            "POST",
            "/boot",
            headers,
            fields=authn.DefaultFields,
            hab=controller,
            alg="ed25519",
            keyid=controller.pre,
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

        assert dict(headers) == {
            "Connection": "close",
            "Content-Length": "256",
            "Content-Type": "application/json",
            "Signature": 'indexed="?0";signify="0BDBVr5ape8f9nV60ThhWOKvu5HKXQc5798Sz95FIoqXQ9vvL8HoYsLRp5aN86MIXr0GqH37SowsmTP-k9UhYSkN"',
            "Signature-Input": 'signify=("signify-resource" "@method" "@path" "signify-timestamp");'
            "created=1609459200;"
            'keyid="EPwUOBk9QkxPM20JBaf_pFXPytSjTUoyxbx95uZJE1Hq";'
            'alg="ed25519"',
            "Signify-Resource": "EPwUOBk9QkxPM20JBaf_pFXPytSjTUoyxbx95uZJE1Hq",
            "Signify-Timestamp": "2022-09-24T00:05:48.196795+00:00",
        }

        req = create_req(method="POST", path="/boot", headers=dict(headers))

        with pytest.raises(
            kering.AuthNError
        ) as e:  # Should fail if Agent hasn't resolved caid's KEL
            authn.inbound(req)
        assert (
            str(e.value)
            == "Unknown or invalid controller (controller KEL not resolved)"
        )

        agentKev = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)

        assert controller.pre in agent.agentHab.kevers

        # Malform Signature-Input
        headers["Signature-Input"] = (
            'notsignify=("signify-resource" "@method" "@path" '
            '"signify-timestamp");created=1609459200;keyid'
            '="EPwUOBk9QkxPM20JBaf_pFXPytSjTUoyxbx95uZJE1Hq";alg="ed25519"'
        )

        headers["Signature"] = (
            'indexed="?0";signify'
            '="0BDBVr5ape8f9nV60ThhWOKvu5HKXQc5798Sz95FIoqXQ9vvL8HoYsLRp5aN86MIXr0GqH37SowsmTP-k9UhYSkM"'
        )
        req = create_req(method="POST", path="/boot", headers=dict(headers))

        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == "Missing signify inputs in signature"

        # Correct Signature-Input
        headers["Signature-Input"] = (
            'signify=("signify-resource" "@method" "@path" '
            '"signify-timestamp");created=1609459200;keyid'
            '="EPwUOBk9QkxPM20JBaf_pFXPytSjTUoyxbx95uZJE1Hq";alg="ed25519"'
        )

        # Bad signature
        headers["Signature"] = (
            'indexed="?0";signify'
            '="0BDBVr5ape8f9nV60ThhWOKvu5HKXQc5798Sz95FIoqXQ9vvL8HoYsLRp5aN86MIXr0GqH37SowsmTP-k9UhYSkM"'
        )
        req = create_req(method="POST", path="/boot", headers=dict(headers))

        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == (
            "Signature for Inputage(name='signify', fields=['signify-resource', '@method', "
            "'@path', 'signify-timestamp'], created=1609459200, "
            "keyid='EPwUOBk9QkxPM20JBaf_pFXPytSjTUoyxbx95uZJE1Hq', alg='ed25519', expires=None, "
            "nonce=None, context=None) invalid"
        )
        # Good signature
        headers["Signature"] = (
            'indexed="?0";signify'
            '="0BDBVr5ape8f9nV60ThhWOKvu5HKXQc5798Sz95FIoqXQ9vvL8HoYsLRp5aN86MIXr0GqH37SowsmTP-k9UhYSkN"'
        )
        req = create_req(method="POST", path="/boot", headers=dict(headers))

        authn.inbound(req)  # Does not raise error

        rep = falcon.Response()
        rep.set_headers(
            [
                ("Content-Type", "application/json"),
                ("Content-Length", "256"),
                ("Connection", "close"),
                ("Signify-Resource", agent.agentHab.pre),
                ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
            ]
        )

        authn.outbound(req, rep)

        assert dict(rep.headers) == {
            "connection": "close",
            "content-length": "256",
            "content-type": "application/json",
            "signature": 'indexed="?0";signify="0BBWiqPdnUjfwkDcFQQyUUjjATXp0mRgG7S9ikr_XZkp0Nbv77dY8syrdpJTLuU4gTfmMYJb4OIR5oN7K02CV_0I"',
            "signature-input": 'signify=("signify-resource" "@method" "@path" '
            '"signify-timestamp");created=1609459200;keyid="EEAJjjsbswsipSk6qypNw9bKszVfkAWvAYonKTKWHnDt";alg="ed25519"',
            "signify-resource": "EEAJjjsbswsipSk6qypNw9bKszVfkAWvAYonKTKWHnDt",
            "signify-timestamp": "2021-01-01T00:00:00.000000+00:00",
        }

        req = create_req(method="POST", path="/boot", headers=dict(rep.headers))
        with pytest.raises(
            kering.AuthNError
        ) as e:  # Should because the agent won't be found
            authn.inbound(req)
        assert str(e.value) == "Unknown controller"


def test_essr_authenticator(mockHelpingNowUTC):
    salt = b"0123456789abcdef"
    salter = core.Salter(raw=salt)

    with habbing.openHab(name="caid", salt=salt, temp=True) as (
        controllerHby,
        controller,
    ):
        agency = agenting.Agency(name="agency", base="", bran=None, temp=True)
        authn = authing.ESSRAuthenticator(agency=agency)

        # Initialize Hio so it will allow for the addition of an Agent hierarchy
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        agent = agency.create(caid=controller.pre, salt=salter.qb64)
        otherAgent = agency.create(caid="ELbpFmMh3eiK5rDj-_7L6e3Yk_CGxLVbhBopMh65gWXD")

        req = create_req(method="POST", path="/oobis")
        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == "Request should not expose endpoint in the clear"

        dt = "2022-09-24T00:05:48.196795+00:00"
        http = essr_request(
            "GET http://127.0.0.1:3901/identifiers/aid1?x=y HTTP/1.1",
            [
                ("content-type", "application/json"),
                (
                    "signify-resource",
                    "ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF",
                ),
            ],
        )
        pubkey = pysodium.crypto_sign_pk_to_box_pk(agent.agentHab.kever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(http, pubkey)

        diger = coring.Diger(ser=raw, code=MtrDex.Blake3_256)
        payload = dict(
            src=controller.pre,
            dest=agent.pre,
            d=diger.qb64,
            dt=dt,
        )
        sig = controller.sign(
            json.dumps(payload, separators=(",", ":")).encode("utf-8"), indexed=False
        )
        signature = ending.signature(
            [
                ending.Signage(
                    markers=dict(signify=sig[0]),
                    indexed=False,
                    signer=None,
                    ordinal=None,
                    digest=None,
                    kind=None,
                )
            ]
        )["Signature"]

        req = create_req(method="POST", path="/", body=raw)
        with pytest.raises(ValueError) as e:
            authn.inbound(req)
        assert str(e.value) == "Missing SIGNATURE header"

        req.headers["SIGNATURE"] = (
            'indexed="?0";signify="0BA9SX7Jyn66ZdCPOb0WqDEn1UC49GeSPypjVgeMrt6VLWKjEw9ij7Ndur7Wcrru_5eQNbSiNaiP4NQYWht5srEL'
        )
        with pytest.raises(ValueError) as e:
            authn.inbound(req)
        assert str(e.value) == "Missing SIGNIFY-TIMESTAMP header"

        req.headers["SIGNIFY-TIMESTAMP"] = dt
        with pytest.raises(ValueError) as e:
            authn.inbound(req)
        assert str(e.value) == "Missing SIGNIFY-RESOURCE header"

        req.headers["SIGNIFY-RESOURCE"] = controller.pre
        with pytest.raises(ValueError) as e:
            authn.inbound(req)
        assert str(e.value) == "Missing SIGNIFY-RECEIVER header"

        req.headers["SIGNIFY-RECEIVER"] = agent.pre
        with pytest.raises(
            kering.AuthNError
        ) as e:  # Should fail if Agent hasn't resolved caid's KEL
            authn.inbound(req)
        assert str(e.value) == "Unknown or invalid controller"

        agentKev = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)
        assert controller.pre in agent.agentHab.kevers

        # After resolving, ensure fails for different receivers (existing but different and non-existing)
        req.headers["SIGNIFY-RECEIVER"] = otherAgent.pre
        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == "Unknown or invalid agent"

        req.headers["SIGNIFY-RECEIVER"] = "unknown-receiver"
        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == "Unknown or invalid agent"

        # Back to correct
        req.headers["SIGNIFY-RECEIVER"] = agent.pre
        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == "Signature invalid"

        req = create_req(
            method="POST",
            path="/",
            body=raw,
            headers={
                "SIGNATURE": signature,
                "SIGNIFY-TIMESTAMP": dt,
                "SIGNIFY-RESOURCE": controller.pre,
                "SIGNIFY-RECEIVER": agent.pre,
            },
        )
        with pytest.raises(kering.AuthNError) as e:
            authn.inbound(req)
        assert str(e.value) == "ESSR payload missing or incorrect encrypted sender"

        # Finally correct ESSR
        dt = "2022-09-24T00:05:48.196795+00:00"
        http = essr_request(
            "GET http://127.0.0.1:3901/identifiers/aid1?x=y HTTP/1.1",
            [
                ("Content-Type", "application/json"),  # liberal on header name case
                ("signify-resource", controller.pre),
            ],
        )
        pubkey = pysodium.crypto_sign_pk_to_box_pk(agent.agentHab.kever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(http, pubkey)

        diger = coring.Diger(ser=raw, code=MtrDex.Blake3_256)
        payload = dict(
            src=controller.pre,
            dest=agent.pre,
            d=diger.qb64,
            dt=dt,
        )
        sig = controller.sign(
            json.dumps(payload, separators=(",", ":")).encode("utf-8"), indexed=False
        )
        signature = ending.signature(
            [
                ending.Signage(
                    markers=dict(signify=sig[0]),
                    indexed=False,
                    signer=None,
                    ordinal=None,
                    digest=None,
                    kind=None,
                )
            ]
        )["Signature"]
        req = create_req(
            method="POST",
            path="/",
            body=raw,
            headers={
                "SIGNATURE": signature,
                "SIGNIFY-TIMESTAMP": dt,
                "SIGNIFY-RESOURCE": controller.pre,
                "SIGNIFY-RECEIVER": agent.pre,
            },
        )

        authn.inbound(req)
        assert req.context.agent == agent
        assert req.context.mode == authing.AuthMode.ESSR
        assert req.get_header("Content-Type") == "application/json"
        assert req.get_header("Signify-Resource") == controller.pre
        assert req.path == "/identifiers/aid1"
        assert req.get_param("x") == "y"
        assert req.method == "GET"

        # Now test outbound
        req = create_req(
            method="POST",
            path="/reward",
            headers={
                "SIGNIFY-RESOURCE": controller.pre,
                "access-control-allow-origin": "*",
                "access-control-allow-methods": "*",
                "access-control-allow-headers": "*",
                "access-control-max-age": "17200",
            },
        )
        req.context.agent = agent
        req.context.mode = authing.AuthMode.ESSR

        rep = falcon.Response()
        rep.set_header("access-control-allow-origin", "*")
        rep.set_header("access-control-allow-methods", "*")
        rep.set_header("access-control-allow-headers", "*")
        rep.set_header("access-control-max-age", 17200)
        rep.status = "400 Bad Request"

        authn.outbound(req, rep)

        # Signature will change each time due to crypto_box_seal
        assert rep.headers == {
            "signature": mock.ANY,
            "signify-resource": "EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy",
            "signify-receiver": "EJPEPKslRHD_fkug3zmoyjQ90DazQAYWI8JIrV2QXyhg",
            "signify-timestamp": "2021-01-01T00:00:00.000000+00:00",
            "content-type": "application/octet-stream",
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "*",
            "access-control-allow-headers": "*",
            "access-control-max-age": "17200",
        }
        assert rep.status == 200

        signages = ending.designature(rep.headers.get("signature"))
        cig = signages[0].markers["signify"]
        payload = dict(
            src="EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy",
            dest="EJPEPKslRHD_fkug3zmoyjQ90DazQAYWI8JIrV2QXyhg",
            d=coring.Diger(ser=rep.data, code=MtrDex.Blake3_256).qb64,
            dt="2021-01-01T00:00:00.000000+00:00",
        )
        assert agent.agentHab.kever.verfers[0].verify(
            sig=cig.raw, ser=json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )

        plaintext = controller.decrypt(ser=rep.data).decode("utf-8")
        assert (
            plaintext
            == """HTTP/1.1 400 Bad Request\r
signify-resource: EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy\r
\r
"""
        )

        def sealed(http):
            raw = pysodium.crypto_box_seal(http, pubkey)
            payload = dict(
                src=controller.pre,
                dest=agent.pre,
                d=coring.Diger(ser=raw, code=MtrDex.Blake3_256).qb64,
                dt=dt,
            )
            sig = controller.sign(
                json.dumps(payload, separators=(",", ":")).encode("utf-8"),
                indexed=False,
            )
            return create_req(
                method="POST",
                path="/",
                body=raw,
                headers={
                    "SIGNATURE": ending.signature(
                        [
                            ending.Signage(
                                markers=dict(signify=sig[0]),
                                indexed=False,
                                signer=None,
                                ordinal=None,
                                digest=None,
                                kind=None,
                            )
                        ]
                    )["Signature"],
                    "SIGNIFY-TIMESTAMP": dt,
                    "SIGNIFY-RESOURCE": controller.pre,
                    "SIGNIFY-RECEIVER": agent.pre,
                },
            )

        # Nothing in the tunnel is normalized, stripped or re-encoded in either direction
        body = json.dumps({"alias": "a\u2028b\u2029c\u0085d\r\ne "}).encode("utf-8")
        req = sealed(
            essr_request(
                "POST http://127.0.0.1:3901/contacts HTTP/1.1",
                [
                    ("content-type", "application/json"),
                    ("signify-resource", controller.pre),
                ],
                body,
            )
        )

        authn.inbound(req)
        assert req.path == "/contacts"
        assert req.content_length == len(body)
        assert req.bounded_stream.read() == body

        rep = falcon.Response()
        rep.status = "200 OK"
        rep.data = body
        authn.outbound(req, rep)
        assert controller.decrypt(ser=rep.data) == (
            b"HTTP/1.1 200 OK\r\nsignify-resource: "
            + agent.agentHab.pre.encode("utf-8")
            + b"\r\n\r\n"
            + body
        )

        middleware = authing.AuthenticationMiddleware(
            agency=agency, authn=None, essrAuthn=authn
        )
        for malformed in (
            b"GET http://127.0.0.1:3901/contacts\r\n\r\n",
            b"GET http://127.0.0.1:3901/contacts HTTP/1.1\r\nnot-a-header\r\n\r\n",
            b"\xff\xfe\r\n\r\n",
        ):
            rep = falcon.Response()
            middleware.process_request(sealed(malformed), rep)
            assert rep.complete is True
            assert rep.status == falcon.HTTP_401


RESOURCE = "ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF"


def test_build_environ():
    http = essr_request(
        "GET http://127.0.0.1:3901/identifiers/aid1?x=y HTTP/1.1",
        [("content-type", "application/json"), ("signify-resource", RESOURCE)],
    )
    environ = authing.ESSRAuthenticator.buildEnviron(http)
    assert environ == {
        "CONTENT_LENGTH": "0",
        "CONTENT_TYPE": "application/json",
        "HTTP_CONTENT_TYPE": "application/json",
        "HTTP_SIGNIFY_RESOURCE": RESOURCE,
        "PATH_INFO": "/identifiers/aid1",
        "QUERY_STRING": "x=y",
        "REQUEST_METHOD": "GET",
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "3901",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.errors": mock.ANY,
        "wsgi.input": mock.ANY,
        "wsgi.url_scheme": "http",
    }
    assert environ["wsgi.input"].read() == b""

    http = essr_request(
        "POST http://127.0.0.1/ HTTP/1.0",
        [("content-type", "text/plain"), ("signify-resource", RESOURCE)],
    )
    environ = authing.ESSRAuthenticator.buildEnviron(http)
    assert environ == {
        "CONTENT_LENGTH": "0",
        "CONTENT_TYPE": "text/plain",
        "HTTP_CONTENT_TYPE": "text/plain",
        "HTTP_SIGNIFY_RESOURCE": RESOURCE,
        "PATH_INFO": "/",
        "QUERY_STRING": "",
        "REQUEST_METHOD": "POST",
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.0",
        "wsgi.errors": mock.ANY,
        "wsgi.input": mock.ANY,
        "wsgi.url_scheme": "http",
    }

    http = essr_request(
        "POST https://127.0.0.1/main HTTP/1.1",
        [("content-type", "application/json"), ("signify-resource", RESOURCE)],
        b"{}",
    )
    environ = authing.ESSRAuthenticator.buildEnviron(http)
    assert environ == {
        "CONTENT_LENGTH": "2",
        "CONTENT_TYPE": "application/json",
        "HTTP_CONTENT_TYPE": "application/json",
        "HTTP_SIGNIFY_RESOURCE": RESOURCE,
        "PATH_INFO": "/main",
        "QUERY_STRING": "",
        "REQUEST_METHOD": "POST",
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "433",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.errors": mock.ANY,
        "wsgi.input": mock.ANY,
        "wsgi.url_scheme": "https",
    }
    assert environ["wsgi.input"].read() == b"{}"

    http = essr_request(
        "POST https://127.0.0.1/main HTTP/1.1",
        [("content-type", "application/json"), ("signify-resource", RESOURCE)],
        "ññ".encode("utf-8"),
    )
    environ = authing.ESSRAuthenticator.buildEnviron(http)
    assert environ["CONTENT_LENGTH"] == "4"  # ñ takes 2
    assert environ["wsgi.input"].read() == "ññ".encode("utf-8")


def test_build_environ_body_is_verbatim():
    def body_of(body):
        environ = authing.ESSRAuthenticator.buildEnviron(
            essr_request(
                "POST http://127.0.0.1/main HTTP/1.1",
                [("content-type", "application/json")],
                body,
            )
        )
        assert environ["CONTENT_LENGTH"] == str(len(body))
        return environ["wsgi.input"].read()

    # the hazard class that made the client escape these before sealing
    hazards = json.dumps({"alias": "a\u2028b\u2029c\u0085d"}).encode("utf-8")
    assert body_of(hazards) == hazards

    assert body_of(b'{"a": "x\r\ny"}') == b'{"a": "x\r\ny"}'
    assert body_of(b"one\r\n\r\ntwo") == b"one\r\n\r\ntwo"
    assert body_of(b"  padded  \n") == b"  padded  \n"
    assert body_of(b"\xff\xfe\x00binary") == b"\xff\xfe\x00binary"


def test_build_environ_header_names_are_case_insensitive():
    http = essr_request(
        "POST http://127.0.0.1/main HTTP/1.1",
        [
            ("Content-Type", "application/json"),
            ("Signify-Resource", RESOURCE),
            ("Location", "http://example.com: 8080"),
        ],
    )
    environ = authing.ESSRAuthenticator.buildEnviron(http)
    assert environ["CONTENT_TYPE"] == "application/json"
    assert environ["HTTP_CONTENT_TYPE"] == "application/json"
    assert environ["HTTP_SIGNIFY_RESOURCE"] == RESOURCE
    assert environ["HTTP_LOCATION"] == "http://example.com: 8080"


def test_build_environ_malformed():
    with pytest.raises(ValueError):  # head not terminated by CRLFCRLF
        authing.ESSRAuthenticator.buildEnviron(
            b"GET http://127.0.0.1/main HTTP/1.1\r\n"
        )

    with pytest.raises(ValueError):
        authing.ESSRAuthenticator.buildEnviron(b"GET http://127.0.0.1/main\r\n\r\n")

    with pytest.raises(ValueError):
        authing.ESSRAuthenticator.buildEnviron(
            b"GET http://127.0.0.1/main HTTP/1.1\r\nnot-a-header\r\n\r\n"
        )

    with pytest.raises(UnicodeDecodeError):
        authing.ESSRAuthenticator.buildEnviron(b"\xff\xfe\r\n\r\n")


def test_serialize_response():
    rep = falcon.Response()
    rep.set_headers(
        [
            ("signify-resource", "EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy"),
            ("access-control-allow-origin", "*"),  # CORS should be ignored
            ("access-control-allow-methods", "*"),
            ("access-control-allow-headers", "*"),
            ("access-control-expose-headers", "*"),
            ("access-control-max-age", "1728000"),
        ]
    )
    rep.status = "400 Bad Request"

    serialized = authing.ESSRAuthenticator.serializeResponse("HTTP/1.1", rep)
    assert serialized == (
        b"HTTP/1.1 400 Bad Request\r\n"
        b"signify-resource: EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy\r\n"
        b"\r\n"
    )

    rep.data = json.dumps({"a": "b"}).encode("utf-8")
    serialized = authing.ESSRAuthenticator.serializeResponse("HTTP/1.1", rep)
    assert serialized == (
        b"HTTP/1.1 400 Bad Request\r\n"
        b"signify-resource: EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy\r\n"
        b"\r\n"
        b'{"a": "b"}'
    )

    rep.data = None
    rep.text = "Identifier not found!"
    serialized = authing.ESSRAuthenticator.serializeResponse("HTTP/1.1", rep)
    assert serialized == (
        b"HTTP/1.1 400 Bad Request\r\n"
        b"signify-resource: EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy\r\n"
        b"\r\n"
        b"Identifier not found!"
    )


def test_serialize_response_without_headers():
    rep = falcon.Response()
    rep.status = "204 No Content"
    assert (
        authing.ESSRAuthenticator.serializeResponse("HTTP/1.1", rep)
        == b"HTTP/1.1 204 No Content\r\n\r\n"
    )

    rep.data = b"\xff\xfe\x00binary"
    assert authing.ESSRAuthenticator.serializeResponse("HTTP/1.1", rep) == (
        b"HTTP/1.1 204 No Content\r\n\r\n\xff\xfe\x00binary"
    )


class MockAgency:
    def __init__(self, agent=None):
        self.agent = agent

    def get(self, caid=None):
        return self.agent


def test_authentication_middleware(mockHelpingNowUTC):
    mockAuthN = mock.Mock(name="MockAuthN")
    mockESSRAuthN = mock.Mock(name="MockESSRAuthN")

    agent = object()
    vc = authing.AuthenticationMiddleware(
        agency=MockAgency(agent=agent),
        authn=mockAuthN,
        essrAuthn=mockESSRAuthN,
        allowed=["/test", "/reward"],
    )

    req = create_req(method="POST", path="/test")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = create_req(method="POST", path="/reward")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = create_req(method="GET", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert mockAuthN.inbound.call_count == 2  # not 4
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    mockAuthN.reset_mock()
    mockAuthN.inbound.side_effect = kering.AuthNError()

    req = create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    mockAuthN.inbound.assert_called_once()
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    mockAuthN.reset_mock()
    mockAuthN.inbound.side_effect = ValueError()

    req = create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    mockAuthN.inbound.assert_called_once()
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    req = create_req(method="POST", path="/")
    rep = falcon.Response()

    vc.process_request(req, rep)
    mockESSRAuthN.inbound.assert_called_once()
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    mockESSRAuthN.reset_mock()
    mockESSRAuthN.inbound.side_effect = kering.AuthNError()

    req = create_req(method="POST", path="/")
    rep = falcon.Response()

    vc.process_request(req, rep)
    mockESSRAuthN.inbound.assert_called_once()
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    mockESSRAuthN.reset_mock()
    mockESSRAuthN.inbound.side_effect = ValueError()

    req = create_req(method="POST", path="/")
    rep = falcon.Response()

    vc.process_request(req, rep)
    mockESSRAuthN.inbound.assert_called_once()
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    mockESSRAuthN.reset_mock()
    mockESSRAuthN.inbound.side_effect = UnicodeDecodeError(
        "utf-8", b"\xff", 0, 1, "invalid start byte"
    )

    req = create_req(method="POST", path="/")
    rep = falcon.Response()

    vc.process_request(req, rep)
    mockESSRAuthN.inbound.assert_called_once()
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    # Now test outbound
    req = create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    req.context.agent = agent
    req.context.mode = authing.AuthMode.SIGNED_HEADERS

    vc.process_response(req, rep, None, True)
    mockAuthN.outbound.assert_called_once()

    req.context.mode = authing.AuthMode.ESSR
    vc.process_response(req, rep, None, True)
    mockESSRAuthN.outbound.assert_called_once()
