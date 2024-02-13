# -*- coding: utf-8 -*-
"""
Helpers for tests that need KERIA
"""
import json
import os
import shutil
from contextlib import contextmanager

import falcon
from falcon import testing
from hio.core import http
from keri import kering
from keri.app import keeping, habbing, configing, signing
from keri.core import coring, eventing, parsing, routing, scheming, serdering
from keri.core.coring import MtrDex
from keri.core.eventing import SealEvent
from keri.help import helping
from keri.vc import proving
from keri.vdr import credentialing, verifying
from keri.vdr import eventing as veventing
from keri.vdr.credentialing import Regery, Registrar

from keria.app import agenting, indirecting

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
        sad = {'$id': 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
               '$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Qualified vLEI Issuer Credential',
               'description': 'A vLEI Credential issued by GLEIF to Qualified vLEI Issuers which allows the Qualified '
                              'vLEI Issuers to issue, verify and revoke Legal Entity vLEI Credentials and Legal '
                              'Entity Official Organizational Role vLEI Credentials',
               'type': 'object', 'credentialType': 'QualifiedvLEIIssuervLEICredential', 'version': '1.0.0',
               'properties': {'v': {'description': 'Version', 'type': 'string'},
                              'd': {'description': 'Credential SAID', 'type': 'string'},
                              'u': {'description': 'One time use nonce', 'type': 'string'},
                              'i': {'description': 'GLEIF Issuee AID', 'type': 'string'},
                              'ri': {'description': 'Credential status registry', 'type': 'string'},
                              's': {'description': 'Schema SAID', 'type': 'string'}, 'a': {
                       'oneOf': [{'description': 'Attributes block SAID', 'type': 'string'},
                                 {'$id': 'ELGgI0fkloqKWREXgqUfgS0bJybP1LChxCO3sqPSFHCj',
                                  'description': 'Attributes block', 'type': 'object',
                                  'properties': {'d': {'description': 'Attributes block SAID', 'type': 'string'},
                                                 'i': {'description': 'QVI Issuee AID', 'type': 'string'},
                                                 'dt': {'description': 'Issuance date time', 'type': 'string',
                                                        'format': 'date-time'},
                                                 'LEI': {'description': 'LEI of the requesting Legal Entity',
                                                         'type': 'string', 'format': 'ISO 17442'},
                                                 'gracePeriod': {'description': 'Allocated grace period',
                                                                 'type': 'integer', 'default': 90}},
                                  'additionalProperties': False, 'required': ['i', 'dt', 'LEI']}]}, 'r': {
                       'oneOf': [{'description': 'Rules block SAID', 'type': 'string'},
                                 {'$id': 'ECllqarpkZrSIWCb97XlMpEZZH3q4kc--FQ9mbkFMb_5', 'description': 'Rules block',
                                  'type': 'object',
                                  'properties': {'d': {'description': 'Rules block SAID', 'type': 'string'},
                                                 'usageDisclaimer': {'description': 'Usage Disclaimer',
                                                                     'type': 'object', 'properties': {
                                                         'l': {'description': 'Associated legal language',
                                                               'type': 'string',
                                                               'const': 'Usage of a valid, unexpired, and non-revoked '
                                                                        'vLEI Credential, as defined in the '
                                                                        'associated Ecosystem Governance Framework, '
                                                                        'does not assert that the Legal Entity is '
                                                                        'trustworthy, honest, reputable in its '
                                                                        'business dealings, safe to do business with, '
                                                                        'or compliant with any laws or that an '
                                                                        'implied or expressly intended purpose will '
                                                                        'be fulfilled.'}}},
                                                 'issuanceDisclaimer': {'description': 'Issuance Disclaimer',
                                                                        'type': 'object', 'properties': {
                                                         'l': {'description': 'Associated legal language',
                                                               'type': 'string',
                                                               'const': 'All information in a valid, unexpired, '
                                                                        'and non-revoked vLEI Credential, as defined '
                                                                        'in the associated Ecosystem Governance '
                                                                        'Framework, is accurate as of the date the '
                                                                        'validation process was complete. The vLEI '
                                                                        'Credential has been issued to the legal '
                                                                        'entity or person named in the vLEI '
                                                                        'Credential as the subject; and the qualified '
                                                                        'vLEI Issuer exercised reasonable care to '
                                                                        'perform the validation process set forth in '
                                                                        'the vLEI Ecosystem Governance Framework.'}}}},
                                  'additionalProperties': False,
                                  'required': ['d', 'usageDisclaimer', 'issuanceDisclaimer']}]}},
               'additionalProperties': False, 'required': ['i', 'ri', 's', 'd']}
        _, sad = coring.Saider.saidify(sad, label=coring.Saids.dollar)
        schemer = scheming.Schemer(sed=sad)
        # NEW: "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
        db.schema.pin(schemer.said, schemer)

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
    def remove_test_dirs(name, kdir="/usr/local/var/keri"):
        # if os.path.exists(f'{kdir}/adb/TheAgency'):
        #     shutil.rmtree(f'{kdir}/adb/TheAgency')
        if os.path.exists(f'{kdir}/cf/{name}.json'):
            os.remove(f'{kdir}/cf/{name}.json')
        if os.path.exists(f'{kdir}/cf/{name}'):
            shutil.rmtree(f'{kdir}/cf/{name}')
        if os.path.exists(f'{kdir}/db/{name}'):
            shutil.rmtree(f'{kdir}/db/{name}')
        if os.path.exists(f'{kdir}/ks/{name}'):
            shutil.rmtree(f'{kdir}/ks/{name}')
        if os.path.exists(f'{kdir}/mbx/{name}'):
            shutil.rmtree(f'{kdir}/mbx/{name}')
        if os.path.exists(f'{kdir}/not/{name}'):
            shutil.rmtree(f'{kdir}/not/{name}')
        if os.path.exists(f'{kdir}/opr/{name}'):
            shutil.rmtree(f'{kdir}/opr/{name}')
        if os.path.exists(f'{kdir}/reg/{name}'):
            shutil.rmtree(f'{kdir}/reg/{name}')
        if os.path.exists(f'{kdir}/reg/agent-{name}'):
            shutil.rmtree(f'{kdir}/reg/agent-{name}')
        if os.path.exists(f'{kdir}/rks/{name}'):
            shutil.rmtree(f'{kdir}/rks/{name}')

    @staticmethod
    def server(agency, httpPort=3902):
        app = falcon.App()
        httpEnd = indirecting.HttpEnd(agency=agency)
        app.add_route("/", httpEnd)
        server = http.Server(port=httpPort, app=app)
        httpServerDoer = http.ServerDoer(server=server)
        return httpServerDoer

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
    def interact(pre, bran, pidx, ridx, sn, dig, data):
        serder = eventing.interact(pre=pre, dig=dig, sn=sn, data=data)
        salter = coring.Salter(raw=bran)
        creator = keeping.SaltyCreator(salt=salter.qb64, stem="signify:aid", tier=coring.Tiers.low)

        signers = creator.create(pidx=pidx, ridx=ridx, tier=coring.Tiers.low, temp=False, count=1)
        sigers = [signer.sign(ser=serder.raw, index=0).qb64 for signer in signers]
        return serder, sigers

    @staticmethod
    def sign(bran, pidx, ridx, ser):
        salter = coring.Salter(raw=bran)
        creator = keeping.SaltyCreator(salt=salter.qb64, stem="signify:aid", tier=coring.Tiers.low)

        signers = creator.create(pidx=pidx, ridx=ridx, tier=coring.Tiers.low, temp=False, count=1)
        sigers = [signer.sign(ser=ser, index=0).qb64 for signer in signers]
        return sigers

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
                    'stem': 'signify:aid', 'pidx': 0, 'tier': 'low', 'sxlt': sxlt, 'transferable': True, 'kidx': 0,
                    'icodes': [MtrDex.Ed25519_Seed], 'ncodes': [MtrDex.Ed25519_Seed]}
                }

        res = client.simulate_post(path="/identifiers", body=json.dumps(body))
        assert res.status_code == 200 or res.status_code == 202
        return res.json

    @staticmethod
    def createEndRole(client, agent, recp, name, salt):
        rpy = Helpers.endrole(recp, agent.agentHab.pre)
        sigs = Helpers.sign(salt, 0, 0, rpy.raw)
        body = dict(rpy=rpy.ked, sigs=sigs)

        res = client.simulate_post(path=f"/identifiers/{name}/endroles", json=body)
        op = res.json
        ked = op["response"]
        serder = serdering.SerderKERI(sad=ked)
        assert serder.raw == rpy.raw

    @staticmethod
    def createRegistry(client, agent, salt, doist, deeds):
        op = Helpers.createAid(client, "issuer", salt)
        aid = op["response"]
        pre = aid['i']
        assert pre == "EHgwVwQT15OJvilVvW57HE4w0-GPs_Stj2OFoAHZSysY"

        nonce = coring.randomNonce()
        regser = veventing.incept(pre,
                                  baks=[],
                                  toad="0",
                                  nonce=nonce,
                                  cnfg=[eventing.TraitCodex.NoBackers],
                                  code=coring.MtrDex.Blake3_256)
        anchor = dict(i=regser.ked['i'], s=regser.ked["s"], d=regser.said)
        serder, sigers = Helpers.interact(pre=pre, bran=salt, pidx=0, ridx=0, dig=aid['d'], sn='1', data=[anchor])
        body = dict(name="test", alias="test", vcp=regser.ked, ixn=serder.ked, sigs=sigers)
        result = client.simulate_post(path="/identifiers/issuer/registries", body=json.dumps(body).encode("utf-8"))
        op = result.json
        metadata = op["metadata"]

        assert op["done"] is True
        assert metadata["anchor"] == anchor
        assert result.status == falcon.HTTP_202

        while regser.pre not in agent.tvy.tevers:
            doist.recur(deeds=deeds)

        assert regser.pre in agent.tvy.tevers

        result = client.simulate_get(path="/identifiers/issuer/registries")
        registries = result.json
        assert len(registries) == 1
        assert registries[0]["name"] == "test"

        issuer = client.simulate_get("/identifiers/issuer")

        return registries[0], issuer.json

    @staticmethod
    def endrole(cid, eid, role="agent"):
        data = dict(cid=cid, role=role, eid=eid)
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
            cf = configing.Configer(name="keria", headDirPath="tests/scripts", reopen=True, clear=False)

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

    @staticmethod
    @contextmanager
    def withIssuer(name, hby):
        yield Issuer(name=name, hby=hby)

    @staticmethod
    def mockNowUTC():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return helping.fromIso8601("2021-01-01T00:00:00.000000+00:00")

    @staticmethod
    def mockNowIso8601():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return "2021-06-27T21:26:21.233257+00:00"

    @staticmethod
    def mockRandomNonce():
        return "A9XfpxIl1LcIkMhUSCCC8fgvkuX8gG9xK3SM-S8a8Y_U"
    

