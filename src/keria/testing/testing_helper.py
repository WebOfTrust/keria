# -*- coding: utf-8 -*-
"""
Helpers for tests that need KERIA
"""
import os
import shutil
import json

import falcon
import pytest
from falcon import testing
from keri import kering
from keri.app import keeping, habbing, configing
from keri.core import coring, eventing, parsing, routing, scheming
from keri.core.coring import MtrDex
from keri.help import helping
from keri.vdr import credentialing
from keria.app import agenting
from contextlib import contextmanager

WitnessUrls = {
    "wan:tcp": "tcp://127.0.0.1:5632/",
    "wan:http": "http://127.0.0.1:5642/",
    "wes:tcp": "tcp://127.0.0.1:5634/",
    "wes:http": "http://127.0.0.1:5644/",
    "wil:tcp": "tcp://127.0.0.1:5633/",
    "wil:http": "http://127.0.0.1:5643/",
}

class DbSeed:
    @staticmethod
    def seedWitEnds(db, witHabs, protocols=None):
        """ Add endpoint and location records for well known test witnesses

        Args:
            db (Baser): database to add records
            witHabs (list): list of witness Habs for whom to create Ends
            protocols (list) array of str protocol names to load URLs for.
        Returns:

        """

        rtr = routing.Router()
        rvy = routing.Revery(db=db, rtr=rtr)
        kvy = eventing.Kevery(db=db, lax=False, local=True, rvy=rvy)
        kvy.registerReplyRoutes(router=rtr)
        psr = parsing.Parser(framed=True, kvy=kvy, rvy=rvy)

        if protocols is None:
            protocols = [kering.Schemes.tcp, kering.Schemes.http]

        for scheme in protocols:
            msgs = bytearray()
            for hab in witHabs:
                url = WitnessUrls[f"{hab.name}:{scheme}"]
                msgs.extend(hab.makeEndRole(eid=hab.pre,
                                            role=kering.Roles.controller,
                                            stamp=helping.nowIso8601()))

                msgs.extend(hab.makeLocScheme(url=url,
                                              scheme=scheme,
                                              stamp=helping.nowIso8601()))
                psr.parse(ims=msgs)

    @staticmethod
    def seedSchema(db):
        # OLD: "E1MCiPag0EWlqeJGzDA9xxr1bUSUR4fZXtqHDrwdXgbk"
        sad = {'$id': '',
               '$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Legal Entity vLEI Credential',
               'description': 'A vLEI Credential issued by a Qualified vLEI issuer to a Legal Entity',
               'credentialType': 'LegalEntityvLEICredential',
               'properties': {'v': {'type': 'string'}, 'd': {'type': 'string'}, 'i': {'type': 'string'},
                              'ri': {'description': 'credential status registry', 'type': 'string'},
                              's': {'description': 'schema SAID', 'type': 'string'}, 'a': {'description': 'data block',
                                                                                           'properties': {
                                                                                               'd': {'type': 'string'},
                                                                                               'i': {'type': 'string'},
                                                                                               'dt': {
                                                                                                   'description':
                                                                                                       'issuance date '
                                                                                                       'time',
                                                                                                   'format':
                                                                                                       'date-time',
                                                                                                   'type': 'string'},
                                                                                               'LEI': {
                                                                                                   'type': 'string'}},
                                                                                           'additionalProperties':
                                                                                               False,
                                                                                           'required': ['i', 'dt',
                                                                                                        'LEI'],
                                                                                           'type': 'object'},
                              'e': {'description': 'edges block', 'type': 'object'},
                              'r': {'type': 'object', 'description': 'rules block'}}, 'additionalProperties': False,
               'required': ['i', 'ri', 's', 'd', 'e', 'r'], 'type': 'object'}

        _, sad = coring.Saider.saidify(sad, label=coring.Saids.dollar)
        schemer = scheming.Schemer(sed=sad)
        # NEW: "ENTAoj2oNBFpaniRswwPcca9W1ElEeH2V7ahw68HV4G5
        db.schema.pin(schemer.said, schemer)

        # OLD: "ExBYRwKdVGTWFq1M3IrewjKRhKusW9p9fdsdD0aSTWQI"
        sad = {'$id': '',
               '$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'GLEIF vLEI Credential',
               'description': 'The vLEI Credential issued to GLEIF', 'credentialType': 'GLEIFvLEICredential',
               'type': 'object',
               'properties': {'v': {'type': 'string'}, 'd': {'type': 'string'}, 'i': {'type': 'string'},
                              'ri': {'description': 'credential status registry', 'type': 'string'},
                              's': {'description': 'schema SAID', 'type': 'string'}, 'a': {'description': 'data block',
                                                                                           'properties': {
                                                                                               'd': {'type': 'string'},
                                                                                               'i': {'type': 'string'},
                                                                                               'dt': {
                                                                                                   'description':
                                                                                                       'issuance date '
                                                                                                       'time',
                                                                                                   'format':
                                                                                                       'date-time',
                                                                                                   'type': 'string'},
                                                                                               'LEI': {
                                                                                                   'type': 'string'}},
                                                                                           'additionalProperties':
                                                                                               False,
                                                                                           'required': ['d', 'dt',
                                                                                                        'LEI'],
                                                                                           'type': 'object'},
                              'e': {'type': 'object'}}, 'additionalProperties': False, 'required': ['d', 'i', 'ri']}
        _, sad = coring.Saider.saidify(sad, label=coring.Saids.dollar)
        schemer = scheming.Schemer(sed=sad)
        # NEW: EMQWEcCnVRk1hatTNyK3sIykYSrrFvafX3bHQ9Gkk1kC
        db.schema.pin(schemer.said, schemer)

        # OLD: EPz3ZvjQ_8ZwRKzfA5xzbMW8v8ZWLZhvOn2Kw1Nkqo_Q
        sad = {'$id': '', '$schema':
            'http://json-schema.org/draft-07/schema#', 'title': 'Legal Entity vLEI Credential',
               'description': 'A vLEI Credential issued by a Qualified vLEI issuer to a Legal Entity',
               'credentialType': 'LegalEntityvLEICredential',
               'properties': {'v': {'type': 'string'}, 'd': {'type': 'string'}, 'i': {'type': 'string'},
                              'ri': {'description': 'credential status registry', 'type': 'string'},
                              's': {'description': 'schema SAID', 'type': 'string'}, 'a': {'description': 'data block',
                                                                                           'properties': {
                                                                                               'd': {'type': 'string'},
                                                                                               'i': {'type': 'string'},
                                                                                               'dt': {
                                                                                                   'description':
                                                                                                       'issuance date '
                                                                                                       'time',
                                                                                                   'format':
                                                                                                       'date-time',
                                                                                                   'type': 'string'},
                                                                                               'LEI': {
                                                                                                   'type': 'string'}},
                                                                                           'additionalProperties':
                                                                                               False,
                                                                                           'required': ['i', 'dt',
                                                                                                        'LEI'],
                                                                                           'type': 'object'},
                              'e': {'description': 'edges block',
                                    'properties': {'d': {'description': 'SAID of edges block', 'type': 'string'},
                                                   'qualifiedvLEIIssuervLEICredential': {
                                                       'description': 'node SAID of issuer credential',
                                                       'properties': {'n': {'type': 'string'}},
                                                       'additionalProperties': False, 'required': ['n'],
                                                       'type': 'object'}}, 'additionalProperties': False,
                                    'required': ['d', 'qualifiedvLEIIssuervLEICredential'], 'type': 'object'},
                              'r': {'type': 'array', 'items': {'type': 'object'}, 'description': 'rules block',
                                    'minItems': 0}}, 'additionalProperties': False,
               'required': ['i', 'ri', 's', 'd', 'e', 'r'], 'type': 'object'}
        _, sad = coring.Saider.saidify(sad, label=coring.Saids.dollar)
        schemer = scheming.Schemer(sed=sad)
        # NEW: ED892b40P_GcESs3wOcc2zFvL_GVi2Ybzp9isNTZKqP0
        db.schema.pin(schemer.said, schemer)

        # OLD: EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao
        sad = {'$id': '',
               '$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Qualified vLEI Issuer Credential',
               'description': 'A vLEI Credential issued by GLEIF to Qualified vLEI Issuers which allows the Qualified '
                              'vLEI Issuers to issue, verify and revoke Legal Entity vLEI Credentials and Legal '
                              'Entity Official Organizational Role vLEI Credentials',
               'credentialType': 'QualifiedvLEIIssuervLEICredential',
               'properties': {'v': {'type': 'string'}, 'd': {'type': 'string'}, 'i': {'type': 'string'},
                              'ri': {'description': 'credential status registry', 'type': 'string'},
                              's': {'description': 'schema SAID', 'type': 'string'}, 'a': {'description': 'data block',
                                                                                           'properties': {
                                                                                               'd': {'type': 'string'},
                                                                                               'i': {'type': 'string'},
                                                                                               'dt': {
                                                                                                   'description':
                                                                                                       'issuance date '
                                                                                                       'time',
                                                                                                   'format':
                                                                                                       'date-time',
                                                                                                   'type': 'string'},
                                                                                               'LEI': {
                                                                                                   'type': 'string'},
                                                                                               'gracePeriod': {
                                                                                                   'default': 90,
                                                                                                   'type': 'integer'}},
                                                                                           'additionalProperties':
                                                                                               False,
                                                                                           'required': ['i', 'dt',
                                                                                                        'LEI'],
                                                                                           'type': 'object'},
                              'e': {'type': 'object'}}, 'additionalProperties': False,
               'required': ['i', 'ri', 's', 'd'], 'type': 'object'}

        _, sad = coring.Saider.saidify(sad, label=coring.Saids.dollar)
        schemer = scheming.Schemer(sed=sad)
        # NEW: EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs
        db.schema.pin(schemer.said, schemer)

