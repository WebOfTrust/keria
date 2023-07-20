# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
import json
import os
from dataclasses import asdict
from urllib import parse
from urllib.parse import urlparse

from keri import kering
from keri.app.notifying import Notifier
from keri.app.storing import Mailboxer
from ordered_set import OrderedSet as oset

import falcon
from falcon import media
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri.app import configing, keeping, habbing, storing, signaling, oobiing, agenting, delegating, \
    forwarding, querying, connecting
from keri.app.grouping import Counselor
from keri.app.keeping import Algos
from keri.core import coring, parsing, eventing, routing
from keri.core.coring import Ilks, randomNonce
from keri.db import dbing
from keri.db.basing import OobiRecord
from keria.end import ending
from keri.help import helping, ogler
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying
from keri.vdr.credentialing import Regery
from keri.vdr.eventing import Tevery
from keri.app import challenging

from . import aiding, notifying, indirecting, credentialing, presenting
from .specing import AgentSpecResource
from ..core import authing, longrunning, httping
from ..core.authing import Authenticater
from ..core.keeping import RemoteManager
from ..db import basing

logger = ogler.getLogger()


def setup(name, bran, adminPort, bootPort, base='', httpPort=None, configFile=None, configDir=None,
          interceptor_webhook=None, interceptor_headers=None):
    """ Set up an ahab in Signify mode """

    agency = Agency(name=name, base=base, bran=bran, configFile=configFile, configDir=configDir,
                    interceptor_webhook=interceptor_webhook, interceptor_headers=interceptor_headers)
    bootApp = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                        'signify-resource', 'signify-timestamp']))
    bootServer = http.Server(port=bootPort, app=bootApp)
    bootServerDoer = http.ServerDoer(server=bootServer)
    bootEnd = BootEnd(agency)
    bootApp.add_route("/boot", bootEnd)

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agency=agency)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                        'signify-resource', 'signify-timestamp']))
    if os.getenv("KERI_AGENT_CORS", "false").lower() in ("true", "1"):
        app.add_middleware(middleware=httping.HandleCORS())
    app.add_middleware(authing.SignatureValidationComponent(agency=agency, authn=authn, allowed=["/agent"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    adminServer = http.Server(port=adminPort, app=app)
    adminServerDoer = http.ServerDoer(server=adminServer)

    doers = [agency, bootServerDoer, adminServerDoer]
    loadEnds(app=app)
    aidEnd = aiding.loadEnds(app=app, agency=agency, authn=authn)
    credentialing.loadEnds(app=app, identifierResource=aidEnd)
    presenting.loadEnds(app=app)
    notifying.loadEnds(app=app)

    if httpPort:
        happ = falcon.App(middleware=falcon.CORSMiddleware(
            allow_origins='*', allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                            'signify-resource', 'signify-timestamp']))
        happ.req_options.media_handlers.update(media.Handlers())
        happ.resp_options.media_handlers.update(media.Handlers())

        ending.loadEnds(agency=agency, app=happ)
        indirecting.loadEnds(agency=agency, app=happ)

        server = http.Server(port=httpPort, app=happ)
        httpServerDoer = http.ServerDoer(server=server)
        doers.append(httpServerDoer)

        swagsink = http.serving.StaticSink(staticDirPath="./static")
        happ.add_sink(swagsink, prefix="/swaggerui")

        specEnd = AgentSpecResource(app=app, title='KERIA Interactive Web Interface API')
        specEnd.addRoutes(happ)
        happ.add_route("/spec.yaml", specEnd)

    print("The Agency is loaded and waiting for requests...")
    return doers


class Agency(doing.DoDoer):
    def __init__(self, name, bran, base="", configFile=None, configDir=None, adb=None, temp=False,
                 interceptor_webhook=None, interceptor_headers=None):
        self.name = name
        self.base = base
        self.bran = bran
        self.temp = temp
        self.configFile = configFile
        self.configDir = configDir
        self.cf = None
        self.intercepts = decking.Deck()
        doers = []
        self.interceptor = None
        if interceptor_webhook is not None:
            self.interceptor = InterceptorDoer(interceptor_webhook, interceptor_headers, cues=self.intercepts)
            doers.append(self.interceptor)

        if self.configFile is not None:  # Load config file if creating database
            self.cf = configing.Configer(name=self.configFile,
                                         base="",
                                         headDirPath=self.configDir,
                                         temp=False,
                                         reopen=True,
                                         clear=False)

        self.agents = dict()

        self.adb = adb if adb is not None else basing.AgencyBaser(name="TheAgency", base=base, reopen=True, temp=temp)
        super(Agency, self).__init__(doers=doers, always=True)

    def create(self, caid):
        ks = keeping.Keeper(name=caid,
                            base=self.base,
                            temp=self.temp,
                            reopen=True)

        cf = None
        if self.cf is not None:  # Load config file if creating database
            data = dict(self.cf.get())
            if "keria" in data:
                curls = data["keria"]
                data[f"agent-{caid}"] = curls
                del data["keria"]

            cf = configing.Configer(name=f"{caid}",
                                    base="",
                                    human=False,
                                    temp=self.temp,
                                    reopen=True,
                                    clear=False)
            cf.put(data)

        # Create the Hab for the Agent with only 2 AIDs
        agentHby = habbing.Habery(name=caid, base=self.base, bran=self.bran, ks=ks, cf=cf, temp=self.temp)
        agentHab = agentHby.makeHab(f"agent-{caid}", ns="agent", transferable=True, delpre=caid)
        agentRgy = Regery(hby=agentHby, name=agentHab.name, base=self.base, temp=self.temp)

        agent = Agent(agentHby, agentRgy, agentHab,
                      caid=caid,
                      agency=self,
                      configDir=self.configDir,
                      configFile=self.configFile)

        self.adb.agnt.pin(keys=(caid,),
                          val=coring.Prefixer(qb64=agent.pre))
        self.adb.ctrl.pin(keys=(agent.pre,),
                          val=coring.Prefixer(qb64=caid))

        # add agent to cache
        self.agents[caid] = agent
        # start agents processes running
        self.extend([agent])

        return agent

    def delete(self, agent):
        self.adb.agnt.rem(key=agent.caid)
        agent.hby.deleteHab(agent.caid)
        agent.hby.ks.close(clear=True)
        agent.hby.close(clear=True)

        del self.agents[agent.caid]

    def get(self, caid):
        if caid in self.agents:
            return self.agents[caid]

        aaid = self.adb.agnt.get(keys=(caid,))
        if aaid is None:
            return None

        ks = keeping.Keeper(name=caid,
                            base=self.base,
                            temp=self.temp,
                            reopen=True)

        agentHby = habbing.Habery(name=caid, base=self.base, bran=self.bran, ks=ks, temp=self.temp)

        agentHab = agentHby.habByName(f"agent-{caid}", ns="agent")
        if aaid.qb64 != agentHab.pre:
            raise kering.ConfigurationError(f"invalid agent aid={aaid.qb64}/{agentHab.pre} to controller aid={caid}")

        agentRgy = Regery(hby=agentHby, name=agentHab.name, base=self.base, temp=self.temp)
        agent = Agent(hby=agentHby, rgy=agentRgy, agentHab=agentHab, agency=self, caid=caid)
        self.agents[caid] = agent

        return agent

    def lookup(self, pre):
        # Check to see if this is a managed AID
        if (prefixer := self.adb.aids.get(keys=(pre,))) is not None:
            caid = prefixer.qb64
        # Or if its an agent AID
        elif (prefixer := self.adb.ctrl.get(keys=(pre,))) is not None:
            caid = prefixer.qb64
        else:
            return None

        try:
            return self.get(caid)
        except kering.ConfigurationError:
            return None

    def incept(self, caid, pre):
        self.adb.aids.pin(keys=(pre,), val=coring.Prefixer(qb64=caid))


class Agent(doing.DoDoer):
    """ 
    
    The top level object and DoDoer representing a Habery for a remote controller and all associated processing

    """

    def __init__(self, hby, rgy, agentHab, agency, caid, **opts):
        self.hby = hby
        self.rgy = rgy
        self.agentHab = agentHab
        self.agency = agency
        self.caid = caid

        self.swain = delegating.Boatswain(hby=hby, proxy=agentHab)
        self.counselor = Counselor(hby=hby, swain=self.swain)
        self.org = connecting.Organizer(hby=hby)

        oobiery = oobiing.Oobiery(hby=hby)

        self.mgr = RemoteManager(hby=hby)

        self.cues = decking.Deck()
        self.groups = decking.Deck()
        self.anchors = decking.Deck()
        self.witners = decking.Deck()
        self.queries = decking.Deck()
        self.agency.intercepts

        receiptor = agenting.Receiptor(hby=hby)
        self.postman = forwarding.Poster(hby=hby)
        self.witPub = agenting.WitnessPublisher(hby=self.hby)
        self.witDoer = agenting.WitnessReceiptor(hby=self.hby)

        self.rep = storing.Respondant(hby=hby, cues=self.cues, mbx=Mailboxer(name=self.hby.name, temp=self.hby.temp))

        doers = [habbing.HaberyDoer(habery=hby), receiptor, self.postman, self.witPub, self.rep, self.swain,
                 self.counselor, self.witDoer, *oobiery.doers]

        signaler = signaling.Signaler()
        self.notifier = Notifier(hby=hby, signaler=signaler)

        # Initialize all the credential processors
        self.verifier = verifying.Verifier(hby=hby, reger=rgy.reger)
        self.registrar = credentialing.Registrar(agentHab=agentHab, hby=hby, rgy=rgy, counselor=self.counselor, witPub=self.witPub,
                                                 witDoer=self.witDoer, postman=self.postman, verifier=self.verifier)
        self.credentialer = credentialing.Credentialer(agentHab=agentHab, hby=self.hby, rgy=self.rgy,
                                                       postman=self.postman, registrar=self.registrar,
                                                       verifier=self.verifier, notifier=self.notifier)

        self.monitor = longrunning.Monitor(hby=hby, swain=self.swain, counselor=self.counselor, temp=hby.temp,
                                           registrar=self.registrar, credentialer=self.credentialer)
        self.seeker = basing.Seeker(name=hby.name, db=hby.db, reger=self.rgy.reger, reopen=True, temp=self.hby.temp)

        issueHandler = protocoling.IssueHandler(hby=hby, rgy=rgy, notifier=self.notifier)
        requestHandler = protocoling.PresentationRequestHandler(hby=hby, notifier=self.notifier)
        applyHandler = protocoling.ApplyHandler(hby=hby, rgy=rgy, verifier=self.verifier,
                                                name=agentHab.name)
        proofHandler = protocoling.PresentationProofHandler(notifier=self.notifier)

        challengeHandler = challenging.ChallengeHandler(db=hby.db, signaler=signaler)

        handlers = [issueHandler, requestHandler, proofHandler, applyHandler, challengeHandler]
        self.exc = exchanging.Exchanger(db=hby.db, handlers=handlers)

        self.rvy = routing.Revery(db=hby.db, cues=self.cues)
        self.kvy = eventing.Kevery(db=hby.db,
                                   lax=True,
                                   local=False,
                                   rvy=self.rvy,
                                   cues=self.cues)
        self.kvy.registerReplyRoutes(router=self.rvy.rtr)

        self.tvy = Tevery(reger=self.verifier.reger,
                          db=hby.db,
                          local=False,
                          cues=self.cues)

        self.tvy.registerReplyRoutes(router=self.rvy.rtr)
        self.parser = parsing.Parser(framed=True,
                                     kvy=self.kvy,
                                     tvy=self.tvy,
                                     exc=self.exc,
                                     rvy=self.rvy,
                                     vry=self.verifier)

        doers.extend([
            Initer(agentHab=agentHab, caid=caid, intercepts=self.agency.intercepts),
            Querier(hby=hby, agentHab=agentHab, kvy=self.kvy, queries=self.queries),
            Escrower(kvy=self.kvy, rgy=self.rgy, rvy=self.rvy, tvy=self.tvy, exc=self.exc, vry=self.verifier,
                     registrar=self.registrar, credentialer=self.credentialer),
            Messager(kvy=self.kvy, parser=self.parser),
            Witnesser(receiptor=receiptor, witners=self.witners, intercepts=self.agency.intercepts),
            Delegator(agentHab=agentHab, swain=self.swain, anchors=self.anchors, intercepts=self.agency.intercepts),
            GroupRequester(hby=hby, agentHab=agentHab, postman=self.postman, counselor=self.counselor,
                           groups=self.groups, intercepts=self.agency.intercepts),
            SeekerDoer(seeker=self.seeker, cues=self.verifier.cues)
        ])
        if self.agency.interceptor is not None:
            doers.append(self.agency.interceptor) 
        super(Agent, self).__init__(doers=doers, always=True, **opts)

    @property
    def pre(self):
        return self.agentHab.pre

    def inceptSalty(self, pre, **kwargs):
        keeper = self.mgr.get(Algos.salty)
        keeper.incept(pre=pre, **kwargs)

        self.agency.incept(self.caid, pre)

    def inceptRandy(self, pre, verfers, digers, **kwargs):
        keeper = self.mgr.get(Algos.randy)
        keeper.incept(pre=pre, verfers=verfers, digers=digers, **kwargs)

        self.agency.incept(self.caid, pre)

    def inceptGroup(self, pre, mpre, verfers, digers):
        keeper = self.mgr.get(Algos.group)
        keeper.incept(pre=pre, mpre=mpre, verfers=verfers, digers=digers)

        self.agency.incept(self.caid, pre)

    def inceptExtern(self, pre, verfers, digers, **kwargs):
        keeper = self.mgr.get(Algos.extern)
        keeper.incept(pre=pre, verfers=verfers, digers=digers, **kwargs)

        self.agency.incept(self.caid, pre)


class InterceptorDoer(doing.DoDoer):

    def __init__(self, webhook, headers, cues=None):
        self.webhook = webhook
        self.headers = headers
        self.cues = cues if cues is not None else decking.Deck()
        self.purl = parse.urlparse(webhook)
        self.client = http.clienting.Client(scheme=self.purl.scheme,
                                            hostname=self.purl.hostname,
                                            port=self.purl.port,
                                            portOptional=True)
        clientDoer = http.clienting.ClientDoer(client=self.client)

        super(InterceptorDoer, self).__init__(doers=[clientDoer], always=True)

    def recur(self, tyme, deeds=None):
        if self.cues:
            msg = self.cues.popleft()
            body = json.dumps(msg).encode("utf-8")
            # TODO: Sent the message somewhere
            self.client.request(
                method="POST",
                path=f"{self.purl.path}?{self.purl.query}",
                qargs=None,
                headers=self.headers,
                body=body
            )

        return super(InterceptorDoer, self).recur(tyme, deeds)


class Messager(doing.Doer):

    def __init__(self, kvy, parser):
        self.kvy = kvy
        self.parser = parser
        super(Messager, self).__init__()

    def recur(self, tyme=None):
        if self.parser.ims:
            logger.info("Agent %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator()  # process messages continuously
        return done  # should never get here except forced close


class Witnesser(doing.Doer):

    def __init__(self, receiptor, witners, intercepts=None):
        self.receiptor = receiptor
        self.witners = witners
        self.intercepts = intercepts
        super(Witnesser, self).__init__()

    def recur(self, tyme=None):
        while True:
            if self.witners:
                msg = self.witners.popleft()
                serder = msg["serder"]
                if self.intercepts is not None:
                    self.intercepts.append(dict(evt="witnessed", ked=serder.ked))
                # If we are a rotation event, may need to catch new witnesses up to current key state
                if serder.ked['t'] in (Ilks.rot, Ilks.drt):
                    adds = serder.ked["ba"]
                    for wit in adds:
                        yield from self.receiptor.catchup(serder.pre, wit)

                yield from self.receiptor.receipt(serder.pre, serder.sn)
                if self.intercepts is not None:
                    self.intercepts.append(dict(evt="witnessing", data=dict(aid=serder.pre)))

            yield self.tock


class Delegator(doing.Doer):

    def __init__(self, agentHab, swain, anchors, intercepts=None):
        self.agentHab = agentHab
        self.swain = swain
        self.anchors = anchors
        self.intercepts = intercepts
        super(Delegator, self).__init__()

    def recur(self, tyme=None):
        if self.anchors:
            msg = self.anchors.popleft()
            sn = msg["sn"] if "sn" in msg else None
            self.swain.delegation(pre=msg["pre"], sn=sn, proxy=self.agentHab)
            if self.intercepts is not None:
                self.intercepts.append(dict(msg))

        return False


class SeekerDoer(doing.Doer):

    def __init__(self, seeker, cues):
        self.seeker = seeker
        self.cues = cues

        super(SeekerDoer, self).__init__()

    def recur(self, tyme=None):
        if self.cues:
            cue = self.cues.popleft()
            if cue["kin"] == "saved":
                creder = cue["creder"]
                print(f"indexing {creder.said}")
                self.seeker.index(said=creder.said)


class Initer(doing.Doer):
    def __init__(self, agentHab, caid, intercepts):
        self.agentHab = agentHab
        self.caid = caid
        self.intercepts = intercepts
        super(Initer, self).__init__()

    def recur(self, tyme):
        """ Prints Agent name and prefix """
        if not self.agentHab.inited:
            return False
        self.intercepts.append(dict(evt="init", data=dict(aid=self.agentHab.pre)))
        print("  Agent:", self.agentHab.pre, "  Controller:", self.caid)

        return True


class GroupRequester(doing.Doer):

    def __init__(self, hby, agentHab, postman, counselor, groups, intercepts):
        self.hby = hby
        self.agentHab = agentHab
        self.postman = postman
        self.counselor = counselor
        self.groups = groups
        self.intercepts = intercepts

        super(GroupRequester, self).__init__()

    def recur(self, tyme):
        """ Checks cue for group proceccing requests and processes any with Counselor """
        if self.groups:
            msg = self.groups.popleft()
            serder = msg["serder"]
            sigers = msg["sigers"]
            self.intercepts.append(dict(evt="group", data=dict(msg)))
            ghab = self.hby.habs[serder.pre]
            if "smids" in msg:
                smids = msg['smids']
            else:
                smids = ghab.db.signingMembers(pre=ghab.pre)

            if "rmids" in msg:
                rmids = msg['rmids']
            else:
                rmids = ghab.db.rotationMembers(pre=ghab.pre)

            atc = bytearray()  # attachment
            atc.extend(coring.Counter(code=coring.CtrDex.ControllerIdxSigs, count=len(sigers)).qb64b)
            for siger in sigers:
                atc.extend(siger.qb64b)

            others = list(oset(smids + (rmids or [])))
            others.remove(ghab.mhab.pre)  # don't send to self
            print(f"Sending multisig event to {len(others)} other participants")
            for recpt in others:
                self.postman.send(hab=self.agentHab, dest=recpt, topic="multisig", serder=serder,
                                  attachment=atc)

            prefixer = coring.Prefixer(qb64=serder.pre)
            seqner = coring.Seqner(sn=serder.sn)
            saider = coring.Saider(qb64=serder.said)
            self.counselor.start(ghab=ghab, prefixer=prefixer, seqner=seqner, saider=saider)

        return False


class Querier(doing.DoDoer):

    def __init__(self, hby, agentHab, queries, kvy):
        self.hby = hby
        self.agentHab = agentHab
        self.queries = queries
        self.kvy = kvy

        super(Querier, self).__init__()

    def recur(self, tyme, deeds=None):
        """ Processes query reqests submitting any on the cue"""
        if self.queries:
            msg = self.queries.popleft()
            pre = msg["pre"]

            qryDo = querying.QueryDoer(hby=self.hby, hab=self.agentHab, pre=pre, kvy=self.kvy)
            self.extend([qryDo])

        return super(Querier, self).recur(tyme, deeds)


class Escrower(doing.Doer):
    def __init__(self, kvy, rgy, rvy, tvy, exc, vry, registrar, credentialer):
        """ Recuring process or escrows for all components in an Agent

        Parameters:
            kvy (Kevery):
            rgy (Regery):
            rvy (Revery):
            tvy (Tevery):
            exc (Exchanger):
            vry (Verifier):
            registrar (Registrar): Credential TEL escrow processor
            credentialer (Credentialer): Credential escrow processor
        """
        self.kvy = kvy
        self.rgy = rgy
        self.rvy = rvy
        self.tvy = tvy
        self.exc = exc
        self.vry = vry
        self.registrar = registrar
        self.credentialer = credentialer

        super(Escrower, self).__init__()

    def recur(self, tyme):
        """ Process all escrows once per loop. """
        self.kvy.processEscrows()
        self.rgy.processEscrows()
        self.rvy.processEscrowReply()
        if self.tvy is not None:
            self.tvy.processEscrows()
        self.exc.processEscrow()
        self.vry.processEscrows()
        self.registrar.processEscrows()
        self.credentialer.processEscrows()

        return False


def loadEnds(app):
    opEnd = longrunning.OperationResourceEnd()
    app.add_route("/operations/{name}", opEnd)

    oobiColEnd = OOBICollectionEnd()
    app.add_route("/oobis", oobiColEnd)
    oobiResEnd = OobiResourceEnd()
    app.add_route("/oobis/{alias}", oobiResEnd)

    statesEnd = KeyStateCollectionEnd()
    app.add_route("/states", statesEnd)

    eventsEnd = KeyEventCollectionEnd()
    app.add_route("/events", eventsEnd)

    queryEnd = QueryCollectionEnd()
    app.add_route("/queries", queryEnd)


class BootEnd:
    """ Resource class for creating datastore in cloud ahab """

    def __init__(self, agency):
        """ Provides endpoints for initializing and unlocking an agent

        Parameters:
            agency (Agency): Agency for managing agents

        """
        self.authn = authing.Authenticater(agency=agency)
        self.agency = agency

    def on_post(self, req, rep):
        """ Inception event POST endpoint

        Give me a new Agent.  Create Habery using ctrlPRE as database name, agentHab that anchors the caid and
        returns the KEL of agentHAB Stores ControllerPRE -> AgentPRE in database

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """

        body = req.get_media()
        if "icp" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "icp" missing from body')
        icp = eventing.Serder(ked=body["icp"])

        if "sig" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "sig" missing from body')
        siger = coring.Siger(qb64=body["sig"])

        caid = icp.pre

        if caid in self.agency.agents:
            raise falcon.HTTPBadRequest(title="agent already exists",
                                        description=f"agent for controller {caid} already exists")

        agent = self.agency.create(caid=caid)

        try:
            ctrlHab = agent.hby.makeSignifyHab(name=agent.caid, ns="agent", serder=icp, sigers=[siger])
        except Exception:
            self.agency.delete(agent)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid icp event for caid {agent.caid}')

        if ctrlHab.pre != agent.caid:
            self.agency.delete(agent)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid icp event for caid {agent.caid}')

        # Client is requesting that the Agent track the Salty parameters
        if Algos.salty in body:
            salt = body[Algos.salty]
            stem = httping.getRequiredParam(salt, "stem")
            pidx = httping.getRequiredParam(salt, "pidx")
            tier = httping.getRequiredParam(salt, "tier")
            sxlt = httping.getRequiredParam(salt, "sxlt")
            icodes = httping.getRequiredParam(salt, "icodes")
            ncodes = httping.getRequiredParam(salt, "ncodes")

            mgr = agent.mgr.get(algo=Algos.salty)
            mgr.incept(agent.caid, icodes=icodes, ncodes=ncodes, sxlt=sxlt, pidx=pidx, kidx=0, stem=stem, tier=tier,
                       transferable=True)

        elif Algos.randy in body:
            rand = body[Algos.randy]
            if "pris" not in rand:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "pris" missing from body.rand')
            pris = rand["pris"]

            if "nxts" not in rand:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "nxts" missing from body.rand')
            nxts = rand["nxts"]

            mgr = agent.mgr.get(algo=Algos.randy)
            mgr.incept(agent.caid, verfers=ctrlHab.kever.verfers,
                       digers=ctrlHab.kever.digers,
                       prxs=pris, nxts=nxts)

        elif Algos.group in body:
            raise falcon.HTTPBadRequest(description="multisig groups not supported as agent controller")

        rep.status = falcon.HTTP_202


class KeyStateCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary:  Display key event log (KEL) for given identifier prefix
        description:  If provided qb64 identifier prefix is in Kevers, return the current state of the
                      identifier along with the KEL and all associated signatures and receipts
        tags:
           - Key Event Log
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of KEL to load
        responses:
           200:
              description: Key event log and key state of identifier
           404:
              description: Identifier not found in Key event database


        """
        agent = req.context.agent
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest(description="required parameter 'pre' missing")

        pres = req.params.get("pre")
        pres = pres if isinstance(pres, list) else [pres]

        states = []
        for pre in pres:
            if pre not in agent.hby.kevers:
                continue

            kever = agent.hby.kevers[pre]
            states.append(asdict(kever.state()))

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(states).encode("utf-8")


class KeyEventCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary:  Display key event log (KEL) for given identifier prefix
        description:  If provided qb64 identifier prefix is in Kevers, return the current state of the
                      identifier along with the KEL and all associated signatures and receipts
        tags:
           - Key Event Log
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of KEL to load
        responses:
           200:
              description: Key event log and key state of identifier
           404:
              description: Identifier not found in Key event database


        """
        agent = req.context.agent
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest(description="required parameter 'pre' missing")

        pre = req.params.get("pre")
        preb = pre.encode("utf-8")
        events = []
        for fn, dig in agent.hby.db.getFelItemPreIter(preb, fn=0):
            dgkey = dbing.dgKey(preb, dig)  # get message
            if not (raw := agent.hby.db.getEvt(key=dgkey)):
                raise falcon.HTTPInternalServerError(f"Missing event for dig={dig}.")

            serder = coring.Serder(raw=bytes(raw))
            events.append(serder.ked)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(events).encode("utf-8")


class OOBICollectionEnd:

    def __init__(self):
        """ Create OOBI Collection endpoint instance
        """

    @staticmethod
    def on_post(req, rep):
        """ Resolve OOBI endpoint.

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Resolve OOBI and assign an alias for the remote identifier
        description: Resolve OOBI URL or `rpy` message by process results of request and assign 'alias' in contact
                     data for resolved identifier
        tags:
           - OOBIs
        requestBody:
            required: true
            content:
              application/json:
                schema:
                    description: OOBI
                    properties:
                        oobialias:
                          type: string
                          description: alias to assign to the identifier resolved from this OOBI
                          required: false
                        url:
                          type: string
                          description:  URL OOBI
                        rpy:
                          type: object
                          description: unsigned KERI `rpy` event message with endpoints
        responses:
           202:
              description: OOBI resolution to key state successful

        """
        agent = req.context.agent
        body = req.get_media()

        if "url" in body:
            oobi = body["url"]
            dt = helping.nowUTC()

            obr = OobiRecord(date=helping.toIso8601(dt))
            if "oobialias" in body:
                obr.oobialias = body["oobialias"]

            agent.hby.db.oobis.pin(keys=(oobi,), val=obr)

        elif "rpy" in body:
            raise falcon.HTTPNotImplemented(description="'rpy' support not implemented yet")

        else:
            raise falcon.HTTPBadRequest(description="invalid OOBI request body, either 'rpy' or 'url' is required")

        oid = randomNonce()
        op = agent.monitor.submit(oid, longrunning.OpTypes.oobi, metadata=dict(oobi=oobi))

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")


class OobiResourceEnd:

    @staticmethod
    def on_get(req, rep, alias):
        """ OOBI GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            alias: option route parameter for specific identifier to get

        ---
        summary:  Get OOBI for specific identifier
        description:  Generate OOBI for the identifier of the specified alias and role
        tags:
           - OOBIs
        parameters:
          - in: path
            name: alias
            schema:
              type: string
            required: true
            description: human readable alias for the identifier generate OOBI for
          - in: query
            name: role
            schema:
              type: string
            required: true
            description: role for which to generate OOBI
        responses:
            200:
              description: An array of Identifier key state information
              content:
                  application/json:
                    schema:
                        description: Key state information for current identifiers
                        type: object
        """
        agent = req.context.agent
        hab = agent.hby.habByName(alias)
        if hab is None:
            raise falcon.HTTPBadRequest(description="Invalid alias to generate OOBI")

        role = req.params["role"]

        res = dict(role=role)
        if role in (kering.Roles.witness,):  # Fetch URL OOBIs for all witnesses
            oobis = []
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http)
                if not urls:
                    raise falcon.HTTPNotFound(description=f"unable to query witness {wit}, no http endpoint")

                up = urlparse(urls[kering.Schemes.http])
                oobis.append(f"http://{up.hostname}:{up.port}/oobi/{hab.pre}/witness/{wit}")
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http)
            if not urls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            up = urlparse(urls[kering.Schemes.http])
            oobis.append(f"http://{up.hostname}:{up.port}/oobi/{hab.pre}/controller")
            res["oobis"] = oobis
        elif role in (kering.Roles.agent,):
            oobis = []
            roleUrls = hab.fetchRoleUrls(hab.pre, scheme=kering.Schemes.http, role=kering.Roles.agent)
            if not roleUrls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            for eid, urls in roleUrls['agent'].items():
                up = urlparse(urls[kering.Schemes.http])
                oobis.append(f"http://{up.hostname}:{up.port}/oobi/{hab.pre}/agent/{eid}")
                res["oobis"] = oobis
        else:
            rep.status = falcon.HTTP_404
            return

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")


class QueryCollectionEnd:

    @staticmethod
    def on_post(req, rep):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary:  Display key event log (KEL) for given identifier prefix
        description:  If provided qb64 identifier prefix is in Kevers, return the current state of the
                      identifier along with the KEL and all associated signatures and receipts
        tags:
          - Query
        parameters:
          - in: body
            name: pre
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of KEL to load
        responses:
           200:
              description: Key event log and key state of identifier
           404:
              description: Identifier not found in Key event database


        """
        agent = req.context.agent
        body = req.get_media()
        pre = httping.getRequiredParam(body, "pre")
        qry = dict(pre=pre)

        meta = dict()
        if "anchor" in body:
            meta["anchor"] = body["anchor"]
        elif "sn" in body:
            meta["sn"] = body["sn"]
        else:  # Must reset key state so we know when we have a new update.
            for (keys, saider) in agent.hby.db.knas.getItemIter(keys=(pre,)):
                agent.hby.db.knas.rem(keys)
                agent.hby.db.ksns.rem((saider.qb64,))
                agent.hby.db.ksns.rem((saider.qb64,))

        qry.update(meta)
        agent.queries.append(qry)
        op = agent.monitor.submit(pre, longrunning.OpTypes.query, metadata=meta)

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")
