# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
import json
import os
from dataclasses import asdict
from urllib.parse import urlparse, urljoin

from keri import kering
from keri.app.notifying import Notifier
from keri.app.storing import Mailboxer

import falcon
from falcon import media
from hio.base import doing
from hio.core import http, tcp
from hio.help import decking
from keri.app import configing, keeping, habbing, storing, signaling, oobiing, agenting, \
    forwarding, querying, connecting, grouping
from keri.app.grouping import Counselor
from keri.app.keeping import Algos
from keri.core import coring, parsing, eventing, routing, serdering
from keri.core.coring import Ilks, randomNonce
from keri.db import dbing
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
          keypath=None, certpath=None, cafilepath=None):
    """ Set up an ahab in Signify mode """

    agency = Agency(name=name, base=base, bran=bran, configFile=configFile, configDir=configDir)
    bootApp = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input',
                        'signify-resource', 'signify-timestamp']))

    bootServer = createHttpServer(bootPort, bootApp, keypath, certpath, cafilepath)
    if not bootServer.reopen():
        raise RuntimeError(f"cannot create boot http server on port {bootPort}")
    bootServerDoer = http.ServerDoer(server=bootServer)
    bootEnd = BootEnd(agency)
    bootApp.add_route("/boot", bootEnd)
    bootApp.add_route("/health", HealthEnd())

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

    adminServer = createHttpServer(adminPort, app, keypath, certpath, cafilepath)
    if not adminServer.reopen():
        raise RuntimeError(f"cannot create admin http server on port {adminPort}")
    adminServerDoer = http.ServerDoer(server=adminServer)

    doers = [agency, bootServerDoer, adminServerDoer]
    loadEnds(app=app)
    aidEnd = aiding.loadEnds(app=app, agency=agency, authn=authn)
    credentialing.loadEnds(app=app, identifierResource=aidEnd)
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

    def __init__(self, name, bran, base="", configFile=None, configDir=None, adb=None, temp=False):
        self.name = name
        self.base = base
        self.bran = bran
        self.temp = temp
        self.configFile = configFile
        self.configDir = configDir
        self.cf = None
        if self.configFile is not None:  # Load config file if creating database
            self.cf = configing.Configer(name=self.configFile,
                                         base="",
                                         headDirPath=self.configDir,
                                         temp=False,
                                         reopen=True,
                                         clear=False)

        self.agents = dict()

        self.adb = adb if adb is not None else basing.AgencyBaser(name="TheAgency", base=base, reopen=True, temp=temp)
        super(Agency, self).__init__(doers=[], always=True)

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

        res = self.adb.agnt.pin(keys=(caid,),
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

        self.swain = delegating.Sealer(hby=hby, proxy=agentHab)
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

        receiptor = agenting.Receiptor(hby=hby)
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.witPub = agenting.WitnessPublisher(hby=self.hby)
        self.witDoer = agenting.WitnessReceiptor(hby=self.hby)
        self.submitter = agenting.WitnessReceiptor(hby=self.hby, force=True, tock=5.0)

        self.rep = storing.Respondant(hby=hby, cues=self.cues, mbx=Mailboxer(name=self.hby.name, temp=self.hby.temp))

        doers = [habbing.HaberyDoer(habery=hby), receiptor, self.witq, self.witPub, self.rep, self.swain,
                 self.counselor, self.witDoer, self.submitter, *oobiery.doers]

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
        self.monitor = longrunning.Monitor(hby=hby, swain=self.swain, counselor=self.counselor, temp=hby.temp,
                                           registrar=self.registrar, credentialer=self.credentialer, exchanger=self.exc, submitter=self.submitter)

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
            Initer(agentHab=agentHab, caid=caid),
            Querier(hby=hby, agentHab=agentHab, kvy=self.kvy, queries=self.queries),
            Escrower(kvy=self.kvy, rgy=self.rgy, rvy=self.rvy, tvy=self.tvy, exc=self.exc, vry=self.verifier,
                     registrar=self.registrar, credentialer=self.credentialer),
            ParserDoer(kvy=self.kvy, parser=self.parser),
            Witnesser(receiptor=receiptor, witners=self.witners),
            Delegator(agentHab=agentHab, swain=self.swain, anchors=self.anchors),
            ExchangeSender(hby=hby, agentHab=agentHab, exc=self.exc, exchanges=self.exchanges),
            Granter(hby=hby, rgy=rgy,  agentHab=agentHab, exc=self.exc, grants=self.grants),
            Admitter(hby=hby, witq=self.witq, psr=self.parser, agentHab=agentHab, exc=self.exc, admits=self.admits),
            GroupRequester(hby=hby, agentHab=agentHab, counselor=self.counselor, groups=self.groups),
            SeekerDoer(seeker=self.seeker, cues=self.verifier.cues),
            ExchangeCueDoer(seeker=self.exnseeker, cues=self.exc.cues, queries=self.queries)
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

    def witnessResubmit(self, pre):
        self.submitDoer.msgs.append(dict(pre=pre))        


class ParserDoer(doing.Doer):

    def __init__(self, kvy, parser):
        self.kvy = kvy
        self.parser = parser
        super(ParserDoer, self).__init__()

    def recur(self, tyme=None):
        if self.parser.ims:
            logger.info("Agent %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator()  # process messages continuously
        return done  # should never get here except forced close


class Witnesser(doing.Doer):

    def __init__(self, receiptor, witners):
        self.receiptor = receiptor
        self.witners = witners
        super(Witnesser, self).__init__()

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

    def __init__(self, agentHab, swain, anchors):
        self.agentHab = agentHab
        self.swain = swain
        self.anchors = anchors
        super(Delegator, self).__init__()

    def recur(self, tyme=None):
        if self.anchors:
            msg = self.anchors.popleft()
            sn = msg["sn"] if "sn" in msg else None
            self.swain.delegation(pre=msg["pre"], sn=sn, proxy=self.agentHab)

        return False


class ExchangeSender(doing.DoDoer):

    def __init__(self, hby, agentHab, exc, exchanges):
        self.hby = hby
        self.agentHab = agentHab
        self.exc = exc
        self.exchanges = exchanges
        super(ExchangeSender, self).__init__(always=True)

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

    def __init__(self, hby, rgy, agentHab, exc, grants):
        self.hby = hby
        self.rgy = rgy
        self.agentHab = agentHab
        self.exc = exc
        self.grants = grants
        super(Granter, self).__init__(always=True)

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

    def __init__(self, hby, witq, psr, agentHab, exc, admits):
        self.hby = hby
        self.agentHab = agentHab
        self.witq = witq
        self.psr = psr
        self.exc = exc
        self.admits = admits
        super(Admitter, self).__init__()

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

    def __init__(self, seeker, cues):
        self.seeker = seeker
        self.cues = cues

        super(SeekerDoer, self).__init__()

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

    def __init__(self, seeker, cues, queries):
        self.seeker = seeker
        self.cues = cues
        self.queries = queries

        super(ExchangeCueDoer, self).__init__()

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
    def __init__(self, agentHab, caid):
        self.agentHab = agentHab
        self.caid = caid
        super(Initer, self).__init__()

    def recur(self, tyme):
        """ Prints Agent name and prefix """
        if not self.agentHab.inited:
            return False

        print("  Agent:", self.agentHab.pre, "  Controller:", self.caid)
        return True


class GroupRequester(doing.Doer):

    def __init__(self, hby, agentHab, counselor, groups):
        self.hby = hby
        self.agentHab = agentHab
        self.counselor = counselor
        self.groups = groups

        super(GroupRequester, self).__init__()

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

    def __init__(self, hby, agentHab, queries, kvy):
        self.hby = hby
        self.agentHab = agentHab
        self.queries = queries
        self.kvy = kvy

        super(Querier, self).__init__(always=True)

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
        icp = serdering.SerderKERI(sad=body["icp"])

        if "sig" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "sig" missing from body')
        siger = coring.Siger(qb64=body["sig"])

        caid = icp.pre

        if self.agency.get(caid=caid) is not None:
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

            serder = serdering.SerderKERI(raw=bytes(raw))
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
