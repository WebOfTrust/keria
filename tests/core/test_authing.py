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
from keri import kering
from keri import core
from keri.app import habbing
from keri.core import parsing, eventing, coring, MtrDex
from keri.end import ending

from keria.app import agenting
from keria.core import authing


def test_authenticater_unwrap(mockHelpingNowUTC):
    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)

    with habbing.openHab(name="caid", salt=salt, temp=True) as (controllerHby, controller):
        agency = agenting.Agency(name="agency", base='', bran=None, temp=True)
        authn = authing.Authenticator(agency=agency)

        # Initialize Hio so it will allow for the addition of an Agent hierarchy
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        agent = agency.create(caid=controller.pre, salt=salter.qb64)
        otherAgent = agency.create(caid="ELbpFmMh3eiK5rDj-_7L6e3Yk_CGxLVbhBopMh65gWXD")

        req = testing.create_req(method="POST", path="/oobis")
        with pytest.raises(kering.AuthNError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Request should not expose endpoint in the clear"

        dt = "2022-09-24T00:05:48.196795+00:00"
        http = """GET http://127.0.0.1:3901/identifiers/aid1?x=y HTTP/1.1
content-type: application/json
signify-resource: ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF

""".encode("utf-8")
        pubkey = pysodium.crypto_sign_pk_to_box_pk(agent.agentHab.kever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(http, pubkey)

        diger = coring.Diger(ser=raw, code=MtrDex.Blake3_256)
        payload = dict(
            src=controller.pre,
            dest=agent.pre,
            d=diger.qb64,
            dt=dt,
        )
        sig = controller.sign(json.dumps(payload, separators=(",", ":")).encode("utf-8"), indexed=False)
        signature = \
        ending.signature([ending.Signage(markers=dict(signify=sig[0]), indexed=False, signer=None, ordinal=None,
                                         digest=None,
                                         kind=None)])['Signature']

        req = testing.create_req(method="POST", path="/", body=raw)
        with pytest.raises(ValueError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Missing SIGNATURE header"

        req.headers["SIGNATURE"] = 'indexed="?0";signify="0BA9SX7Jyn66ZdCPOb0WqDEn1UC49GeSPypjVgeMrt6VLWKjEw9ij7Ndur7Wcrru_5eQNbSiNaiP4NQYWht5srEL'
        with pytest.raises(ValueError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Missing SIGNIFY-TIMESTAMP header"

        req.headers["SIGNIFY-TIMESTAMP"] = dt
        with pytest.raises(ValueError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Missing SIGNIFY-RESOURCE header"

        req.headers["SIGNIFY-RESOURCE"] = controller.pre
        with pytest.raises(ValueError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Missing SIGNIFY-RECEIVER header"

        req.headers["SIGNIFY-RECEIVER"] = agent.pre
        with pytest.raises(kering.AuthNError) as e:  # Should fail if Agent hasn't resolved caid's KEL
            authn.unwrap(req)
        assert str(e.value) == "Unknown or invalid controller"

        agentKev = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)
        assert controller.pre in agent.agentHab.kevers

        # After resolving, ensure fails for different receivers (existing but different and non-existing)
        req.headers["SIGNIFY-RECEIVER"] = otherAgent.pre
        with pytest.raises(kering.AuthNError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Unknown or invalid agent"

        req.headers["SIGNIFY-RECEIVER"] = "unknown-receiver"
        with pytest.raises(kering.AuthNError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Unknown or invalid agent"

        # Back to correct
        req.headers["SIGNIFY-RECEIVER"] = agent.pre
        with pytest.raises(kering.AuthNError) as e:
            authn.unwrap(req)
        assert str(e.value) == "Signature invalid"

        req = testing.create_req(method="POST", path="/", body=raw, headers={
            "SIGNATURE": signature,
            "SIGNIFY-TIMESTAMP": dt,
            "SIGNIFY-RESOURCE": controller.pre,
            "SIGNIFY-RECEIVER": agent.pre,
        })
        with pytest.raises(kering.AuthNError) as e:
            authn.unwrap(req)
        assert str(e.value) == "ESSR payload missing or incorrect encrypted sender"

        # Finally correct ESSR
        dt = "2022-09-24T00:05:48.196795+00:00"
        http = f"""GET http://127.0.0.1:3901/identifiers/aid1?x=y HTTP/1.1
        content-type: application/json
        signify-resource: {controller.pre}

        """.encode("utf-8")
        pubkey = pysodium.crypto_sign_pk_to_box_pk(agent.agentHab.kever.verfers[0].raw)
        raw = pysodium.crypto_box_seal(http, pubkey)

        diger = coring.Diger(ser=raw, code=MtrDex.Blake3_256)
        payload = dict(
            src=controller.pre,
            dest=agent.pre,
            d=diger.qb64,
            dt=dt,
        )
        sig = controller.sign(json.dumps(payload, separators=(",", ":")).encode("utf-8"), indexed=False)
        signature = \
            ending.signature([ending.Signage(markers=dict(signify=sig[0]), indexed=False, signer=None, ordinal=None,
                                             digest=None,
                                             kind=None)])['Signature']
        req = testing.create_req(method="POST", path="/", body=raw, headers={
            "SIGNATURE": signature,
            "SIGNIFY-TIMESTAMP": dt,
            "SIGNIFY-RESOURCE": controller.pre,
            "SIGNIFY-RECEIVER": agent.pre,
        })

        agentFound, environ = authn.unwrap(req)
        assert agentFound == agent
        assert environ["HTTP_CONTENT_TYPE"] == "application/json"
        assert environ["HTTP_SIGNIFY_RESOURCE"] == controller.pre
        assert environ["PATH_INFO"] == "/identifiers/aid1"
        assert environ["QUERY_STRING"] == "x=y"
        assert environ["REQUEST_METHOD"] == "GET"


class MockAgency:
    def __init__(self, agent=None):
        self.agent = agent

    def get(self):
        return self.agent


class MockAuthN:
    def __init__(self, agent, environ, error=None):
        self.agent = agent
        self.environ = environ
        self.error = error

    def unwrap(self, _):
        if self.error is not None:
            raise self.error

        return self.agent, self.environ

    @staticmethod
    def resource(_):
        return ""


def create_req(**kwargs):
    return authing.ModifiableRequest(testing.create_environ(**kwargs))


def test_signature_validation(mockHelpingNowUTC):
    agent = object()
    environ = authing.buildEnviron("""POST http://127.0.0.1:3901/main HTTP/1.1
content-type: application/octet-stream
signify-resource: ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF

""")
    vc = authing.SignatureValidationComponent(agency=MockAgency(agent=agent), authn=MockAuthN(agent=agent, environ=environ),
                                              allowed=["/test", "/reward"])

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
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    vc = authing.SignatureValidationComponent(agency=MockAgency(), authn=MockAuthN(agent=agent, environ=environ, error=kering.AuthNError()))
    req = testing.create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    vc = authing.SignatureValidationComponent(agency=MockAgency(), authn=MockAuthN(agent=agent, environ=environ, error=ValueError()))
    req = testing.create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)
    with habbing.openHab(name="caid", salt=salt, temp=True) as (controllerHby, controller):

        agency = agenting.Agency(name="agency", base='', bran=None, temp=True)
        authn = authing.Authenticator(agency=agency)

        # Initialize Hio so it will allow for the addition of an Agent hierarchy
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        agent = agency.create(caid=controller.pre, salt=salter.qb64)
        agentKev = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)
        assert controller.pre in agent.agentHab.kevers

        req = create_req(method="POST", path="/reward", headers={
            "SIGNIFY-RESOURCE": controller.pre,
            "access-control-allow-origin": "*",
            "access-control-allow-methods": "*",
            "access-control-allow-headers": "*",
            "access-control-max-age": "17200"
        })
        req.context.agent = agent

        rep = falcon.Response()
        rep.set_header("access-control-allow-origin", "*")
        rep.set_header("access-control-allow-methods", "*")
        rep.set_header("access-control-allow-headers", "*")
        rep.set_header("access-control-max-age", 17200)
        rep.status = "400 Bad Request"

        vc = authing.SignatureValidationComponent(agency=agency, authn=authn)
        vc.process_response(req, rep, None, True)

        # Signature will change each time due to crypto_box_seal
        assert rep.headers == {'signature': mock.ANY,
                               'signify-resource': 'EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy',
                               'signify-receiver': 'EJPEPKslRHD_fkug3zmoyjQ90DazQAYWI8JIrV2QXyhg',
                               'signify-timestamp': '2021-01-01T00:00:00.000000+00:00',
                               'content-type': 'application/octet-stream',
                               'access-control-allow-origin': '*',
                               'access-control-allow-methods': '*',
                               'access-control-allow-headers': '*',
                               'access-control-max-age': '17200',
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
        assert agent.agentHab.kever.verfers[0].verify(sig=cig.raw, ser=json.dumps(payload, separators=(",", ":")).encode("utf-8"))

        plaintext = controller.decrypt(ser=rep.data).decode("utf-8")
        assert plaintext == """HTTP/1.1 400 Bad Request\r
signify-resource: EDqDrGuzned0HOKFTLqd7m7O7WGE5zYIOHrlCq4EnWxy\r
\r
"""


def test_build_environ():
    http = """GET http://127.0.0.1:3901/identifiers/aid1?x=y HTTP/1.1
    content-type: application/json
    signify-resource: ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF

    """
    environ = authing.buildEnviron(http)
    assert environ == {'CONTENT_LENGTH': '0',
                       'CONTENT_TYPE': 'application/json',
                       'HTTP_CONTENT_TYPE': 'application/json',
                       'HTTP_SIGNIFY_RESOURCE': 'ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF',
                       'PATH_INFO': '/identifiers/aid1',
                       'QUERY_STRING': 'x=y',
                       'REQUEST_METHOD': 'GET',
                       'SERVER_NAME': '127.0.0.1',
                       'SERVER_PORT': '3901',
                       'SERVER_PROTOCOL': 'HTTP/1.1',
                       'wsgi.errors': mock.ANY,
                       'wsgi.input': mock.ANY,
                       'wsgi.url_scheme': 'http'}

    http = """POST http://127.0.0.1/ HTTP/1.0
    content-type: text/plain 
    signify-resource: ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF

    """
    environ = authing.buildEnviron(http)
    assert environ == {'CONTENT_LENGTH': '0',
                       'CONTENT_TYPE': 'text/plain',
                       'HTTP_CONTENT_TYPE': 'text/plain',
                       'HTTP_SIGNIFY_RESOURCE': 'ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF',
                       'PATH_INFO': '/',
                       'QUERY_STRING': '',
                       'REQUEST_METHOD': 'POST',
                       'SERVER_NAME': '127.0.0.1',
                       'SERVER_PORT': '80',
                       'SERVER_PROTOCOL': 'HTTP/1.0',
                       'wsgi.errors': mock.ANY,
                       'wsgi.input': mock.ANY,
                       'wsgi.url_scheme': 'http'}

    http = """POST https://127.0.0.1/main HTTP/1.1
    content-type: application/json
    signify-resource: ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF

    {}
    """
    environ = authing.buildEnviron(http)
    assert environ == {'CONTENT_LENGTH': '2',
                       'CONTENT_TYPE': 'application/json',
                       'HTTP_CONTENT_TYPE': 'application/json',
                       'HTTP_SIGNIFY_RESOURCE': 'ECjmyrSFFfOb3VJi1JUKTy-Vn766h-VKl3XY8OEFdxBF',
                       'PATH_INFO': '/main',
                       'QUERY_STRING': '',
                       'REQUEST_METHOD': 'POST',
                       'SERVER_NAME': '127.0.0.1',
                       'SERVER_PORT': '433',
                       'SERVER_PROTOCOL': 'HTTP/1.1',
                       'wsgi.errors': mock.ANY,
                       'wsgi.input': mock.ANY,
                       'wsgi.url_scheme': 'https'}