class Issuer:
    LE = "ENTAoj2oNBFpaniRswwPcca9W1ElEeH2V7ahw68HV4G5"
    QVI = "EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs"
    date = "2021-06-27T21:26:21.233257+00:00"

    def __init__(self, name, hby):
        self.hby = hby
        self.rgy = Regery(hby=hby, name=name, temp=True)
        self.registrar = Registrar(hby=hby, rgy=self.rgy, counselor=None)
        self.verifier = verifying.Verifier(hby=hby, reger=self.rgy.reger)

    def createRegistry(self, pre, name):
        conf = dict(nonce='AGu8jwfkyvVXQ2nqEb5yVigEtR31KSytcpe2U2f7NArr')
        hab = self.hby.habs[pre]

        registry = self.rgy.makeRegistry(name=name, prefix=pre, **conf)
        assert registry.regk == "EACehJRd0wfteUAJgaTTJjMSaQqWvzeeHqAMMqxuqxU4"

        rseal = SealEvent(registry.regk, "0", registry.regd)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)
        anc = hab.interact(data=[rseal])

        aserder = serdering.SerderKERI(raw=bytes(anc))
        self.registrar.incept(iserder=registry.vcp, anc=aserder)

        # Process escrows to clear event
        self.rgy.processEscrows()
        self.registrar.processEscrows()

        assert self.rgy.reger.ctel.get(keys=(registry.regk, coring.Seqner(sn=0).qb64)) is not None

    def issueLegalEntityvLEI(self, reg, issuer, issuee, LEI):
        registry = self.rgy.registryByName(reg)
        credSubject = dict(
            d="",
            i=issuee,
            dt=self.date,
            LEI=LEI,
        )

        # Create the Creder and issue the credentials
        creder = proving.credential(issuer=issuer.pre,
                                    schema=self.LE,
                                    data=credSubject,
                                    status=registry.regk,
                                    source={}, rules={})

        iserder = registry.issue(said=creder.said, dt=self.date)

        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        anc = issuer.interact(data=[rseal])
        aserder = serdering.SerderKERI(raw=anc)
        self.registrar.issue(creder=creder, iserder=iserder, anc=aserder)

        prefixer = coring.Prefixer(qb64=iserder.pre)
        seqner = coring.Seqner(sn=iserder.sn)
        saider = coring.Saider(qb64=iserder.said)
        craw = signing.serialize(creder, prefixer, seqner, saider)

        # Process escrows to clear event
        self.rgy.processEscrows()
        self.registrar.processEscrows()

        parsing.Parser().parse(ims=craw, vry=self.verifier)

        assert self.rgy.reger.saved.get(keys=creder.said) is not None

        return creder.said

    def issueQVIvLEI(self, reg, issuer, issuee, LEI):
        registry = self.rgy.registryByName(reg)
        credSubject = dict(
            d="",
            i=issuee,
            dt=self.date,
            LEI=LEI,
        )

        # Create the Creder and issue the credentials
        creder = proving.credential(issuer=issuer.pre,
                                    schema=self.QVI,
                                    data=credSubject,
                                    status=registry.regk)

        iserder = registry.issue(said=creder.said, dt=self.date)

        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        anc = issuer.interact(data=[rseal])
        aserder = serdering.SerderKERI(raw=anc)
        self.registrar.issue(creder=creder, iserder=iserder, anc=aserder)

        prefixer = coring.Prefixer(qb64=iserder.pre)
        seqner = coring.Seqner(sn=iserder.sn)
        saider = coring.Saider(qb64=iserder.said)
        craw = signing.serialize(creder, prefixer, seqner, saider)

        # Process escrows to clear event
        self.rgy.processEscrows()
        self.registrar.processEscrows()

        parsing.Parser().parse(ims=craw, vry=self.verifier)

        assert self.rgy.reger.saved.get(keys=creder.said) is not None

        return creder.said


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
