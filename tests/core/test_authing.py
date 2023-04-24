# -*- encoding: utf-8 -*-
"""
SIGNIFY
keria.core.authing module

Testing httping utils
"""
import pytest
from falcon import testing
from hio.base import doing
from hio.help import Hict
from keri import kering
from keri.app import habbing
from keri.core import parsing, eventing
from keri.end import ending

from keria.app import agenting
from keria.core import authing


def test_authenticater(mockHelpingNowUTC):
    salt = b'0123456789abcdef'
    with habbing.openHab(name="caid", salt=salt, temp=True) as (controllerHby, controller):

        agency = agenting.Agency(name="agency", base='', bran=None, temp=True)
        authn = authing.Authenticater(agency=agency)

        # Initialize Hio so it will allow for the addition of an Agent hierarchy
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        agent = agency.create(caid=controller.pre)

        # Create authenticater with Agent and controllers AID
        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", "256"),
            ("Connection", "close"),
            ("Signify-Resource", controller.pre),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        header, qsig = ending.siginput("signify", "POST", "/boot", headers, fields=authn.DefaultFields,
                                       hab=controller, alg="ed25519", keyid=controller.pre)
        headers.extend(header)
        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        assert dict(headers) == {'Connection': 'close',
                                 'Content-Length': '256',
                                 'Content-Type': 'application/json',
                                 'Signature': 'indexed="?0";signify="0BA9SX7Jyn66ZdCPOb0WqDEn1UC49GeSPypjVgeMrt6VLWKjEw'
                                              '9ij7Ndur7Wcrru_5eQNbSiNaiP4NQYWht5srEL"',
                                 'Signature-Input': 'signify=("signify-resource" "@method" "@path" '
                                                    '"signify-timestamp");created=1609459200;keyid="EJPEPKslRHD_fkug3zm'
                                                    'oyjQ90DazQAYWI8JIrV2QXyhg";alg="ed25519"',
                                 'Signify-Resource': 'EJPEPKslRHD_fkug3zmoyjQ90DazQAYWI8JIrV2QXyhg',
                                 'Signify-Timestamp': '2022-09-24T00:05:48.196795+00:00'}

        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))

        with pytest.raises(kering.AuthNError):  # Should fail if Agent hasn't resolved caid's KEL
            authn.verify(req)

        agentKev = eventing.Kevery(db=agent.agentHab.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)

        assert controller.pre in agent.agentHab.kevers

        assert authn.verify(req)
