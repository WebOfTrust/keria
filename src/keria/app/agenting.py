# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
import json

from keri import kering
from keri.app.storing import Mailboxer
from ordered_set import OrderedSet as oset

import falcon
from falcon import media
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri.app import configing, keeping, habbing, storing, signaling, notifying, oobiing, agenting, delegating, \
    forwarding, querying, connecting
from keri.app.grouping import Counselor
from keria.app.indirecting import HttpEnd
from keri.app.keeping import Algos
from keri.core import coring, parsing, eventing, routing
from keri.core.coring import Ilks, randomNonce
from keri.db import dbing
from keri.db.basing import OobiRecord
from keria.end import ending
from keri.help import helping, ogler
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying, credentialing
from keri.vdr.eventing import Tevery

from . import aiding
from ..core import authing, longrunning, httping
from ..core.authing import Authenticater
from ..core.keeping import RemoteManager
from ..db import basing

logger = ogler.getLogger()


def setup(name, base, bran, adminPort, bootPort, httpPort=None, configFile=None, configDir=None):
    """ Set up an ahab in Signify mode """

    agency = Agency(name=name, base=base, bran=bran, configFile=configFile, configDir=configDir)
    bootApp = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
    bootServer = http.Server(port=bootPort, app=bootApp)
    bootServerDoer = http.ServerDoer(server=bootServer)
    bootEnd = BootEnd(agency)
    bootApp.add_route("/boot", bootEnd)

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agency=agency)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
    app.add_middleware(authing.SignatureValidationComponent(agency=agency, authn=authn, allowed=["/agent"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    adminServer = http.Server(port=adminPort, app=app)
    adminServerDoer = http.ServerDoer(server=adminServer)

    doers = [agency, bootServerDoer, adminServerDoer]
    loadEnds(app=app)
    aiding.loadEnds(app=app, agency=agency)

    if httpPort:
        happ = falcon.App(middleware=falcon.CORSMiddleware(
            allow_origins='*', allow_credentials='*',
            expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
        happ.req_options.media_handlers.update(media.Handlers())
        happ.resp_options.media_handlers.update(media.Handlers())

        ending.loadEnds(agency=agency, app=happ)
        httpEnd = HttpEnd(agency=agency)
        happ.add_route("/", httpEnd)

        server = http.Server(port=httpPort, app=happ)
        httpServerDoer = http.ServerDoer(server=server)
        doers.append(httpServerDoer)

    print("The Agency is loaded and waiting for requests...")
    return doers


class Agency(doing.DoDoer):
    def __init__(self, name, base, bran, configFile=None, configDir=None, adb=None, temp=False):
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

        self.adb = adb if adb is not None else basing.AgencyBaser(name="TheAgency", reopen=True, temp=temp)
        super(Agency, self).__init__(doers=[], always=True)

    def create(self, caid):
        ks = keeping.Keeper(name=caid,
                            base=self.base,
                            temp=self.temp,
                            reopen=True)

        cf = None
        if self.cf is not None:  # Load config file if creating database
            data = dict(self.cf.get())
            curls = data["keria"]
            data[caid] = curls
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
        agentHab = agentHby.makeHab(caid, ns="agent", transferable=True, data=[caid])
        agentRgy = credentialing.Regery(hby=agentHby, name=agentHab.name, base=self.base, temp=self.temp)

        agent = Agent(agentHby, agentRgy, agentHab,
                      caid=caid,
                      agency=self,
                      configDir=self.configDir,
                      configFile=self.configFile)

        self.adb.agnt.pin(keys=(caid,),
                          val=coring.Prefixer(qb64=agent.pre))

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
                            temp=False,
                            reopen=True)

        agentHby = habbing.Habery(name=caid, base=self.base, bran=self.bran, ks=ks, temp=self.temp)
        agentRgy = credentialing.Regery(hby=agentHby, name=caid, base=self.base, temp=self.temp)

        agentHab = agentHby.habByName(caid, ns="agent")
        if aaid.qb64 != agentHab.pre:
            raise kering.ConfigurationError(f"invalid agent aid={aaid.qb64} to controller aid={caid}")

        agent = Agent(hby=agentHby, rgy=agentRgy, agentHab=agentHab, agency=self, caid=caid)
        self.agents[caid] = agent

        return agent

    def lookup(self, pre):
        prefixer = self.adb.aids.get(keys=(pre,))
        if prefixer is None:
            return None

        try:
            return self.get(prefixer.qb64)
        except kering.ConfigurationError as e:
            return None

    def incept(self, caid, pre):
        self.adb.aids.pin(keys=(pre,), val=coring.Prefixer(qb64=caid))


class Agent(doing.DoDoer):
    """ 
    
    The top level object and DoDoer representing a Habery for a remote controller and all associated processing

    """

    def __init__(self, hby, rgy, agentHab, agency, caid, **opts):

        self.hby = hby
        self.agentHab = agentHab
        self.agency = agency
        self.caid = caid

        self.swain = delegating.Boatswain(hby=hby)
        self.counselor = Counselor(hby=hby)
        self.org = connecting.Organizer(hby=hby)

        oobiery = oobiing.Oobiery(hby=hby)

        self.monitor = longrunning.Monitor(hby=hby, swain=self.swain, counselor=self.counselor, temp=hby.temp)
        self.remoteMgr = RemoteManager(hby=hby)

        self.cues = decking.Deck()
        self.groups = decking.Deck()
        self.anchors = decking.Deck()
        self.witners = decking.Deck()
        self.queries = decking.Deck()
        receiptor = agenting.Receiptor(hby=hby)
        self.postman = forwarding.Poster(hby=hby)
        self.rep = storing.Respondant(hby=hby, cues=self.cues, mbx=Mailboxer(name=self.hby.name, temp=self.hby.temp))

        doers = [habbing.HaberyDoer(habery=hby), receiptor, self.postman, self.rep, self.swain, self.counselor, *oobiery.doers]

        verifier = verifying.Verifier(hby=hby, reger=rgy.reger)

        signaler = signaling.Signaler()
        notifier = notifying.Notifier(hby=hby, signaler=signaler)
        issueHandler = protocoling.IssueHandler(hby=hby, rgy=rgy, notifier=notifier)
        requestHandler = protocoling.PresentationRequestHandler(hby=hby, notifier=notifier)
        applyHandler = protocoling.ApplyHandler(hby=hby, rgy=rgy, verifier=verifier,
                                                name=agentHab.name)
        proofHandler = protocoling.PresentationProofHandler(notifier=notifier)

        handlers = [issueHandler, requestHandler, proofHandler, applyHandler]
        self.exc = exchanging.Exchanger(db=hby.db, handlers=handlers)

        self.rvy = routing.Revery(db=hby.db, cues=self.cues)
        self.kvy = eventing.Kevery(db=hby.db,
                                   lax=True,
                                   local=False,
                                   rvy=self.rvy,
                                   cues=self.cues)
        self.kvy.registerReplyRoutes(router=self.rvy.rtr)

        self.tvy = Tevery(reger=verifier.reger,
                          db=hby.db,
                          local=False,
                          cues=self.cues)

        self.tvy.registerReplyRoutes(router=self.rvy.rtr)
        self.parser = parsing.Parser(framed=True,
                                     kvy=self.kvy,
                                     tvy=self.tvy,
                                     exc=self.exc,
                                     rvy=self.rvy)

        init = Initer(agentHab=agentHab)
        qr = Querier(hby=hby, agentHab=agentHab, kvy=self.kvy, queries=self.queries)
        er = Escrower(kvy=self.kvy, rvy=self.rvy, tvy=self.tvy, exc=self.exc)
        mr = Messager(kvy=self.kvy, parser=self.parser)
        wr = Witnesser(receiptor=receiptor, witners=self.witners)
        dr = Delegator(agentHab=agentHab, swain=self.swain, anchors=self.anchors)
        doers.extend([init, qr, er, mr, wr, dr])

        super().__init__(doers=doers, always=True, **opts)

    @property
    def pre(self):
        return self.agentHab.pre

    def inceptSalty(self, pre, **kwargs):
        keeper = self.remoteMgr.get(Algos.salty)
        keeper.incept(pre=pre, **kwargs)

        self.agency.incept(self.caid, pre)

    def inceptRandy(self, pre, verfers, digers, **kwargs):
        keeper = self.remoteMgr.get(Algos.randy)
        keeper.incept(pre=pre, verfers=verfers, digers=digers, **kwargs)

        self.agency.incept(self.caid, pre)

    def inceptGroup(self, pre, mpre, verfers, digers):
        keeper = self.remoteMgr.get(Algos.group)
        keeper.incept(pre=pre, mpre=mpre, verfers=verfers, digers=digers)

        self.agency.incept(self.caid, pre)


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


class Initer(doing.Doer):
    def __init__(self, agentHab):
        self.agentHab = agentHab
        super(Initer, self).__init__()

    def recur(self, tyme):
        """ Prints Agent name and prefix """
        if not self.agentHab.inited:
            return False

        print("  Agent", self.agentHab.name, ":", self.agentHab.pre)
        return True


class GroupRequester(doing.Doer):

    def __init__(self, hby, agentHab, postman, counselor, groups):
        self.hby = hby
        self.agentHab = agentHab
        self.postman = postman
        self.counselor = counselor
        self.groups = groups

        super(GroupRequester, self).__init__()

    def recur(self, tyme):
        """ Checks cue for group proceccing requests and processes any with Counselor """
        if self.groups:
            msg = self.groups.popleft()
            serder = msg["serder"]
            sigers = msg["sigers"]

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
    def __init__(self, kvy, rvy, tvy, exc):
        self.kvy = kvy
        self.rvy = rvy
        self.tvy = tvy
        self.exc = exc

        super(Escrower, self).__init__()

    def recur(self, tyme):
        """ Process all escrows once per loop. """
        self.kvy.processEscrows()
        self.rvy.processEscrowReply()
        if self.tvy is not None:
            self.tvy.processEscrows()
        self.exc.processEscrow()

        return False


def loadEnds(app):
    opEnd = longrunning.OperationResourceEnd()
    app.add_route("/operations/{name}", opEnd)

    oobiEnd = OOBICollectionEnd()
    app.add_route("/oobis", oobiEnd)

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
            if "stem" not in salt:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "stem" missing from body.salt')
            stem = salt["stem"]

            if "pidx" not in salt:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "pidx" missing from body.salt')
            pidx = salt["pidx"]

            if "tier" not in salt:
                raise falcon.HTTPBadRequest(title="invalid inception",
                                            description=f'required field "tier" missing from body.salt')
            tier = salt["tier"]

            mgr = agent.remoteMgr.get(algo=Algos.salty)
            mgr.incept(agent.caid, verfers=ctrlHab.kever.verfers,
                       digers=ctrlHab.kever.digers,
                       pidx=pidx, ridx=0, kidx=0, stem=stem, tier=tier)

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

            mgr = agent.remoteMgr.get(algo=Algos.randy)
            mgr.incept(agent.caid, verfers=ctrlHab.kever.verfers,
                       digers=ctrlHab.kever.digers,
                       prxs=pris, nxts=nxts)

        elif Algos.group in body:
            raise falcon.HTTPBadRequest("multisig groups not supported as agent controller")

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
           - Ket Event Log
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
            raise falcon.HTTPBadRequest("required parameter 'pre' missing")

        pres = req.params.get("pre")
        pres = pres if isinstance(pres, list) else [pres]

        states = []
        for pre in pres:
            if pre not in agent.hby.kevers:
                continue

            kever = agent.hby.kevers[pre]
            states.append(kever.state().ked)

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
           - Ket Event Log
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
            raise falcon.HTTPBadRequest("required parameter 'pre' missing")

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
            agent.hby.db.oobis.pin(keys=(oobi,), val=obr)

        elif "rpy" in body:
            raise falcon.HTTPNotImplemented("'rpy' support not implemented yet")

        else:
            raise falcon.HTTPBadRequest("invalid OOBI request body, either 'rpy' or 'url' is required")

        oid = randomNonce()
        op = agent.monitor.submit(oid, longrunning.OpTypes.oobi, metadata=dict(oobi=oobi))

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")


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
