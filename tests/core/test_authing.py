# -*- encoding: utf-8 -*-
"""
SIGNIFY
keria.core.authing module

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
    with habbing.openHab(name="ctrlAid", salt=salt, temp=True) as (controllerHby, controller), \
            habbing.openHab(name="ahab", salt=salt, temp=True) as (agentHby, agent):

        # Create authenticater with Agent and controllers AID
        authn = authing.Authenticater(agent=agent, ctrlAid=controller.pre)
        signer = authing.Authenticater(agent=controller, ctrlAid=agent.pre)

        rep = falcon.Response()
        with pytest.raises(kering.AuthNError):  # Should fail if Agent hasn't resolved ctrlAid's KEL
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
                                 'Signature': 'indexed="?0";signify="0BBiMWsrTn_MEjz0uJ1IG8lhG_xhfKfOmc3_wt1ul_xY6jFx6'
                                              'EasHbB6RDM1jrboFDx2ULt425efzbeq5zKn9G4J"',
                                 'Signature-Input': 'signify=("signify-resource" "@method" "@path" '
                                                    '"signify-timestamp");created=1609459200;keyid="ECaJaP75uGKZOcDZqj'
                                                    'CbnjZ3L0jre6XWhKxoR3kloHoH";alg="ed25519"',
                                 'Signify-Resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
                                 'Signify-Timestamp': '2022-09-24T00:05:48.196795+00:00'}

        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))
        assert authn.verify(req)
