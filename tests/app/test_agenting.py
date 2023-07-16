# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

Testing the Mark II Agent
"""
import json
import os
import shutil

import falcon
from falcon import testing
from hio.base import doing
from hio.help import decking
from keri import kering
from keri.app import habbing, configing, oobiing
from keri.app.agenting import Receiptor
from keri.core import coring
from keri.core.coring import MtrDex
from keri.db import basing
from keri.vdr import credentialing

from keria.app import agenting, aiding
from keria.core import longrunning


def test_setup():
    doers = agenting.setup(name="test", bran=None, adminPort=1234, bootPort=5678)
    assert len(doers) == 3
    assert isinstance(doers[0], agenting.Agency) is True

    doers = agenting.setup("test", bran=None, adminPort=1234, bootPort=5678, httpPort=9999)
    assert len(doers) == 4


def test_load_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        agenting.loadEnds(app=app)
        assert app._router is not None

        res = app._router.find("/test")
        assert res is None

        (end, *_) = app._router.find("/operations/NAME")
        assert isinstance(end, longrunning.OperationResourceEnd)
        (end, *_) = app._router.find("/oobis")
        assert isinstance(end, agenting.OOBICollectionEnd)
        (end, *_) = app._router.find("/oobis/ALIAS")
        assert isinstance(end, agenting.OobiResourceEnd)
        (end, *_) = app._router.find("/states")
        assert isinstance(end, agenting.KeyStateCollectionEnd)
        (end, *_) = app._router.find("/events")
        assert isinstance(end, agenting.KeyEventCollectionEnd)
        (end, *_) = app._router.find("/queries")
        assert isinstance(end, agenting.QueryCollectionEnd)


def test_agency():
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hab = hby.makeHab(name="test")

        agency = agenting.Agency(name="agency", base="", bran=None, temp=True, configFile="keria",
                                 configDir="scripts")
        assert agency.cf is not None
        assert agency.cf.path.endswith("scripts/keri/cf/keria.json") is True

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        doist.enter(doers=[agency])

        caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
        agent = agency.create(caid)
        assert agent.pre == "EIAEKYpTygdBtFHBrHKWeh0aYCdx0ZJqZtzQLFnaDB2b"

        badcaid = "E987eerAdhmvrjDeam2eAO2SR5niCgnjAJXJHtJoe"
        agent = agency.get(badcaid)
        assert agent is None

        agent = agency.get(caid)
        assert agent.pre == "EIAEKYpTygdBtFHBrHKWeh0aYCdx0ZJqZtzQLFnaDB2b"

        agency.incept(caid, hab.pre)

        agent = agency.lookup(badcaid)
        assert agent is None

        agent = agency.lookup(hab.pre)
        assert agent.pre == "EIAEKYpTygdBtFHBrHKWeh0aYCdx0ZJqZtzQLFnaDB2b"

        # Create non-temp Agency and test reload of agent from disk
        base = "keria-temp"

        # Clean up afterwards
        if os.path.exists(f'/usr/local/var/keri/db/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/db/{base}')
        if os.path.exists(f'/usr/local/var/keri/ks/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/ks/{base}')
        if os.path.exists(f'/usr/local/var/keri/ks/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/ks/{base}')
        if os.path.exists(f'/usr/local/var/keri/adb/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/adb/{base}')

        agency = agenting.Agency(name="agency", base=base, bran=None, configFile="keria",
                                 configDir="scripts")
        assert agency.cf is not None
        assert agency.cf.path.endswith("scripts/keri/cf/keria.json") is True

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        doist.enter(doers=[agency])

        caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
        agent = agency.create(caid)
        assert agent.pre == "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"

        # Rcreate the agency to see if agent is reloaded from disk
        agency = agenting.Agency(name="agency", base=base, bran=None, configFile="keria",
                                 configDir="scripts")
        agent = agency.get(caid)
        assert agent.pre == "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"

        # Clean up afterwards
        if os.path.exists(f'/usr/local/var/keri/db/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/db/{base}')
        if os.path.exists(f'/usr/local/var/keri/ks/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/ks/{base}')
        if os.path.exists(f'/usr/local/var/keri/ks/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/ks/{base}')
        if os.path.exists(f'/usr/local/var/keri/adb/{base}'):
            shutil.rmtree(f'/usr/local/var/keri/adb/{base}')


def test_boot_ends(helpers):
    agency = agenting.Agency(name="agency", bran=None, temp=True)
    doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
    doist.enter(doers=[agency])

    serder, sigers = helpers.controller()
    assert serder.pre == helpers.controllerAID

    app = falcon.App()
    client = testing.TestClient(app)

    bootEnd = agenting.BootEnd(agency)
    app.add_route("/boot", bootEnd)

    body = dict(
        icp=serder.ked,
        sig=sigers[0].qb64,
        salty=dict(
            stem='signify:aid', pidx=0, tier='low', sxlt='OBXYZ',
            icodes=[MtrDex.Ed25519_Seed], ncodes=[MtrDex.Ed25519_Seed]
        )
    )

    rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"))
    assert rep.status_code == 202

    rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"))
    assert rep.status_code == 400
    assert rep.json == {
        'title': 'agent already exists',
        'description': 'agent for controller EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx already exists'
    }


def test_witnesser(helpers):
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True) as hby:
        witners = decking.Deck()
        receiptor = Receiptor(hby=hby)
        wr = agenting.Witnesser(receiptor=receiptor, witners=witners)

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)

        # doist.do(doers=doers)
        deeds = doist.enter(doers=[wr])
        doist.recur(deeds)

def test_keystate_ends(helpers):
    caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    salt = b'0123456789abcdef'
    salter = coring.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hab = hby.makeHab(name="test")
        agency = agenting.Agency(name="agency", bran=None, temp=True)
        agentHab = hby.makeHab(caid, ns="agent", transferable=True, data=[caid])

        rgy = credentialing.Regery(hby=hby, name=agentHab.name, base=hby.base, temp=True)
        agent = agenting.Agent(hby=hby, rgy=rgy, agentHab=agentHab, agency=agency, caid=caid)

        end = agenting.KeyStateCollectionEnd()

        app = falcon.App()
        app.add_middleware(helpers.middleware(agent))
        app.add_route("/states", end)

        client = testing.TestClient(app)

        res = client.simulate_get(f"/states?pre={hab.pre}")
        states = res.json
        assert len(states) == 1

        state = states[0]
        assert state['i'] == hab.pre
        assert state['d'] == "EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3"
        assert state['et'] == 'icp'
        assert state['k'] == ['DGmIfLmgErg4zFHfPwaDckLNxsLqc5iS_P0QbLjbWR0I']
        assert state['n'] == ['EJhRr10e5p7LVB6JwLDIcgqsISktnfe5m60O_I2zZO6N']
        assert state['ee'] == {'ba': [],
                               'br': [],
                               'd': 'EIaGMMWJFPmtXznY1IIiKDIrg-vIyge6mBl2QV8dDjI3',
                               's': '0'}


def test_oobi_ends(seeder, helpers):
    with helpers.openKeria() as (agency, agent, app, client), \
            habbing.openHby(name="wes", salt=coring.Salter(raw=b'wess-the-witness').qb64) as wesHby:
        wesHab = wesHby.makeHab(name="wes", transferable=False)

        # Register the identifier endpoint so we can create an AID for the test
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)
        salt = b'0123456789abcdef'
        helpers.createAid(client, "pal", salt, wits=[wesHab.pre], toad="1")
        palPre = "EEkruFP-J0InOD9cYbNLlBxQtkLAbmJPNecSnBzJixP0"

        oobiery = oobiing.Oobiery(hby=agent.hby)

        oobiColEnd = agenting.OOBICollectionEnd()
        app.add_route("/oobi", oobiColEnd)
        oobiResEnd = agenting.OobiResourceEnd()
        app.add_route("/oobi/{alias}", oobiResEnd)

        result = client.simulate_get(path="/oobi/test?role=witness")
        assert result.status == falcon.HTTP_400  # Bad alias, does not exist

        result = client.simulate_get(path="/oobi/pal?role=watcher")
        assert result.status == falcon.HTTP_404  # Bad role, watcher not supported yet

        result = client.simulate_get(path="/oobi/pal?role=witness")
        assert result.status == falcon.HTTP_404  # Missing OOBI endpoints for witness

        result = client.simulate_get(path="/oobi/pal?role=controller")
        assert result.status == falcon.HTTP_404  # Missing OOBI controller endpoints

        # Add controller endpoints
        url = "http://127.0.0.1:9999"
        agent.hby.db.locs.put(keys=(palPre, kering.Schemes.http), val=basing.LocationRecord(url=url))
        result = client.simulate_get(path="/oobi/pal?role=controller")
        assert result.status == falcon.HTTP_200  # Missing OOBI controller endpoints
        assert result.json == {
            'oobis': ['http://127.0.0.1:9999/oobi/EEkruFP-J0InOD9cYbNLlBxQtkLAbmJPNecSnBzJixP0/controller'],
            'role': 'controller'}

        # Seed with witness endpoints
        seeder.seedWitEnds(agent.hby.db, witHabs=[wesHab], protocols=[kering.Schemes.http, kering.Schemes.tcp])

        result = client.simulate_get(path="/oobi/pal?role=witness")
        assert result.status == falcon.HTTP_200
        assert result.json == {
            'oobis': [
                'http://127.0.0.1:5644/oobi/EEkruFP-J0InOD9cYbNLlBxQtkLAbmJPNecSnBzJixP0/witness/BN8t3n1lxcV0SWGJIIF'
                '46fpSUqA7Mqre5KJNN3nbx3mr'],
            'role': 'witness'}

        # Post without a URL or RPY
        data = dict()
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/oobi", body=b)
        assert result.status == falcon.HTTP_400

        # Post an RPY
        data = dict(rpy={})
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/oobi", body=b)
        assert result.status == falcon.HTTP_501

        data = dict(url="http://127.0.0.1:5644/oobi/E6Dqo6tHmYTuQ3Lope4mZF_4hBoGJl93cBHRekr_iD_A/witness/")
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/oobi", body=b)
        assert result.status == falcon.HTTP_202
        assert oobiery.hby.db.oobis.cntAll() == 1
        (url,), item = next(oobiery.hby.db.oobis.getItemIter())
        assert item is not None
        assert url == 'http://127.0.0.1:5644/oobi/E6Dqo6tHmYTuQ3Lope4mZF_4hBoGJl93cBHRekr_iD_A/witness/'
        oobiery.hby.db.oobis.rem(keys=(url,))

        # Post an RPY
        data = dict(oobialias="sal", rpy={})
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/oobi", body=b)
        assert result.status == falcon.HTTP_501

        # POST without an oobialias
        data = dict(url="http://127.0.0.1:5644/oobi/E6Dqo6tHmYTuQ3Lope4mZF_4hBoGJl93cBHRekr_iD_A/witness/")
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/oobi", body=b)
        assert result.status == falcon.HTTP_202
        assert oobiery.hby.db.oobis.cntAll() == 1
        (url,), item = next(oobiery.hby.db.oobis.getItemIter())
        assert item is not None
        assert url == 'http://127.0.0.1:5644/oobi/E6Dqo6tHmYTuQ3Lope4mZF_4hBoGJl93cBHRekr_iD_A/witness/'
        assert item.oobialias is None
        oobiery.hby.db.oobis.rem(keys=(url,))

        data = dict(oobialias="sal", url="http://127.0.0.1:5644/oobi/E6Dqo6tHmYTuQ3Lope4mZF_4hBoGJl93cBHRekr_iD_A"
                                         "/witness/")
        b = json.dumps(data).encode("utf-8")
        result = client.simulate_post(path="/oobi", body=b)
        assert result.status == falcon.HTTP_202
        assert oobiery.hby.db.oobis.cntAll() == 1
        (url,), item = next(oobiery.hby.db.oobis.getItemIter())
        assert item is not None
        assert url == 'http://127.0.0.1:5644/oobi/E6Dqo6tHmYTuQ3Lope4mZF_4hBoGJl93cBHRekr_iD_A/witness/'
        assert item.oobialias == 'sal'

        op = helpers.createAid(client, "aggie", salt)
        aid = op["response"]
        aggiePre = aid['i']
        assert aggiePre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        keys = (aggiePre, kering.Roles.agent, agent.agentHab.pre)
        ender = basing.EndpointRecord(allowed=True)
        agent.hby.db.ends.pin(keys=keys, val=ender)  # overwrite
        url = "http://127.0.0.1:3902"
        agent.hby.db.locs.put(keys=(agent.agentHab.pre, kering.Schemes.http), val=basing.LocationRecord(url=url))

        result = client.simulate_get(path="/oobi/aggie?role=agent")
        assert result.status == falcon.HTTP_200
        assert result.json == {'oobis': ['http://127.0.0.1:3902/oobi/EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY/agent'
                                         '/EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9'],
                               'role': 'agent'}
