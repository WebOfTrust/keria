"""
Configure PyTest

Use this module to configure pytest
https://docs.pytest.org/en/latest/pythonpath.html

"""
import json
import os
import shutil
from contextlib import contextmanager

import falcon
import pytest
from falcon import testing
from keri.app import keeping, habbing
from keri.core import coring, eventing
from keri.core.coring import MtrDex
from keri.help import helping
from keri.vdr import credentialing

from keria.app import agenting

WitnessUrls = {
    "wan:tcp": "tcp://127.0.0.1:5632/",
    "wan:http": "http://127.0.0.1:5642/",
    "wes:tcp": "tcp://127.0.0.1:5634/",
    "wes:http": "http://127.0.0.1:5644/",
    "wil:tcp": "tcp://127.0.0.1:5633/",
    "wil:http": "http://127.0.0.1:5643/",
}


@pytest.fixture()
def mockHelpingNowUTC(monkeypatch):
    """
    Replace nowUTC universally with fixed value for testing
    """

    def mockNowUTC():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return helping.fromIso8601("2021-01-01T00:00:00.000000+00:00")

    monkeypatch.setattr(helping, "nowUTC", mockNowUTC)


@pytest.fixture()
def mockHelpingNowIso8601(monkeypatch):
    """
    Replace nowIso8601 universally with fixed value for testing
    """

    def mockNowIso8601():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return "2021-06-27T21:26:21.233257+00:00"

    monkeypatch.setattr(helping, "nowIso8601", mockNowIso8601)

@pytest.fixture()
def mockCoringRandomNonce(monkeypatch):
    """ Replay randomNonce with fixed falue for testing"""

    def mockRandomNonce():
        return "A9XfpxIl1LcIkMhUSCCC8fgvkuX8gG9xK3SM-S8a8Y_U"

    monkeypatch.setattr(coring, "randomNonce", mockRandomNonce)


class Helpers:

    @staticmethod
    def remove_test_dirs(name):
        if os.path.exists(f'/usr/local/var/keri/db/{name}'):
            shutil.rmtree(f'/usr/local/var/keri/db/{name}')
        if os.path.exists(f'/usr/local/var/keri/ks/{name}'):
            shutil.rmtree(f'/usr/local/var/keri/ks/{name}')
        if os.path.exists(f'/usr/local/var/keri/reg/{name}'):
            shutil.rmtree(f'/usr/local/var/keri/reg/{name}')
        if os.path.exists(f'/usr/local/var/keri/cf/{name}.json'):
            os.remove(f'/usr/local/var/keri/cf/{name}.json')
        if os.path.exists(f'/usr/local/var/keri/cf/{name}'):
            shutil.rmtree(f'/usr/local/var/keri/cf/{name}')
        if os.path.exists(f'~/.keri/db/{name}'):
            shutil.rmtree(f'~/.keri/db/{name}')
        if os.path.exists(f'~/.keri/ks/{name}'):
            shutil.rmtree(f'~/.keri/ks/{name}')
        if os.path.exists(f'~/.keri/reg/{name}'):
            shutil.rmtree(f'~/.keri/reg/{name}')
        if os.path.exists(f'~/.keri/cf/{name}.json'):
            os.remove(f'~/.keri/cf/{name}.json')
        if os.path.exists(f'~/.keri/cf/{name}'):
            shutil.rmtree(f'~/.keri/cf/{name}')

    @staticmethod
    def incept(bran, stem, pidx, count=1, sith="1", wits=None, toad="0"):
        if wits is None:
            wits = []

        salter = coring.Salter(raw=bran)
        creator = keeping.SaltyCreator(salt=salter.qb64, stem=stem, tier=coring.Tiers.low)

        signers = creator.create(pidx=pidx, ridx=0, tier=coring.Tiers.low, temp=False, count=count)
        nsigners = creator.create(pidx=pidx, ridx=1, tier=coring.Tiers.low, temp=False, count=count)

        keys = [signer.verfer.qb64 for signer in signers]
        ndigs = [coring.Diger(ser=nsigner.verfer.qb64b) for nsigner in nsigners]

        serder = eventing.incept(keys=keys,
                                 isith=sith,
                                 nsith=sith,
                                 ndigs=[diger.qb64 for diger in ndigs],
                                 code=coring.MtrDex.Blake3_256,
                                 toad=toad,
                                 wits=wits)

        return serder, signers

    @staticmethod
    def createAid(client, name, salt):
        serder, signers = Helpers.incept(salt, "signify:aid", pidx=0)
        assert len(signers) == 1

        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': name,
                'icp': serder.ked,
                'sigs': sigers,
                "salty": {
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low',
                    'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200
        return res.json

    @staticmethod
    def endrole(cid, eid):
        data = dict(cid=cid, role="agent", eid=eid)
        return eventing.reply(route="/end/role/add", data=data)

    @staticmethod
    def middleware(agent):
        return MockAgentMiddleware(agent=agent)

    @staticmethod
    @contextmanager
    def openKeria(caid, salter, cf, temp=True):
        with habbing.openHby(name="keria", salt=salter.qb64, temp=temp, cf=cf) as hby:

            agency = agenting.Agency(name="agency", base=None, bran=None, temp=True)
            agentHab = hby.makeHab(caid, ns="agent", transferable=True, data=[caid])

            rgy = credentialing.Regery(hby=hby, name=agentHab.name, base=hby.base, temp=True)
            agent = agenting.Agent(hby=hby, rgy=rgy, agentHab=agentHab, agency=agency, caid=caid)

            app = falcon.App()
            app.add_middleware(Helpers.middleware(agent))
            client = testing.TestClient(app)
            yield agency, agent, app, client


@pytest.fixture
def helpers():
    return Helpers


class MockAgentMiddleware:

    def __init__(self, agent):
        self.agent = agent

    def process_request(self, req, resp):
        """ Process request to ensure has a valid signature from caid

        Parameters:
            req: Http request object
            resp: Http response object


        """
        req.context.agent = self.agent
