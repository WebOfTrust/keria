# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.httping module

Testing httping utils
"""
import falcon
import pytest
from falcon import testing
from hio.help import Hict
from keri import kering
from keri.app import habbing
from keri.core import parsing, eventing

from keria.core import authing


def test_authenticater(mockHelpingNowUTC):
    salt = b'0123456789abcdef'
    with habbing.openHab(name="conAid", salt=salt, temp=True) as (controllerHby, controller), \
            habbing.openHab(name="ahab", salt=salt, temp=True) as (agentHby, agent):

        # Create authenticater with Agent and controllers AID
        authn = authing.Authenticater(agent=agent, caid=controller.pre)
        signer = authing.Authenticater(agent=controller, caid=agent.pre)

        rep = falcon.Response()
        with pytest.raises(kering.AuthNError):  # Should fail if Agent hasn't resolved conAid's KEL
            authn.verify(rep)

        agentKev = eventing.Kevery(db=agent.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)

        assert controller.pre in agent.kevers

        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", "256"),
            ("Connection", "close"),
            ("Signify-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        headers = signer.sign(headers, method="POST", path="/boot")
        assert dict(headers) == {'Connection': 'close',
                                 'Content-Length': '256',
                                 'Content-Type': 'application/json',
                                 'Signature': 'indexed="?0";signify="0BBuKkeizz5dM7MurQd7i3PyYh5kariHlZ0id01UJJfYfl5gKr'
                                              'Bg5BPsTKyIySCnQfBgEiCaDvC5NCC0kon_8QEI"',
                                 'Signature-Input': 'signify=("signify-resource" "@method" "@path" '
                                                    '"signify-timestamp");created=1609459200;keyid="EAM6vT0VYoaEWxRTgr'
                                                    '24g0nZHmPSUBgs19WB43zEKHnz";alg="ed25519"',
                                 'Signify-Resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
                                 'Signify-Timestamp': '2022-09-24T00:05:48.196795+00:00'}

        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))
        assert authn.verify(req)
