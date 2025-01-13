# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
from base64 import b64decode
import json
import os
import datetime
from dataclasses import asdict
from urllib.parse import urlparse, urljoin
from types import MappingProxyType

import falcon
from falcon import media
from hio.base import doing
from hio.core import http, tcp
from hio.help import decking

from keri import kering
from keri import core
from keri.app.notifying import Notifier
from keri.app.storing import Mailboxer

from keri.app import configing, keeping, habbing, storing, signaling, oobiing, agenting, \
    forwarding, querying, connecting, grouping
from keri.app.grouping import Counselor
from keri.app.keeping import Algos
from keri.core import coring, parsing, eventing, routing, serdering
from keri.core.coring import Ilks
from keri.core.signing import Salter
from keri.db.basing import OobiRecord
from keri.vc import protocoling

from keria.end import ending
from keri.help import helping, ogler, nowIso8601
from keri.peer import exchanging
from keri.vdr import verifying
from keri.vdr.credentialing import Regery, sendArtifacts
from keri.vdr.eventing import Tevery
from keri.app import challenging

from . import aiding, notifying, indirecting, credentialing, ipexing, delegating
from . import grouping as keriagrouping
from ..peer import exchanging as keriaexchanging
from .specing import AgentSpecResource
from ..core import authing, longrunning, httping
from ..core.authing import Authenticater
from ..core.keeping import RemoteManager
from ..db import basing

logger = ogler.getLogger()


