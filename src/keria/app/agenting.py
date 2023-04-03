# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
import json

import falcon
from falcon import media
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri.app import configing, keeping, habbing, storing, signaling, notifying, oobiing, agenting, delegating
from keri.app.grouping import Counselor
from keri.app.indirecting import HttpEnd
from keri.app.keeping import Algos
from keri.core import coring, parsing, eventing, routing
from keri.core.coring import Ilks, randomNonce
from keri.db import dbing
from keri.db.basing import OobiRecord
from keri.end import ending
from keri.help import helping, ogler
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying, credentialing
from keri.vdr.eventing import Tevery

from . import grouping, aiding
from .keeping import RemoteManager
from ..core import authing, longrunning
from ..core.authing import Authenticater
from ..core.eventing import cloneAid

logger = ogler.getLogger()


def setup(name, base, bran, ctrlAid, adminPort, configFile=None, configDir=None, httpPort=None):
    """ Set up an ahab in Signify mode """
    ks = keeping.Keeper(name=name,
                        base=base,
                        temp=False,
                        reopen=True)

    aeid = ks.gbls.get('aeid')

    cf = None
    if aeid is None and configFile is not None:  # Load config file if creating database
        cf = configing.Configer(name=configFile,
                                base="",
                                headDirPath=configDir,
                                temp=False,
                                reopen=True,
                                clear=False)

    # Create the Hab for the Agent with only 2 AIDs
    agentHby = habbing.Habery(name=name, base=base, bran=bran, ks=ks, cf=cf)

    # Create the Hab for the Controller AIDs.
    doers = [habbing.HaberyDoer(habery=agentHby)]

    # Create Agent AID if it does not already exist
    agentHab = agentHby.habByName(name, ns="agent")
    if agentHab is None:
        print(f"Creating agent...")
        agentHab = agentHby.makeHab(name, ns="agent", transferable=True, data=[ctrlAid])
    else:
        print(f"Loading agent...")

    rgy = credentialing.Regery(hby=agentHby, name=name, base=base)
    swain = delegating.Boatswain(hby=agentHby)
    counselor = Counselor(hby=agentHby)

    mon = longrunning.Monitor(hby=agentHby, swain=swain, counselor=counselor)

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agent=agentHab, ctrlAid=ctrlAid)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
    app.add_middleware(authing.SignatureValidationComponent(authn=authn, allowed=["/boot"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    adminServer = http.Server(port=adminPort, app=app)
    adminServerDoer = http.ServerDoer(server=adminServer)
    oobiery = oobiing.Oobiery(hby=agentHby)
    agentOobiery = oobiing.Oobiery(hby=agentHby)

    agent = Agenter(hby=agentHby,
                    hab=agentHab,
                    rgy=rgy,
                    counselor=counselor,
                    swain=swain,
                    httpPort=httpPort)

    doers.extend([adminServerDoer, agent, swain, counselor, *oobiery.doers, *agentOobiery.doers])
    loadEnds(app=app, agentHby=agentHby, agentHab=agentHab, ctrlAid=ctrlAid, monitor=mon)
    aiding.loadEnds(app=app, hby=agentHby, monitor=mon, groups=agent.groups, witners=agent.witners,
                    anchors=agent.anchors)
    grouping.loadEnds(app=app, agentHby=agentHby)

    return doers


class Agenter(doing.DoDoer):
    """ Doer to print witness prefix after initialization

    """

    def __init__(self, hby, hab, rgy, swain, counselor, cues=None, httpPort=None, **opts):
        self.agentHab = hab
        self.hby = hby
        self.swain = swain
        self.counselor = counselor
        self.cues = cues if cues is not None else decking.Deck()
        self.groups = decking.Deck()
        self.anchors = decking.Deck()
        self.witners = decking.Deck()
        self.receiptor = agenting.Receiptor(hby=hby)

        doers = [doing.doify(self.start), doing.doify(self.msgDo), doing.doify(self.escrowDo), doing.doify(self.witDo),
                 doing.doify(self.anchorDo), doing.doify(self.groupDo), self.receiptor]

        if httpPort is not None:
            verifier = verifying.Verifier(hby=hby, reger=rgy.reger)

            signaler = signaling.Signaler()
            notifier = notifying.Notifier(hby=hby, signaler=signaler)
            issueHandler = protocoling.IssueHandler(hby=hby, rgy=rgy, notifier=notifier)
            requestHandler = protocoling.PresentationRequestHandler(hby=hby, notifier=notifier)
            applyHandler = protocoling.ApplyHandler(hby=hby, rgy=rgy, verifier=verifier, name=hab.name)
            proofHandler = protocoling.PresentationProofHandler(notifier=notifier)

            handlers = [issueHandler, requestHandler, proofHandler, applyHandler]
            self.exc = exchanging.Exchanger(db=hby.db, handlers=handlers)

            mbx = storing.Mailboxer(name=hby.name)
            self.rvy = routing.Revery(db=hby.db, cues=cues)
            self.kvy = eventing.Kevery(db=hby.db,
                                       lax=True,
                                       local=False,
                                       rvy=self.rvy,
                                       cues=cues)
            self.kvy.registerReplyRoutes(router=self.rvy.rtr)

            self.tvy = Tevery(reger=verifier.reger,
                              db=hby.db,
                              local=False,
                              cues=cues)

            self.tvy.registerReplyRoutes(router=self.rvy.rtr)
            self.parser = parsing.Parser(framed=True,
                                         kvy=self.kvy,
                                         tvy=self.tvy,
                                         exc=self.exc,
                                         rvy=self.rvy)

            happ = falcon.App(middleware=falcon.CORSMiddleware(
                allow_origins='*', allow_credentials='*',
                expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
            happ.req_options.media_handlers.update(media.Handlers())
            happ.resp_options.media_handlers.update(media.Handlers())

            ending.loadEnds(app=happ, hby=self.hby, default=self.agentHab.pre)
            httpEnd = HttpEnd(rxbs=self.parser.ims, mbx=mbx)
            happ.add_route("/", httpEnd)

            server = http.Server(port=httpPort, app=happ)
            httpServerDoer = http.ServerDoer(server=server)
            doers.append(httpServerDoer)

        super().__init__(doers=doers, **opts)

    def start(self, tymth=None, tock=0.0):
        """ Prints witness name and prefix

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while not self.agentHab.inited:
            yield self.tock

        print("  Agent", self.agentHab.name, ":", self.agentHab.pre)

    def msgDo(self, tymth=None, tock=0.0):
        """
        Returns doifiable Doist compatibile generator method (doer dog) to process
            incoming message stream of .kevery

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        if self.parser.ims:
            logger.info("Agent %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator()  # process messages continuously
        return done  # should nover get here except forced close

    def escrowDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery and .tevery escrows.

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            self.kvy.processEscrows()
            self.rvy.processEscrowReply()
            if self.tvy is not None:
                self.tvy.processEscrows()
            self.exc.processEscrow()

            yield

    def witDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery and .tevery escrows.

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.witners:
                msg = self.witners.popleft()
                serder = msg["serder"]

                # If we are a rotation event, may need to catch new witnesses up to current key state
                if serder.ked['t'] in (Ilks.rot,):
                    adds = serder.ked["ba"]
                    for wit in adds:
                        print(f"catching up {wit}")
                        yield from self.receiptor.catchup(serder.pre, wit)

                yield from self.receiptor.receipt(serder.pre, serder.sn)

            yield self.tock

    def anchorDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            delegation anchor requests

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.anchors:
                msg = self.anchors.popleft()
                sn = msg["sn"] if "sn" in msg else None
                self.swain.delegation(pre=msg["pre"], sn=sn, proxy=self.agentHab)

            yield self.tock

    def groupDo(self, tymth=None, tock=0.0):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            delegation anchor requests

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.groups:
                msg = self.groups.popleft()
                pre = msg['pre']
                sn = msg['sn']
                said = msg['d']
                smids = msg['smids']
                rmids = msg['rmids']

                prefixer = coring.Prefixer(qb64=pre)
                seqner = coring.Seqner(sn=sn)
                saider = coring.Saider(qb64=said)
                ghab = self.hby.habs[pre]
                self.counselor.start(ghab=ghab, prefixer=prefixer, seqner=seqner, saider=saider, smids=smids,
                                     rmids=rmids, proxy=self.agentHab)

            yield self.tock


def loadEnds(app, agentHby, agentHab, ctrlAid, monitor):
    bootEnd = BootEnd(agentHby, agentHab, ctrlAid)
    app.add_route("/boot", bootEnd)

    opEnd = longrunning.OperationResourceEnd(monitor=monitor)
    app.add_route("/operations/{name}", opEnd)

    oobiEnd = OOBICollectionEnd(hby=agentHby, monitor=monitor, agent=agentHby)
    app.add_route("/oobis", oobiEnd)

    statesEnd = KeyStateCollectionEnd(hby=agentHby)
    app.add_route("/states", statesEnd)

    eventsEnd = KeyEventCollectionEnd(hby=agentHby)
    app.add_route("/events", eventsEnd)


class BootEnd:
    """ Resource class for creating datastore in cloud ahab """

    def __init__(self, agentHby, agentHab, ctrlAid, rm=None):
        """ Provides endpoints for initializing and unlocking an agent

        Parameters:
            agentHby (Habery): Habery for Signify Agent
            agentHab (Hab): Hab for Signify Agent
            ctrlAid (str): qb64 of ctrlAid AID

        """
        self.authn = authing.Authenticater(agent=agentHab, ctrlAid=ctrlAid)
        self.agentHby = agentHby
        self.agent = agentHab
        self.ctrlAid = ctrlAid
        self.rm = rm if rm is not None else RemoteManager(hby=agentHby)

    def on_get(self, _, rep):
        """ GET endpoint for Keystores

        Get keystore status

        Args:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        """
        kel = cloneAid(db=self.agent.db, pre=self.agent.pre)
        pidx = self.agentHby.db.habs.cntAll()
        body = dict(kel=kel, pidx=pidx)

        if (ctrlHab := self.agentHby.habByName(self.ctrlAid, ns="agent")) is not None:
            body["ridx"] = ctrlHab.kever.sn

        rep.content_type = "application/json"
        rep.data = json.dumps(body).encode("utf-8")
        rep.status = falcon.HTTP_200

    def on_post(self, req, rep):
        """ Inception event POST endpoint

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

        ctrlHab = self.agentHby.makeSignifyHab(name=self.ctrlAid, ns="agent", serder=icp, sigers=[siger])

        if ctrlHab.pre != self.ctrlAid:
            self.agentHby.deleteHab(self.ctrlAid)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid icp event for ctrlAid {self.ctrlAid}')

        if not self.authn.verify(req):
            self.agentHby.deleteHab(self.ctrlAid)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid signature on rquest')

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

            self.rm.incept(self.ctrlAid, algo=Algos.salty, verfers=ctrlHab.kever.verfers, digers=ctrlHab.kever.digers,
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

            self.rm.incept(self.ctrlAid, algo=Algos.randy, verfers=ctrlHab.kever.verfers, digers=ctrlHab.kever.digers,
                           prxs=pris, nxts=nxts)

        elif Algos.group in body:
            raise falcon.HTTPBadRequest("multisig groups not supported as agent controllers")

        rep.status = falcon.HTTP_202


class KeyStateCollectionEnd:

    def __init__(self, hby):
        self.hby = hby

    def on_get(self, req, rep):
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
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest("required parameter 'pre' missing")

        pres = req.params.get("pre")
        pres = pres if isinstance(pres, list) else [pres]

        states = []
        for pre in pres:
            if pre not in self.hby.kevers:
                continue

            kever = self.hby.kevers[pre]
            states.append(kever.state().ked)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(states).encode("utf-8")


class KeyEventCollectionEnd:

    def __init__(self, hby):
        self.hby = hby

    def on_get(self, req, rep):
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
        if "pre" not in req.params:
            raise falcon.HTTPBadRequest("required parameter 'pre' missing")

        pre = req.params.get("pre")
        preb = pre.encode("utf-8")
        events = []
        for fn, dig in self.hby.db.getFelItemPreIter(preb, fn=0):
            dgkey = dbing.dgKey(preb, dig)  # get message
            if not (raw := self.hby.db.getEvt(key=dgkey)):
                raise falcon.HTTPInternalServerError(f"Missing event for dig={dig}.")

            serder = coring.Serder(raw=bytes(raw))
            events.append(serder.ked)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(events).encode("utf-8")


class OOBICollectionEnd:

    def __init__(self, hby, agent, monitor):
        """ Create OOBI Collection endpoint instance

        Parameters:
            hby (Habery): Controller database and keystore environment
            agent (Habery): Agent database and keystore environment
            monitor (Monitor): Long running process monitor
        """

        self.hby = hby
        self.agent = agent
        self.mon = monitor

    def on_post(self, req, rep):
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
        body = req.get_media()

        if "url" in body:
            oobi = body["url"]
            dt = helping.nowUTC()

            obr = OobiRecord(date=helping.toIso8601(dt))
            if "oobialias" in body:
                obr.oobialias = body["oobialias"]

            self.hby.db.oobis.pin(keys=(oobi,), val=obr)
            self.agent.db.oobis.pin(keys=(oobi,), val=obr)

        elif "rpy" in body:
            raise falcon.HTTPNotImplemented("'rpy' support not implemented yet")

        else:
            raise falcon.HTTPBadRequest("invalid OOBI request body, either 'rpy' or 'url' is required")

        oid = randomNonce()
        op = self.mon.submit(oid, longrunning.OpTypes.oobi, metadata=dict(oobi=oobi))

        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")