class Helpers:

    controllerAID = "EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx"

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
    def controller():
        serder, signers = Helpers.incept(bran=b'0123456789abcdefghijk', stem="signify:controller", pidx=0)
        sigers = [signers[0].sign(ser=serder.raw, index=0)]
        return serder, sigers

    @staticmethod
    def incept(bran, stem, pidx, count=1, sith="1", wits=None, toad="0", delpre=None):
        if wits is None:
            wits = []

        salter = coring.Salter(raw=bran)
        creator = keeping.SaltyCreator(salt=salter.qb64, stem=stem, tier=coring.Tiers.low)

        signers = creator.create(pidx=pidx, ridx=0, tier=coring.Tiers.low, temp=False, count=count)
        nsigners = creator.create(pidx=pidx, ridx=1, tier=coring.Tiers.low, temp=False, count=count)

        keys = [signer.verfer.qb64 for signer in signers]
        ndigs = [coring.Diger(ser=nsigner.verfer.qb64b) for nsigner in nsigners]

        if delpre is not None:
            serder = eventing.delcept(delpre=delpre,
                                      keys=keys,
                                      isith=sith,
                                      nsith=sith,
                                      ndigs=[diger.qb64 for diger in ndigs],
                                      code=coring.MtrDex.Blake3_256,
                                      toad=toad,
                                      wits=wits)
        else:
            serder = eventing.incept(keys=keys,
                                     isith=sith,
                                     nsith=sith,
                                     ndigs=[diger.qb64 for diger in ndigs],
                                     code=coring.MtrDex.Blake3_256,
                                     toad=toad,
                                     wits=wits)

        return serder, signers

    @staticmethod
    def inceptRandy(bran, count=1, sith="1", wits=None, toad="0"):
        if wits is None:
            wits = []

        salter = coring.Salter(raw=bran)
        signer = salter.signer(transferable=False)
        aeid = signer.verfer.qb64
        encrypter = coring.Encrypter(verkey=aeid)

        creator = keeping.RandyCreator()
        signers = creator.create(count=count)
        prxs = [encrypter.encrypt(matter=signer).qb64 for signer in signers]
        nsigners = creator.create(count=count)
        nxts = [encrypter.encrypt(matter=signer).qb64 for signer in nsigners]

        keys = [signer.verfer.qb64 for signer in signers]
        ndigs = [coring.Diger(ser=nsigner.verfer.qb64b) for nsigner in nsigners]

        serder = eventing.incept(keys=keys,
                                 isith=sith,
                                 nsith=sith,
                                 ndigs=[diger.qb64 for diger in ndigs],
                                 code=coring.MtrDex.Blake3_256,
                                 toad=toad,
                                 wits=wits)

        return serder, signers, prxs, nxts

    @staticmethod
    def inceptExtern(count=1, sith="1", wits=None, toad="0"):
        if wits is None:
            wits = []

        creator = keeping.RandyCreator()
        signers = creator.create(count=count)
        nsigners = creator.create(count=count)

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
    def createAid(client, name, salt, wits=None, toad="0", delpre=None):
        serder, signers = Helpers.incept(salt, "signify:aid", pidx=0, wits=wits, toad=toad, delpre=delpre)
        assert len(signers) == 1

        salter = coring.Salter(raw=salt)
        encrypter = coring.Encrypter(verkey=signers[0].verfer.qb64)
        sxlt = encrypter.encrypt(salter.qb64).qb64

        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]

        body = {'name': name,
                'icp': serder.ked,
                'sigs': sigers,
                "salty": {
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low', 'sxlt': sxlt,
                    'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200 or res.status_code == 202
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
    def openKeria(salter=None, cf=None, temp=True):

        serder, sigers = Helpers.controller()
        assert serder.pre == Helpers.controllerAID

        if salter is None:
            salt = b'0123456789abcdef'
            salter = coring.Salter(raw=salt)

        if cf is None:
            cf = configing.Configer(name="keria", headDirPath="scripts", temp=True, reopen=True, clear=False)

        with habbing.openHby(name="keria", salt=salter.qb64, temp=temp, cf=cf) as hby:
            ims = eventing.messagize(serder, sigers=sigers)
            parsing.Parser(kvy=hby.kvy).parseOne(ims=ims)

            agency = agenting.Agency(name="agency", bran=None, temp=True)
            agentHab = hby.makeHab(serder.pre, ns="agent", transferable=True, delpre=serder.pre)

            rgy = credentialing.Regery(hby=hby, name=agentHab.name, base=hby.base, temp=True)
            agent = agenting.Agent(hby=hby, rgy=rgy, agentHab=agentHab, agency=agency, caid=serder.pre)
            agency.agents[serder.pre] = agent

            app = falcon.App()
            app.add_middleware(Helpers.middleware(agent))
            client = testing.TestClient(app)
            yield agency, agent, app, client
            
class MockAgentMiddleware:

    def __init__(self, agent):
        self.agent = agent

    def process_request(self, req, _):
        """ Process request to ensure has a valid signature from caid

        Parameters:
            req: Http request object
            _: placeholder for Http response object


        """
        req.context.agent = self.agent