def setup(name, bran, adminPort, bootPort, base='', httpPort=None, configFile=None, configDir=None,
          keypath=None, certpath=None, cafilepath=None, cors=False, releaseTimeout=None, curls=None,
          iurls=None, durls=None, bootUsername=None, bootPassword=None):
    """ Set up an ahab in Signify mode """

    agency = Agency(name=name, base=base, bran=bran, configFile=configFile, configDir=configDir, releaseTimeout=releaseTimeout, curls=curls, iurls=iurls, durls=durls)
    bootApp = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                        'signify-resource', 'signify-timestamp']))

    bootServer = createHttpServer(bootPort, bootApp, keypath, certpath, cafilepath)
    if not bootServer.reopen():
        raise RuntimeError(f"cannot create boot http server on port {bootPort}")
    bootServerDoer = http.ServerDoer(server=bootServer)
    bootEnd = BootEnd(agency, username=bootUsername, password=bootPassword)
    bootApp.add_route("/boot", bootEnd)
    bootApp.add_route("/health", HealthEnd())

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agency=agency)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                        'signify-resource', 'signify-timestamp']))
    if cors:
        app.add_middleware(middleware=httping.HandleCORS())
    app.add_middleware(authing.SignatureValidationComponent(agency=agency, authn=authn, allowed=["/agent"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    adminServer = createHttpServer(adminPort, app, keypath, certpath, cafilepath)
    if not adminServer.reopen():
        raise RuntimeError(f"cannot create admin http server on port {adminPort}")
    adminServerDoer = http.ServerDoer(server=adminServer)

    doers = [agency, bootServerDoer, adminServerDoer]
    loadEnds(app=app)
    aidEnd = aiding.loadEnds(app=app, agency=agency, authn=authn)
    credentialing.loadEnds(app=app, identifierResource=aidEnd)
    delegating.loadEnds(app=app, identifierResource=aidEnd)
    notifying.loadEnds(app=app)
    keriagrouping.loadEnds(app=app)
    keriaexchanging.loadEnds(app=app)
    ipexing.loadEnds(app=app)

    if httpPort:
        happ = falcon.App(middleware=falcon.CORSMiddleware(
            allow_origins='*', allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                            'signify-resource', 'signify-timestamp']))
        happ.req_options.media_handlers.update(media.Handlers())
        happ.resp_options.media_handlers.update(media.Handlers())

        ending.loadEnds(agency=agency, app=happ)
        indirecting.loadEnds(agency=agency, app=happ)

        server = createHttpServer(httpPort, happ, keypath, certpath, cafilepath)
        if not server.reopen():
            raise RuntimeError(f"cannot create local http server on port {httpPort}")
        httpServerDoer = http.ServerDoer(server=server)
        doers.append(httpServerDoer)

        swagsink = http.serving.StaticSink(staticDirPath="./static")
        happ.add_sink(swagsink, prefix="/swaggerui")

        specEnd = AgentSpecResource(app=app, title='KERIA Interactive Web Interface API')
        specEnd.addRoutes(happ)
        happ.add_route("/spec.yaml", specEnd)

    print("The Agency is loaded and waiting for requests...")
    return doers


def createHttpServer(port, app, keypath=None, certpath=None, cafilepath=None):
    """
    Create an HTTP or HTTPS server depending on whether TLS key material is present

    Parameters:
        port (int)         : port to listen on for all HTTP(s) server instances
        app (falcon.App)   : application instance to pass to the http.Server instance
        keypath (string)   : the file path to the TLS private key
        certpath (string)  : the file path to the TLS signed certificate (public key)
        cafilepath (string): the file path to the TLS CA certificate chain file
    Returns:
        hio.core.http.Server
    """
    if keypath is not None and certpath is not None and cafilepath is not None:
        servant = tcp.ServerTls(certify=False,
                                keypath=keypath,
                                certpath=certpath,
                                cafilepath=cafilepath,
                                port=port)
        server = http.Server(port=port, app=app, servant=servant)
    else:
        server = http.Server(port=port, app=app)
    return server


class Agency(doing.DoDoer):
    """
    Agency

    """

    def __init__(self, name, bran, base="", releaseTimeout=None, configFile=None, configDir=None, adb=None, temp=False, curls=None, iurls=None, durls=None):
        self.name = name
        self.base = base
        self.bran = bran
        self.temp = temp
        self.configFile = configFile
        self.configDir = configDir
        self.cf = None
        self.curls = curls
        self.iurls = iurls
        self.durls = durls

        if self.configFile is not None:
            self.cf = configing.Configer(name=self.configFile,
                                         base="",
                                         headDirPath=self.configDir,
                                         temp=False,
                                         reopen=True,
                                         clear=False)

        self.agents = dict()

        self.adb = adb if adb is not None else basing.AgencyBaser(name="TheAgency", base=base, reopen=True, temp=temp)
        super(Agency, self).__init__(doers=[Releaser(self, releaseTimeout=releaseTimeout)], always=True)

    def create(self, caid, salt=None):
        ks = keeping.Keeper(name=caid,
                            base=self.base,
                            temp=self.temp,
                            reopen=True)

        timestamp = nowIso8601()
        data = dict(self.cf.get() if self.cf is not None else { "dt": timestamp })

        habName = f"agent-{caid}"
        if "keria" in data:
            data[habName] = data["keria"]
            del data["keria"]

        if self.curls is not None and isinstance(self.curls, list):
            data[habName] = { "dt": timestamp, "curls": self.curls }

        if self.iurls is not None and isinstance(self.iurls, list):
            data["iurls"] = self.iurls

        if self.durls is not None and isinstance(self.durls, list):
            data["durls"] = self.durls

        config = configing.Configer(name=f"{caid}",
                                base="",
                                human=False,
                                temp=self.temp,
                                reopen=True,
                                clear=False)

        config.put(data)

        # Create the Hab for the Agent with only 2 AIDs
        agentHby = habbing.Habery(name=caid, base=self.base, bran=self.bran, ks=ks, cf=config, temp=self.temp, salt=salt)
        agentHab = agentHby.makeHab(habName, ns="agent", transferable=True, delpre=caid)
        agentRgy = Regery(hby=agentHby, name=agentHab.name, base=self.base, temp=self.temp)

        agent = Agent(hby=agentHby,
                      rgy=agentRgy,
                      agentHab=agentHab,
                      caid=caid,
                      agency=self)

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

    def shut(self, agent):
        logger.info(f"closing idle agent {agent.caid}")
        agent.remove(agent.doers)
        self.remove([agent])
        del self.agents[agent.caid]
        agent.hby.ks.close(clear=False)
        agent.seeker.close(clear=False)
        agent.exnseeker.close(clear=False)
        agent.monitor.opr.close(clear=False)
        agent.notifier.noter.close(clear=False)
        agent.rep.mbx.close(clear=False)
        agent.registrar.rgy.close()
        agent.mgr.rb.close(clear=False)
        agent.hby.close(clear=False)

    def get(self, caid):
        if caid in self.agents:
            agent = self.agents[caid]
            agent.last = helping.nowUTC()
            return agent

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
        self.extend([agent])

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
        self.cfd = MappingProxyType(dict(self.hby.cf.get()) if self.hby.cf is not None else dict())
        self.tocks = MappingProxyType(self.cfd.get("tocks", {}))

        self.last = helping.nowUTC()

        self.swain = delegating.Anchorer(hby=hby, proxy=agentHab)
        self.counselor = Counselor(hby=hby, swain=self.swain, proxy=agentHab)
        self.org = connecting.Organizer(hby=hby)

        oobiery = oobiing.Oobiery(hby=hby)

        self.mgr = RemoteManager(hby=hby)

        self.cues = decking.Deck()
        self.groups = decking.Deck()
        self.anchors = decking.Deck()
        self.witners = decking.Deck()
        self.queries = decking.Deck()
        self.exchanges = decking.Deck()
        self.grants = decking.Deck()
        self.admits = decking.Deck()
        self.submits = decking.Deck()

        receiptor = agenting.Receiptor(hby=hby)
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.witPub = agenting.WitnessPublisher(hby=self.hby)
        self.witDoer = agenting.WitnessReceiptor(hby=self.hby)
        self.witSubmitDoer = agenting.WitnessReceiptor(hby=self.hby, force=True)

        self.rep = storing.Respondant(hby=hby, cues=self.cues, mbx=Mailboxer(name=self.hby.name, temp=self.hby.temp))

        doers = [habbing.HaberyDoer(habery=hby), receiptor, self.witq, self.witPub, self.rep, self.swain,
                 self.counselor, self.witDoer, *oobiery.doers]

        signaler = signaling.Signaler()
        self.notifier = Notifier(hby=hby, signaler=signaler)
        self.mux = grouping.Multiplexor(hby=hby, notifier=self.notifier)

        # Initialize all the credential processors
        self.verifier = verifying.Verifier(hby=hby, reger=rgy.reger)
        self.registrar = credentialing.Registrar(agentHab=agentHab, hby=hby, rgy=rgy, counselor=self.counselor,
                                                 witPub=self.witPub, witDoer=self.witDoer, verifier=self.verifier)
        self.credentialer = credentialing.Credentialer(agentHab=agentHab, hby=self.hby, rgy=self.rgy,
                                                       registrar=self.registrar, verifier=self.verifier,
                                                       notifier=self.notifier)

        self.seeker = basing.Seeker(name=hby.name, db=hby.db, reger=self.rgy.reger, reopen=True, temp=self.hby.temp)
        self.exnseeker = basing.ExnSeeker(name=hby.name, db=hby.db, reopen=True, temp=self.hby.temp)

        challengeHandler = challenging.ChallengeHandler(db=hby.db, signaler=signaler)

        handlers = [challengeHandler]
        self.exc = exchanging.Exchanger(hby=hby, handlers=handlers)
        grouping.loadHandlers(exc=self.exc, mux=self.mux)
        protocoling.loadHandlers(hby=self.hby, exc=self.exc, notifier=self.notifier)
        self.submitter = Submitter(hby=hby, submits=self.submits, witRec=self.witSubmitDoer)
        self.monitor = longrunning.Monitor(hby=hby, swain=self.swain, counselor=self.counselor, temp=hby.temp,
                                           registrar=self.registrar, credentialer=self.credentialer, submitter=self.submitter, exchanger=self.exc)

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
                                     vry=self.verifier,
                                     local=True)  # disable misfit escrow until we can add another parser for remote.

        doers.extend([
            Initer(agentHab=agentHab, caid=caid, tock=self.tocks.get("initer", 0.0)),
            Querier(hby=hby, agentHab=agentHab, kvy=self.kvy, queries=self.queries,
                    tock=self.tocks.get("querier", 0.0)),
            Escrower(kvy=self.kvy, rgy=self.rgy, rvy=self.rvy, tvy=self.tvy, exc=self.exc, vry=self.verifier,
                     registrar=self.registrar, credentialer=self.credentialer, tock=self.tocks.get("escrower", 0.0)),
            ParserDoer(kvy=self.kvy, parser=self.parser, tock=self.tocks.get("parser", 0.0)),
            Witnesser(receiptor=receiptor, witners=self.witners, tock=self.tocks.get("witnesser", 0.0)),
            Delegator(agentHab=agentHab, swain=self.swain, anchors=self.anchors, tock=self.tocks.get("delegator", 0.0)),
            ExchangeSender(hby=hby, agentHab=agentHab, exc=self.exc, exchanges=self.exchanges,
                           tock=self.tocks.get("exchangeSender", 0.0)),
            Granter(hby=hby, rgy=rgy, agentHab=agentHab, exc=self.exc, grants=self.grants,
                    tock=self.tocks.get("granter", 0.0)),
            Admitter(hby=hby, witq=self.witq, psr=self.parser, agentHab=agentHab, exc=self.exc, admits=self.admits,
                     tock=self.tocks.get("admitter", 0.0)),
            GroupRequester(hby=hby, agentHab=agentHab, counselor=self.counselor, groups=self.groups,
                           tock=self.tocks.get("groupRequester", 0.0)),
            SeekerDoer(seeker=self.seeker, cues=self.verifier.cues, tock=self.tocks.get("seeker", 0.0)),
            ExchangeCueDoer(seeker=self.exnseeker, cues=self.exc.cues, queries=self.queries,
                            tock=self.tocks.get("exchangecue", 0.0)),
            self.submitter,
        ])

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


class ParserDoer(doing.Doer):

    def __init__(self, kvy, parser, tock=0.0):
        self.kvy = kvy
        self.parser = parser
        self.tock = tock
        super(ParserDoer, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        if self.parser.ims:
            logger.info("Agent %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator()  # process messages continuously
        return done  # should never get here except forced close


class Witnesser(doing.Doer):

    def __init__(self, receiptor, witners, tock=0.0):
        self.receiptor = receiptor
        self.witners = witners
        self.tock = tock
        super(Witnesser, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        while True:
            if self.witners:
                msg = self.witners.popleft()
                serder = msg["serder"]

                # If we are a rotation event, may need to catch new witnesses up to current key state
                if serder.ked['t'] in (Ilks.rot, Ilks.drt):
                    adds = serder.ked["ba"]
                    for wit in adds:
                        yield from self.receiptor.catchup(serder.pre, wit)

                yield from self.receiptor.receipt(serder.pre, serder.sn)

            yield self.tock


class Delegator(doing.Doer):

    def __init__(self, agentHab, swain, anchors, tock=0.0):
        self.agentHab = agentHab
        self.swain = swain
        self.anchors = anchors
        self.tock = tock
        super(Delegator, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        if self.anchors:
            msg = self.anchors.popleft()
            sn = msg["sn"] if "sn" in msg else None
            self.swain.delegation(pre=msg["pre"], sn=sn, proxy=self.agentHab)

        return False


class ExchangeSender(doing.DoDoer):

    def __init__(self, hby, agentHab, exc, exchanges, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.exc = exc
        self.exchanges = exchanges
        self.tock = tock
        super(ExchangeSender, self).__init__(always=True, tock=self.tock)

    def recur(self, tyme, deeds=None):
        if self.exchanges:
            msg = self.exchanges.popleft()
            said = msg['said']
            if not self.exc.complete(said=said):
                self.exchanges.append(msg)
                return super(ExchangeSender, self).recur(tyme, deeds)

            serder, pathed = exchanging.cloneMessage(self.hby, said)

            pre = msg["pre"]
            rec = msg["rec"]
            topic = msg['topic']
            hab = self.hby.habs[pre]
            if self.exc.lead(hab, said=said):
                atc = exchanging.serializeMessage(self.hby, said)
                del atc[:serder.size]
                for recp in rec:
                    postman = forwarding.StreamPoster(hby=self.hby, hab=self.agentHab, recp=recp, topic=topic)
                    try:
                        postman.send(serder=serder,
                                     attachment=atc)
                    except kering.ValidationError:
                        logger.info(f"unable to send to recipient={recp}")
                    else:
                        doer = doing.DoDoer(doers=postman.deliver())
                        self.extend([doer])

        return super(ExchangeSender, self).recur(tyme, deeds)


class Granter(doing.DoDoer):

    def __init__(self, hby, rgy, agentHab, exc, grants, tock=0.0):
        self.hby = hby
        self.rgy = rgy
        self.agentHab = agentHab
        self.exc = exc
        self.grants = grants
        self.tock = tock
        super(Granter, self).__init__(always=True, tock=self.tock)

    def recur(self, tyme, deeds=None):
        if self.grants:
            msg = self.grants.popleft()
            said = msg['said']
            if not self.exc.complete(said=said):
                self.grants.append(msg)
                return super(Granter, self).recur(tyme, deeds)

            serder, pathed = exchanging.cloneMessage(self.hby, said)

            pre = msg["pre"]
            rec = msg["rec"]
            hab = self.hby.habs[pre]
            if self.exc.lead(hab, said=said):
                for recp in rec:
                    postman = forwarding.StreamPoster(hby=self.hby, hab=self.agentHab, recp=recp, topic="credential")
                    try:
                        credSaid = serder.ked['e']['acdc']['d']
                        creder = self.rgy.reger.creds.get(keys=(credSaid,))
                        sendArtifacts(self.hby, self.rgy.reger, postman, creder, recp)
                        sources = self.rgy.reger.sources(self.hby.db, creder)
                        for source, atc in sources:
                            sendArtifacts(self.hby, self.rgy.reger, postman, source, recp)
                            postman.send(serder=source, attachment=atc)

                    except kering.ValidationError:
                        logger.info(f"unable to send to recipient={recp}")
                    except KeyError:
                        logger.info(f"invalid grant message={serder.ked}")
                    else:
                        doer = doing.DoDoer(doers=postman.deliver())
                        self.extend([doer])

        return super(Granter, self).recur(tyme, deeds)


class Admitter(doing.Doer):

    def __init__(self, hby, witq, psr, agentHab, exc, admits, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.witq = witq
        self.psr = psr
        self.exc = exc
        self.admits = admits
        self.tock = tock
        super(Admitter, self).__init__(tock=self.tock)

    def recur(self, tyme):
        if self.admits:
            msg = self.admits.popleft()
            said = msg['said']
            if not self.exc.complete(said=said):
                self.admits.append(msg)
                return False

            admit, _ = exchanging.cloneMessage(self.hby, said)

            if 'p' not in admit.ked or not admit.ked['p']:
                print(f"Invalid admit message={admit.ked}, no grant listed")
                return False

            grant, pathed = exchanging.cloneMessage(self.hby, admit.ked['p'])

            embeds = grant.ked['e']
            acdc = embeds["acdc"]
            issr = acdc['i']

            # Lets get the latest KEL and Registry if needed
            self.witq.query(hab=self.agentHab, pre=issr)
            if "ri" in acdc:
                self.witq.telquery(hab=self.agentHab, pre=issr, ri=acdc["ri"], i=acdc["d"])

            for label in ("anc", "iss", "acdc"):
                ked = embeds[label]
                if label not in pathed or not pathed[label]:
                    print(f"missing path label {label}")
                    continue

                sadder = coring.Sadder(ked=ked)
                ims = bytearray(sadder.raw) + pathed[label]
                self.psr.parseOne(ims=ims)


class SeekerDoer(doing.Doer):

    def __init__(self, seeker, cues, tock=0.0):
        self.seeker = seeker
        self.cues = cues
        self.tock = tock
        super(SeekerDoer, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        if self.cues:
            cue = self.cues.popleft()
            if cue["kin"] == "saved":
                creder = cue["creder"]
                try:
                    self.seeker.index(said=creder.said)
                except Exception:
                    self.cues.append(cue)
                    return False
            else:
                self.cues.append(cue)
                return False


class ExchangeCueDoer(doing.Doer):

    def __init__(self, seeker, cues, queries, tock=0.0):
        self.seeker = seeker
        self.cues = cues
        self.queries = queries
        self.tock = tock
        super(ExchangeCueDoer, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        if self.cues:
            cue = self.cues.popleft()
            if cue["kin"] == "saved":
                said = cue["said"]
                try:
                    self.seeker.index(said=said)
                except Exception:
                    self.cues.append(cue)
                    return False
            elif cue["kin"] == "query":
                self.queries.append(cue['q'])
                return False
            else:
                self.cues.append(cue)
                return False


class Initer(doing.Doer):
    def __init__(self, agentHab, caid, tock=0.0):
        self.agentHab = agentHab
        self.caid = caid
        self.tock = tock
        super(Initer, self).__init__(tock=self.tock)

    def recur(self, tyme):
        """ Prints Agent name and prefix """
        if not self.agentHab.inited:
            return False

        print("  Agent:", self.agentHab.pre, "  Controller:", self.caid)
        return True


class GroupRequester(doing.Doer):

    def __init__(self, hby, agentHab, counselor, groups, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.counselor = counselor
        self.groups = groups
        self.tock = tock
        super(GroupRequester, self).__init__(tock=self.tock)

    def recur(self, tyme):
        """ Checks cue for group proceccing requests and processes any with Counselor """
        if self.groups:
            msg = self.groups.popleft()
            serder = msg["serder"]

            ghab = self.hby.habs[serder.pre]

            prefixer = coring.Prefixer(qb64=serder.pre)
            seqner = coring.Seqner(sn=serder.sn)
            saider = coring.Saider(qb64=serder.said)
            self.counselor.start(ghab=ghab, prefixer=prefixer, seqner=seqner, saider=saider)

        return False


class Querier(doing.DoDoer):

    def __init__(self, hby, agentHab, queries, kvy, tock=0.0):
        self.hby = hby
        self.agentHab = agentHab
        self.queries = queries
        self.kvy = kvy
        self.tock = tock
        super(Querier, self).__init__(always=True, tock=self.tock)

    def recur(self, tyme, deeds=None):
        """ Processes query reqests submitting any on the cue"""
        if self.queries:
            msg = self.queries.popleft()
            if "pre" not in msg:
                return False

            pre = msg["pre"]

            if "sn" in msg:
                sn = int(msg['sn'], 16)
                seqNoDo = querying.SeqNoQuerier(hby=self.hby, hab=self.agentHab, pre=pre, sn=sn)
                self.extend([seqNoDo])
            elif "anchor" in msg:
                anchor = msg['anchor']
                anchorDo = querying.AnchorQuerier(hby=self.hby, hab=self.agentHab, pre=pre, anchor=anchor)
                self.extend([anchorDo])
            else:
                qryDo = querying.QueryDoer(hby=self.hby, hab=self.agentHab, pre=pre, kvy=self.kvy)
                self.extend([qryDo])

        return super(Querier, self).recur(tyme, deeds)


class Escrower(doing.Doer):
    def __init__(self, kvy, rgy, rvy, tvy, exc, vry, registrar, credentialer, tock=0.0):
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
        self.tock = tock

        super(Escrower, self).__init__(tock=self.tock)

    def recur(self, tyme):
        """ Process all escrows once per loop. """
        self.kvy.processEscrows()
        self.kvy.processEscrowDelegables()
        self.rgy.processEscrows()
        self.rvy.processEscrowReply()
        if self.tvy is not None:
            self.tvy.processEscrows()
        self.exc.processEscrow()
        self.vry.processEscrows()
        self.registrar.processEscrows()
        self.credentialer.processEscrows()
        return False
    
class Releaser(doing.Doer):
    def __init__(self, agency: Agency, releaseTimeout=86400):
        """ Check open agents and close if idle for more than releaseTimeout seconds
        Parameters:
            agency (Agency): KERIA agent manager
            releaseTimeout (int): Timeout in seconds
 
        """
        self.tock = 60.0
        self.agents = agency.agents
        self.agency = agency
        self.releaseTimeout = releaseTimeout

        super(Releaser, self).__init__(tock=self.tock)

    def recur(self, tyme=None):
        while True:
            idle = []
            for caid in self.agents:
                now = helping.nowUTC()
                if (now - self.agents[caid].last) > datetime.timedelta(seconds=self.releaseTimeout):
                    idle.append(caid)

            for caid in idle:
                self.agency.shut(self.agents[caid])
            yield self.tock

def loadEnds(app):
    opColEnd = longrunning.OperationCollectionEnd()
    app.add_route("/operations", opColEnd)
    opResEnd = longrunning.OperationResourceEnd()
    app.add_route("/operations/{name}", opResEnd)

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

    configEnd = ConfigResourceEnd()
    app.add_route("/config", configEnd)


class BootEnd:
    """ Resource class for creating datastore in cloud ahab """

    def __init__(self, agency: Agency, username: str | None = None, password: str | None = None):
        """ Provides endpoints for initializing and unlocking an agent
        Parameters:
            agency (Agency): Agency for managing agents
            username (str): username for boot request
            password (str): password for boot request
        """
        self.username = username
        self.password = password
        self.agency = agency

    def parseBasicAuth(self, req: falcon.Request):
        schemePrefix = 'Basic '
        if req.auth is None or not req.auth.startswith(schemePrefix):
            return None, None

        token = b64decode(req.auth[len(schemePrefix):]).decode('utf-8')
        splitIndex = token.find(':')
        if splitIndex == -1:
            return None, None

        username = token[:splitIndex]
        password = token[splitIndex + 1:]

        return username, password


    def authenticate(self, req: falcon.Request):
        # Username AND Password is not set, so no need to authenticate
        if self.username is None and self.password is None:
            return

        if req.auth is None:
            raise falcon.HTTPUnauthorized(title="Unauthorized")

        try:
            username, password = self.parseBasicAuth(req)

            if username == self.username and password == self.password:
                return

        except Exception:
            raise falcon.HTTPUnauthorized(title="Unauthorized")

        raise falcon.HTTPUnauthorized(title="Unauthorized")

    def on_post(self, req: falcon.Request, rep: falcon.Response):
        """ Inception event POST endpoint

        Give me a new Agent.  Create Habery using ctrlPRE as database name, agentHab that anchors the caid and
        returns the KEL of agentHAB Stores ControllerPRE -> AgentPRE in database

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """

        self.authenticate(req)

        body = req.get_media()
        if "icp" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "icp" missing from body')
        icp = serdering.SerderKERI(sad=body["icp"])

        if "sig" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "sig" missing from body')
        siger = core.Siger(qb64=body["sig"])

        caid = icp.pre

        if self.agency.get(caid=caid) is not None:
            raise falcon.HTTPConflict(title="agent already exists",
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
        rep.data = json.dumps(asdict(agent.agentHab.kever.state())).encode("utf-8")


class HealthEnd:
    """Health resource for determining that a container is live"""

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_OK
        resp.media = {"message": f"Health is okay. Time is {nowIso8601()}"}


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
            name: pre
            description: qb64 identifier prefix of KEL to load
            schema:
              type: string
            required: true
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
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest(description="required parameter 'pre' missing")

        pre = req.params.get("pre")
        preb = pre.encode("utf-8")
        events = []
        for fn, dig in agent.hby.db.getFelItemPreIter(preb, fn=0):
            if not (raw := agent.hby.db.cloneEvtMsg(pre=preb, fn=fn, dig=dig)):
                raise falcon.HTTPInternalServerError(f"Missing event for dig={dig}.")

            serder = serdering.SerderKERI(raw=bytes(raw))
            atc = raw[serder.size:]
            events.append(dict(ked=serder.ked, atc=atc.decode("utf-8")))

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
                  oneOf:
                    - type: object
                      properties:
                        oobialias:
                          type: string
                          description: alias to assign to the identifier resolved from this OOBI
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

        oid = Salter().qb64
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
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http) or hab.fetchUrls(eid=wit,
                                                                                           scheme=kering.Schemes.https)
                if not urls:
                    raise falcon.HTTPNotFound(description=f"unable to query witness {wit}, no http endpoint")

                url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
                up = urlparse(url)
                oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/witness/{wit}"))
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http) or hab.fetchUrls(eid=hab.pre,
                                                                                           scheme=kering.Schemes.https)
            if not urls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
            up = urlparse(url)
            oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/controller"))
            res["oobis"] = oobis
        elif role in (kering.Roles.agent,):
            oobis = []
            roleUrls = hab.fetchRoleUrls(hab.pre, scheme=kering.Schemes.http,
                                         role=kering.Roles.agent) or hab.fetchRoleurls(hab.pre,
                                                                                       scheme=kering.Schemes.https,
                                                                                       role=kering.Roles.agent)
            if not roleUrls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            for eid, urls in roleUrls['agent'].items():
                url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
                up = urlparse(url)
                oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/agent/{eid}"))
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
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                    - pre
                properties:
                  pre:
                    type: string
                    description: qb64 identifier prefix of KEL to load
                  anchor:
                    type: string
                    description: Anchor
                  sn:
                    type: string
                    description: Serial number
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

        oid = pre
        if "anchor" in body:
            qry["anchor"] = body["anchor"]
            oid = f"{pre}.{body["anchor"]["d"]}"
        elif "sn" in body:
            qry["sn"] = body["sn"]
            oid = f"{pre}.{body["sn"]}"
        else:  # Must reset key state so we know when we have a new update.
            for (keys, saider) in agent.hby.db.knas.getItemIter(keys=(pre,)):
                agent.hby.db.knas.rem(keys)
                agent.hby.db.ksns.rem((saider.qb64,))
                agent.hby.db.ksns.rem((saider.qb64,))

        agent.queries.append(qry)
        op = agent.monitor.submit(oid, longrunning.OpTypes.query, metadata=qry)

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")

class Submitter(doing.DoDoer):
    def __init__(self, hby, submits, witRec):
        """
        Process to re-submit the last event from the KEL to the witnesses for receipts and to propogate it to each witness
        """
        self.hby = hby
        self.submits = submits
        self.witRec = witRec

        super(Submitter, self).__init__(always=True)

    def recur(self, tyme, deeds=None):
        """Processes submit reqests submitting any on the cue"""
        if self.submits:
            msg = self.submits.popleft()
            alias = msg["alias"]
            hab = self.hby.habByName(name=alias)
            sn = hab.kever.sn
            if hab and hab.kever.wits:
                auths = {}
                if hasattr(msg, "code"):
                    code = msg["code"]
                    if code:
                        for wit in hab.kever.wits:
                            auths[wit] = f"{code}#{helping.nowIso8601()}"
                witDoer = self.witRec
                witDoer.force = True
                self.extend([witDoer])
                print("Re-submit waiting for witness receipts...")
                witDoer.msgs.append(dict(pre=hab.pre, sn=sn))

        else:
            for doer in self.doers:
                if doer.cues:
                    cue = doer.cues.popleft()

                    if len(doer.cues) == 0:
                        print("Re-submit received all witness receipts for", cue["pre"])
                        self.doers.remove(doer)

        return super(Submitter, self).recur(tyme, deeds)


class ConfigResourceEnd:

    @staticmethod
    def on_get(req, rep):
        """ Config GET endpoint

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response

        ---
        summary: Retrieve agent configuration
        description:  Retrieve agent configuration (only necessary fields are exposed)
        tags:
          - Config
        responses:
           200:
              description: Subset of configuration dict as JSON

        """
        agent = req.context.agent
        config = agent.hby.cf.get()
        subset = {key: config[key] for key in ["iurls"] if key in config}

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(subset).encode("utf-8")
