# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

Testing the Mark II Agent
"""
from base64 import b64encode
import json
import os
import shutil

import pytest

import falcon
import hio
from falcon import testing
from hio.base import doing, tyming
from hio.core import http, tcp
from hio.help import decking
from keri import kering
from keri.app import habbing, configing, indirecting, oobiing, querying
from keri.app.agenting import Receiptor, WitnessReceiptor
from keri import core
from keri.core import coring, serdering
from keri.core.coring import MtrDex
from keri.db import basing, dbing
from keri.help import nowIso8601
from keri.vc import proving
from keri.vdr import credentialing

from keria.app import agenting, aiding
from keria.core import longrunning
from keria.testing.testing_helper import SCRIPTS_DIR


def test_setup_no_http():
    doers = agenting.setup(name="test", bran=None, adminPort=1234, bootPort=5678)
    assert len(doers) == 3
    assert isinstance(doers[0], agenting.Agency) is True

def test_setup():
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
        (end, *_) = app._router.find("/config")
        assert isinstance(end, agenting.ConfigResourceEnd)


def test_load_tocks_config(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        agenting.loadEnds(app=app)
        assert app._router is not None

        assert agent.cfd == {
            "dt": "2022-01-20T12:57:59.823350+00:00",
            "keria": {
                "dt": "2022-01-20T12:57:59.823350+00:00",
                "curls": ["http://127.0.0.1:3902/"]
            },
            "EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx": {
                "dt": "2022-01-20T12:57:59.823350+00:00",
                "curls": ["http://127.0.0.1:3902/"]
            },
            "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9": {
                "dt": "2022-01-20T12:57:59.823350+00:00",
                "curls": ["http://127.0.0.1:3902/"]
            },
            "iurls": [
                "http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller&tag=witness"
            ],
            "tocks": {
                "initer": 0.0,
                "escrower": 1.0
            }
        }

        assert agent.tocks == {
            "initer": 0.0,
            "escrower": 1.0
        }

        escrower_doer = next((doer for doer in agent.doers if isinstance(doer, agenting.Escrower)), None)
        assert escrower_doer is not None
        assert escrower_doer.tock == 1.0

        initer_doer = next((doer for doer in agent.doers if isinstance(doer, agenting.Initer)), None)
        assert initer_doer is not None
        assert initer_doer.tock == 0.0

        querier_doer = next((doer for doer in agent.doers if isinstance(doer, agenting.Querier)), None)
        assert querier_doer is not None
        assert querier_doer.tock == 0.0

        with pytest.raises(TypeError):
            agent.tocks["initer"] = 1.0 # agent.tocks is read-only


def test_agency():
    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath=SCRIPTS_DIR, temp=True, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hab = hby.makeHab(name="test")

        agency = agenting.Agency(name="agency", base="", bran=None, temp=True, configFile="keria",
                                 configDir=SCRIPTS_DIR)
        assert agency.cf is not None
        assert agency.cf.path.endswith("scripts/keri/cf/keria.json") is True

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        doist.enter(doers=[agency])

        caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
        agent = agency.create(caid, salt=salter.qb64)
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
                                 configDir=SCRIPTS_DIR)
        assert agency.cf is not None
        assert agency.cf.path.endswith("scripts/keri/cf/keria.json") is True

        tock = 0.03125
        limit = 1.0
        doist = doing.Doist(limit=limit, tock=tock, real=True)
        doist.enter(doers=[agency])

        caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
        agent = agency.create(caid, salt=salter.qb64)
        assert agent.pre == "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"

        # Rcreate the agency to see if agent is reloaded from disk
        agency = agenting.Agency(name="agency", base=base, bran=None, configFile="keria",
                                 configDir=SCRIPTS_DIR)
        doist.enter(doers=[agency])

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

        agency.shut(agent)
        assert caid not in agency.agents
        assert len(agent.doers) == 0

def test_agency_without_config_file():
    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath=SCRIPTS_DIR, temp=True, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hby.makeHab(name="test")

        agency = agenting.Agency(name="agency", base="", bran=None, temp=True, configFile=None, configDir=SCRIPTS_DIR)
        assert agency.cf is None

        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.extend(doers=[agency])

        # Ensure we can still create agent
        caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
        agent = agency.create(caid, salt=salter.qb64)
        assert agent.pre == "EIAEKYpTygdBtFHBrHKWeh0aYCdx0ZJqZtzQLFnaDB2b"

def test_agency_with_urls_from_arguments():
    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath=SCRIPTS_DIR, temp=True, reopen=True, clear=False)

    with habbing.openHby(name="keria", salt=salter.qb64, temp=True, cf=cf) as hby:
        hby.makeHab(name="test")

        curls = ["http://example.com:3902/"]
        iurls = ["http://example.com:5432/oobi"]
        durls = ["http://example.com:7723/oobi"]
        agency = agenting.Agency(name="agency", base="", bran=None, temp=True, configDir=SCRIPTS_DIR, curls=curls, iurls=iurls, durls=durls)
        assert agency.cf is None

        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.extend(doers=[agency])

        # Ensure we can still create agent
        caid = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
        agent = agency.create(caid, salt=salter.qb64)
        assert agent.pre == "EIAEKYpTygdBtFHBrHKWeh0aYCdx0ZJqZtzQLFnaDB2b"

        assert agent.hby.cf is not None
        assert agent.hby.cf.get()[f"agent-{caid}"]["curls"] == curls
        assert agent.hby.cf.get()["iurls"] == iurls
        assert agent.hby.cf.get()["durls"] == durls

def test_unprotected_boot_ends(helpers):
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
    assert rep.status_code == 409
    assert rep.json == {
        'title': 'agent already exists',
        'description': 'agent for controller EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx already exists'
    }

def test_protected_boot_ends(helpers):
    credentials = [
        dict(bran=b'0123456789abcdefghija', username="user", password="secret"), 
        dict(bran=b'0123456789abcdefghijb', username="admin", password="secret with spaces"),
        dict(bran=b'0123456789abcdefghijc', username="admin", password="secret : with colon")
    ]

    for credential in credentials:
        bran = credential["bran"]
        username = credential["username"]
        password = credential["password"]

        agency = agenting.Agency(name="agency", bran=None, temp=True)
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        doist.enter(doers=[agency])

        serder, sigers = helpers.controller(bran=bran)

        app = falcon.App()
        client = testing.TestClient(app)

        bootEnd = agenting.BootEnd(agency, username=username, password=password)
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
        assert rep.status_code == 401

        rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": "Something test"})
        assert rep.status_code == 401

        rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Basic {username}:{password}"})
        assert rep.status_code == 401

        rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Basic {b64encode(bytes(f'test:{password}', 'utf-8')).decode('utf-8')}"} )
        assert rep.status_code == 401

        rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Basic {b64encode(bytes(f'{username}', 'utf-8')).decode('utf-8')}"} )
        assert rep.status_code == 401

        rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": f"Basic {b64encode(bytes(f'{username}:test', 'utf-8')).decode('utf-8')}"} )
        assert rep.status_code == 401

        authorization = f"Basic {b64encode(bytes(f'{username}:{password}', 'utf-8')).decode('utf-8')}"
        rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": authorization})
        assert rep.status_code == 202

def test_misconfigured_protected_boot_ends(helpers):
    agency = agenting.Agency(name="agency", bran=None, temp=True)
    doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
    doist.enter(doers=[agency])

    serder, sigers = helpers.controller()
    assert serder.pre == helpers.controllerAID

    app = falcon.App()
    client = testing.TestClient(app)

    # No password set, should return 401
    bootEnd = agenting.BootEnd(agency, username="user", password=None)
    app.add_route("/boot", bootEnd)

    body = dict(
        icp=serder.ked,
        sig=sigers[0].qb64,
        salty=dict(
            stem='signify:aid', pidx=0, tier='low', sxlt='OBXYZ',
            icodes=[MtrDex.Ed25519_Seed], ncodes=[MtrDex.Ed25519_Seed]
        )
    )

    authorization = f"Basic {b64encode(b'user').decode('utf-8')}"
    rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": authorization})
    assert rep.status_code == 401

    authorization = f"Basic {b64encode(b'user:secret').decode('utf-8')}"
    rep = client.simulate_post("/boot", body=json.dumps(body).encode("utf-8"), headers={"Authorization": authorization})
    assert rep.status_code == 401

def test_witnesser(helpers):
    salt = b'0123456789abcdef'
    salter = core.Salter(raw=salt)

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
    salter = core.Salter(raw=salt)
    cf = configing.Configer(name="keria", headDirPath=SCRIPTS_DIR, temp=True, reopen=True, clear=False)

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
            habbing.openHby(name="wes", salt=core.Salter(raw=b'wess-the-witness').qb64) as wesHby:
        wesHab = wesHby.makeHab(name="wes", transferable=False)

        result = client.simulate_get(path="/oobi/pal?role=witness")
        assert result.status == falcon.HTTP_404  # Missing OOBI endpoints for witness

        # Add witness endpoints
        url = "http://127.0.0.1:9999"
        agent.hby.db.locs.put(keys=(wesHab.pre, kering.Schemes.http), val=basing.LocationRecord(url=url))

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
        assert result.status == falcon.HTTP_200

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

        # initiated from keria.json config file (iurls), so remove
        oobiery.hby.db.oobis.rem(keys=("http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller&tag=witness",))

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



def test_querier(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        qry = agenting.Querier(hby=agent.hby, agentHab=agent.agentHab, queries=decking.Deck(), kvy=agent.kvy)
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        deeds = doist.enter(doers=[qry])

        qry.queries.append(dict(pre="EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9", sn="1"))
        qry.recur(1.0, deeds=deeds)

        assert len(qry.doers) == 1
        seqNoDoer = qry.doers[0]
        assert isinstance(seqNoDoer, querying.SeqNoQuerier) is True
        assert seqNoDoer.pre == "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"
        assert seqNoDoer.sn == 1

        qry.doers.remove(seqNoDoer)

        # Anchor not implemented yet
        qry.queries.append(dict(pre="EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9", anchor={}))
        qry.recur(1.0, deeds=deeds)
        assert len(qry.doers) == 1
        anchorDoer = qry.doers[0]
        assert isinstance(anchorDoer, querying.AnchorQuerier) is True
        assert anchorDoer.pre == "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"
        assert anchorDoer.anchor == {}
        qry.doers.remove(anchorDoer)

        qry.queries.append(dict(pre="EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"))
        qry.recur(1.0, deeds=deeds)

        assert len(qry.doers) == 1
        qryDoer = qry.doers[0]
        assert isinstance(qryDoer, querying.QueryDoer) is True
        assert qryDoer.pre == "EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9"


def test_query_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        queryEnd = agenting.QueryCollectionEnd()
        app.add_route("/queries", queryEnd)

        result = client.simulate_post(path="/queries")
        assert result.status == falcon.HTTP_400

        result = client.simulate_post(path="/queries", body=json.dumps(dict()))
        assert result.status == falcon.HTTP_400

        body = dict(pre="EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9")
        result = client.simulate_post(path="/queries", body=json.dumps(body))
        assert result.status == falcon.HTTP_202
        assert result.json == {'done': False,
                               'error': None,
                               'metadata': {'pre': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9'},
                               'name': 'query.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9',
                               'response': None}
        assert len(agent.queries) == 1

        snbody = dict(pre="EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9", sn="2")
        result = client.simulate_post(path="/queries", body=json.dumps(snbody))
        assert result.status == falcon.HTTP_202
        assert result.json == {'done': False,
                               'error': None,
                               'metadata': {'pre': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9', 'sn': '2'},
                               'name': 'query.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9.2',
                               'response': None}
        assert len(agent.queries) == 2

        ancbody = dict(
            pre="EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9",
            anchor={"i": "EKQSWRXh_JHX61NdrL6wJ8ELMwG4zFY8y-sU1nymYzXZ", "s": "1", "d": "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"}
        )
        result = client.simulate_post(path="/queries", body=json.dumps(ancbody))
        assert result.status == falcon.HTTP_202
        assert result.json == {'done': False,
                               'error': None,
                               'metadata': {'pre': 'EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9',
                                            'anchor': {'i': 'EKQSWRXh_JHX61NdrL6wJ8ELMwG4zFY8y-sU1nymYzXZ', 's': '1', 'd': 'EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY'}},
                               'name': 'query.EI7AkI40M11MS7lkTCb10JC9-nDt-tXwQh44OHAFlv_9.EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY',
                               'response': None}
        assert len(agent.queries) == 3


class MockServerTls:
    def __init__(self,  certify, keypath, certpath, cafilepath, port):
        pass


class MockHttpServer:
    def __init__(self, port, app, servant=None):
        self.servant = servant


def test_createHttpServer(monkeypatch):
    port = 5632
    app = falcon.App()
    server = agenting.createHttpServer(port, app)
    assert isinstance(server, http.Server)

    monkeypatch.setattr(hio.core.tcp, 'ServerTls', MockServerTls)
    monkeypatch.setattr(hio.core.http, 'Server', MockHttpServer)

    server = agenting.createHttpServer(port, app, keypath='keypath', certpath='certpath',
                                          cafilepath='cafilepath')

    assert isinstance(server, MockHttpServer)
    assert isinstance(server.servant, MockServerTls)


def test_seeker_doer(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        cues = decking.Deck()
        seeker = agenting.SeekerDoer(agent.seeker, cues)

        creder = serdering.SerderACDC(sad={
            "v": "ACDC10JSON000197_",
            "d": "EG7ZlUq0Z6a1EUPTM_Qg1LGEg1BWiypHLAekxo8crGzK",
            "i": "EPbOCiPM7IItIMzMwslKWfPM4tqNIKUCyVVuYJNQHwMB",
            "ri": "EE5upBEf9JlH0ZCkZwLcNOOQYkiowcF7QBa-SDZg3GLo",
            "s": "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao",
            "a": {
                "d": "EH8sB2FZuSYBi6dj8edmPMxS-ZoikR2ova3LAVJvelMe",
                "i": "ECfRBXooQPoNNQC4i0bkwNfKm-VwV3QsUce14uFfejyj",
                "dt": "2023-11-07T23:38:05.508152+00:00",
                "LEI": "5493001KJTIIGC8Y1R17"
            }
        })

        assert creder.said == "EG7ZlUq0Z6a1EUPTM_Qg1LGEg1BWiypHLAekxo8crGzK"

        cues.append(dict(kin="saved", creder=creder))

        result = seeker.recur()
        assert result is False
        assert len(cues) == 1

def test_submitter(seeder, helpers):
    with helpers.openKeria() as (agency, agent, app, client), habbing.openHby(
        name="wes", salt=core.Salter(raw=b"wess-the-witness").qb64, temp=True
    ) as wesHby, habbing.openHby(
        name="wan", salt=core.Salter(raw=b"wann-the-witness").qb64, temp=True
    ) as wanHby:
        
        wesHab = wesHby.makeHab(name="wes", transferable=False)
        assert not wesHab.kever.prefixer.transferable

        wanPort = 5642
        wanDoers = indirecting.setupWitness(
            alias="wan", hby=wanHby, tcpPort=5632, httpPort=wanPort
        )
        wanHab = wanHby.habByName(name="wan")
        assert not wanHab.kever.prefixer.transferable
        witHabs = [wesHab, wanHab]
        witPrefixes = []
        for witHab in witHabs:
            witPrefixes.append(witHab.pre)

        seeder.seedWitEnds(agent.hby.db, witHabs=witHabs)

        # Register the identifier endpoint so we can create an AID for the test
        end = aiding.IdentifierCollectionEnd()
        app.add_route("/identifiers", end)

        opColEnd = longrunning.OperationCollectionEnd()
        app.add_route("/operations", opColEnd)
        opResEnd = longrunning.OperationResourceEnd()
        app.add_route("/operations/{name}", opResEnd)

        salt = b"0123456789abcdef"
        alias = "pal"
        createAidOp = helpers.createAid(client, name=alias, salt=salt, wits=witPrefixes, toad="1")
        hab = agent.hby.habByName(alias)
        serder = hab.iserder

        # no wigs yet
        dgkey = dbing.dgKey(serder.preb, hab.kever.serder.saidb)
        wigs = hab.db.getWigs(dgkey)
        assert len(wigs) == 0

        # no id key state in wit hab yet
        assert hab.pre not in wesHab.kvy.kevers

        # Intentionally manually process a single receipt from only one witness in order to reach the toad (threshold of acceptable duplicity)
        # while at the same time setting up the opportunity to submit the KEL to the other witness, later
        hab = agent.hby.habByName(alias)
        sn = 0
        msg = hab.makeOwnEvent(sn=sn)
        rctMsgs = helpers.witnessMsg(hab=hab, msg=msg, sn=sn, witHabs=[wesHab])
        wigs = hab.db.getWigs(dgkey)
        assert len(wigs) == 1 # only witnessed by one witness
        assert len(wesHab.kvy.db.getWigs(dgkey)) == 1  # only witnessed by one witness
        assert len(wanHab.kvy.db.getWigs(dgkey)) == 0  # only witnessed by the other witness
        assert len(wesHab.kvy.cues) == 0  # witness cues are empty
        assert hab.pre in wesHab.kvy.kevers  # id key state in wit hab
        assert hab.pre not in wanHab.kvy.kevers  # id key state not in wit hab yet
        
        witAidOp = client.simulate_get(path=f'/operations/{createAidOp["name"]}') # witnessing of created aid completed
        assert witAidOp.json["done"] is True # succeed because toad is 1
        assert witAidOp.json["response"]["i"] == hab.pre

        # Now we will setup to 'submit' (resubmit) the KEL to both witnesses 
        limit = 5.0
        tock = 0.03125
        wdoist = doing.Doist(limit=limit, tock=tock, doers=wanDoers)
        wdoist.enter()
        tymer = tyming.Tymer(tymth=wdoist.tymen(), duration=wdoist.limit)
        aidEnd = aiding.IdentifierResourceEnd()
        app.add_route("/identifiers/{name}/submit", aidEnd)
        resSubmit = client.simulate_post(
            path=f"/identifiers/{alias}/submit",
            body=json.dumps(dict(submit=alias)).encode("utf-8"),
        )
        submitter = agent.submitter # get the submitter that was triggered by the submit request
        sdoist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        sdeeds = sdoist.enter(doers=[submitter])
        submitter.recur(tyme=1.0, deeds=sdeeds) # run the submitter to get witness receipts (with WitnessReceiptor) for sn=0 of the KEL
        assert len(submitter.doers) == 1
        rectDoer = submitter.doers[0]
        assert isinstance(rectDoer, WitnessReceiptor) is True
        resSubmit = client.simulate_get(path=f'/operations/{resSubmit.json["name"]}')
        assert resSubmit.json["done"] is False

        stamp = nowIso8601()  # need same time stamp or not duplicate
        agent.witq.query(src=hab.pre, pre=wanHab.pre, stamp=stamp, wits=wanHab.kever.wits)
        agent.witq.query(src=hab.pre, pre=wanHab.pre, stamp=stamp, wits=wanHab.kever.wits)
        agent.witq.query(src=hab.pre, pre=wanHab.pre, stamp=stamp, wits=wanHab.kever.wits)

        # while not (resSubmit.json["done"] or tymer.expired):
        submitter.recur(tyme=1.0, deeds=sdeeds) # run the submitter to check for witness receipts (with WitnessReceiptor) for sn=0 of the KEL
        resSubmit = client.simulate_get(path=f'/operations/{resSubmit.json["name"]}')

        limit = 5.0
        tock = 0.03125
        doist = doing.Doist(limit=limit, tock=tock)
        doers = wanDoers + [rectDoer]
        doist.do(doers=doers)
        doist.recur()
        
        assert hab.pre in wanHab.kvy.kevers  # id key state in wit hab
        assert wanHab.kvy.kevers[hab.pre].sn == 0
        wanHab.processCues(wanHab.kvy.cues)  # process cue returns rct msg
        assert len(wanHab.kvy.db.getWigs(dgkey)) == 2  # now witnessed by the other witness
        assert len(wanHab.kvy.cues) == 0  # witness cues are empty
        assert hab.pre in wanHab.kvy.kevers  # id key state in wit hab yet
        assert wanHby.db.fullyWitnessed(hab.kever.serder)  # fully witnessed

        rctMsg = wanHab.replyToOobi(aid=hab.pre, role='controller')
        hab.psr.parse(ims=bytearray(rctMsg), kvy=hab.kvy, local=True)
        witMsg = wanHab.replyToOobi(aid=wanHab.pre, role='controller')
        hab.psr.parse(ims=bytearray(witMsg), kvy=hab.kvy, local=True)
        assert wanHab.pre in hab.kvy.kevers
        wigs = hab.db.getWigs(dgkey)
        assert len(wigs) == 2

        rectDoer.cues.append(dict(pre=hab.pre, sn=0)) # append expected cue
        submitter.recur(tyme=1.0, deeds=sdeeds)
        resSubmit = client.simulate_get(path=f'/operations/{resSubmit.json["name"]}')
        assert resSubmit.status_code == 200
        assert resSubmit.text == json.dumps(
            dict(
                name="submit.EKOrePIIU8ynKwOOLxs56ZxxQswUFNV8-cyYFt3nBJHR",
                metadata={"alias": "pal", "sn": 0},
                done=True,
                error=None,
                response={
                    "vn": [1, 0],
                    "i": "EKOrePIIU8ynKwOOLxs56ZxxQswUFNV8-cyYFt3nBJHR",
                    "s": "0",
                    "p": "",
                    "d": "EKOrePIIU8ynKwOOLxs56ZxxQswUFNV8-cyYFt3nBJHR",
                    "f": "0",
                    "dt": resSubmit.json["response"]["dt"],
                    "et": "icp",
                    "kt": "1",
                    "k": ["DDNGgXzEO4LD8G1z1uD7eIDF2pDj6Y7hVx-nqhYZmU_8"],
                    "nt": "1",
                    "n": ["EHj7rmVHVkQKqnfeer068PiYvYm-WFSTVZZpFGsClfT-"],
                    "bt": "1",
                    "b": ["BN8t3n1lxcV0SWGJIIF46fpSUqA7Mqre5KJNN3nbx3mr","BOigXdxpp1r43JhO--czUTwrCXzoWrIwW8i41KWDlr8s"],
                    "c": [],
                    "ee": {
                        "s": "0",
                        "d": "EKOrePIIU8ynKwOOLxs56ZxxQswUFNV8-cyYFt3nBJHR",
                        "br": [],
                        "ba": [],
                    },
                    "di": "",
                },
            )
        )


def test_config_ends(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        configEnd = agenting.ConfigResourceEnd()
        app.add_route("/config", configEnd)
        res = client.simulate_get(path="/config")
        assert res.status == falcon.HTTP_200
        assert res.json == {'iurls':
                            ['http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller&tag=witness']}
