# -*- encoding: utf-8 -*-
"""
SIGNIFY
keria.core.authing module

Testing httping utils
"""

import falcon
import pytest
from falcon import testing
from hio.base import doing
from hio.help import Hict
from keri import kering
from keri import core
from keri.app import habbing
from keri.core import parsing, eventing
from keri.end import ending

from keria.app import agenting
from keria.core import authing


def test_authenticater(mockHelpingNowUTC):
    salt = b"1111456789abcdef"
    salter = core.Salter(raw=salt)

    with habbing.openHab(name="caid", salt=salt, temp=True) as (
        controllerHby,
        controller,
    ):
        agency = agenting.Agency(name="agency", base="", bran=None, temp=True)
        authn = authing.Authenticater(agency=agency)

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

        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))

        with pytest.raises(
            kering.AuthNError
        ):  # Should fail if Agent hasn't resolved caid's KEL
            authn.verify(req)

        agentKev = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)

        assert controller.pre in agent.agentHab.kevers

        assert authn.verify(req)

        headers = Hict(
            [
                ("Content-Type", "application/json"),
                ("Content-Length", "256"),
                ("Connection", "close"),
                ("Signify-Resource", agent.agentHab.pre),
                ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
            ]
        )

        headers = authn.sign(agent, headers, method="POST", path="/oobis")
        assert dict(headers) == {
            "Connection": "close",
            "Content-Length": "256",
            "Content-Type": "application/json",
            "Signature": 'indexed="?0";signify="0BCvA13DTtpHGEHpySuP2Pg26xMZvbFdQjOOrHo1DJLEN-IjoCyKQs7dkrNW16AWcLnF2gHo2WcPxgkx2PhCRAoB"',
            "Signature-Input": 'signify=("signify-resource" "@method" "@path" '
            '"signify-timestamp");created=1609459200;keyid="EEAJjjsbswsipSk6qypNw9bKszVfkAWvAYonKTKWHnDt";alg="ed25519"',
            "Signify-Resource": "EEAJjjsbswsipSk6qypNw9bKszVfkAWvAYonKTKWHnDt",
            "Signify-Timestamp": "2022-09-24T00:05:48.196795+00:00",
        }

        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))
        with pytest.raises(
            kering.AuthNError
        ):  # Should because the agent won't be found
            authn.verify(req)


class MockAgency:
    def __init__(self, agent=None):
        self.agent = agent

    def get(self, caid=None):
        return self.agent


class MockAuthN:
    def __init__(self, valid=False, error=None):
        self.valid = valid
        self.error = error

    def verify(self, _):
        if self.error is not None:
            raise self.error

        return self.valid

    @staticmethod
    def resource(_):
        return ""


def test_signature_validation(mockHelpingNowUTC):
    vc = authing.SignatureValidationComponent(
        agency=MockAgency(), authn=MockAuthN(), allowed=["/test", "/reward"]
    )

    req = testing.create_req(method="GET", path="/boot")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    req = testing.create_req(method="POST", path="/boot")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    req = testing.create_req(method="POST", path="/test")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = testing.create_req(method="POST", path="/reward")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    agent = object()
    vc = authing.SignatureValidationComponent(
        agency=MockAgency(agent=agent),
        authn=MockAuthN(valid=True),
        allowed=["/test", "/reward"],
    )

    req = testing.create_req(method="POST", path="/test")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = testing.create_req(method="POST", path="/reward")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = testing.create_req(method="GET", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    req = testing.create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is False
    assert rep.status == falcon.HTTP_200

    vc = authing.SignatureValidationComponent(
        agency=MockAgency(), authn=MockAuthN(error=kering.AuthNError())
    )
    req = testing.create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    vc = authing.SignatureValidationComponent(
        agency=MockAgency(), authn=MockAuthN(error=ValueError())
    )
    req = testing.create_req(method="POST", path="/identifiers")
    rep = falcon.Response()

    vc.process_request(req, rep)
    assert rep.complete is True
    assert rep.status == falcon.HTTP_401

    salt = b"0000456789abcdef"
    salter = core.Salter(raw=salt)
    with habbing.openHab(name="caid", salt=salt, temp=True) as (
        controllerHby,
        controller,
    ):
        agency = agenting.Agency(name="agency", base="", bran=None, temp=True)
        authn = authing.Authenticater(agency=agency)

        # Initialize Hio so it will allow for the addition of an Agent hierarchy
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        agent = agency.create(caid=controller.pre, salt=salter.qb64)
        req = testing.create_req(method="POST", path="/reward")
        req.context.agent = agent
        rep = falcon.Response()

        vc = authing.SignatureValidationComponent(agency=agency, authn=authn)
        vc.process_response(req, rep, None, True)
    assert rep.headers == {
        "signature": 'indexed="?0";signify="0BBwpBCjtO7un6C-8MiLQ0X8gQxU32PbBifGe0VEYlXXuwP19f-unbvi6FMOx5nnVk9SeEnY_sG9VIjvGVTrvn0K"',
        "signature-input": 'signify=("signify-resource" "@method" "@path" '
        '"signify-timestamp");created=1609459200;keyid="EGdzwqMk6992Hu94GitG_L9j-yVrjdz3BmhwT0mRgos0";alg="ed25519"',
        "signify-resource": "EGdzwqMk6992Hu94GitG_L9j-yVrjdz3BmhwT0mRgos0",
        "signify-timestamp": "2021-01-01T00:00:00.000000+00:00",
    }
