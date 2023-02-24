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
from keri import kering
from keri.app import configing, keeping, habbing, indirecting, storing, signaling, notifying
from keri.app.indirecting import HttpEnd
from keri.core import coring, parsing, eventing
from keri.core.coring import Ilks
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying, credentialing

from ..core.authing import Authenticater
from ..core import authing
from ..core.eventing import cloneAid


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
    agentHby = habbing.Habery(name=name, base=base, bran=bran)

    # Create Agent AID if it does not already exist
    agentHab = agentHby.habByName(name)
    if agentHab is None:
        agentHab = agentHby.makeHab(name, transferable=True, data=[ctrlAid])
        print(f"Created Agent AID {agentHab.pre}")
    else:
        print(f"Loading Agent AID {agentHab.pre}")

    # Create the Hab for the Controller AIDs.
    ctrlHby = habbing.Habery(name=ctrlAid, base=base, cf=cf)
    doers = [habbing.HaberyDoer(habery=agentHby), habbing.HaberyDoer(habery=ctrlHby)]

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agent=agentHab, ctrlAid=ctrlAid)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
    app.add_middleware(authing.SignatureValidationComponent(authn=authn, allowed=["/boot"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    cues = decking.Deck()
    mbx = storing.Mailboxer(name=ctrlHby.name)
    rep = storing.Respondant(hby=ctrlHby, mbx=mbx)
    rgy = credentialing.Regery(hby=ctrlHby, name=name, base=base)
    verifier = verifying.Verifier(hby=ctrlHby, reger=rgy.reger)

    signaler = signaling.Signaler()
    notifier = notifying.Notifier(hby=ctrlHby, signaler=signaler)
    issueHandler = protocoling.IssueHandler(hby=ctrlHby, rgy=rgy, notifier=notifier)
    requestHandler = protocoling.PresentationRequestHandler(hby=ctrlHby, notifier=notifier)
    applyHandler = protocoling.ApplyHandler(hby=ctrlHby, rgy=rgy, verifier=verifier, name=ctrlHby.name)
    proofHandler = protocoling.PresentationProofHandler(notifier=notifier)

    handlers = [issueHandler, requestHandler, proofHandler, applyHandler]
    exchanger = exchanging.Exchanger(db=ctrlHby.db, handlers=handlers)
    mbd = indirecting.MailboxDirector(hby=ctrlHby,
                                      exc=exchanger,
                                      verifier=verifier,
                                      rep=rep,
                                      topics=["/receipt", "/replay", "/multisig", "/credential", "/delegate",
                                              "/challenge", "/oobi"],
                                      cues=cues)

    adminServer = http.Server(port=adminPort, app=app)
    adminServerDoer = http.ServerDoer(server=adminServer)
    doers.extend([exchanger, mbd, rep, adminServerDoer])

    if httpPort is not None:
        parser = parsing.Parser(framed=True,
                                kvy=mbd.kvy,
                                tvy=mbd.tvy,
                                exc=exchanger,
                                rvy=mbd.rvy)

        httpEnd = HttpEnd(rxbs=parser.ims, mbx=mbx)
        app.add_route("/", httpEnd)

        server = http.Server(port=httpPort, app=app)
        httpServerDoer = http.ServerDoer(server=server)
        doers.append(httpServerDoer)

    doers += loadEnds(app=app, agentHby=agentHby, agentHab=agentHab, ctrlHby=ctrlHby, ctrlAid=ctrlAid)

    return doers


def loadEnds(app, agentHby, agentHab, ctrlHby, ctrlAid):

    bootEnd = BootEnd(agentHby, agentHab, ctrlHby, ctrlAid)
    app.add_route("/boot", bootEnd)

    idsEnd = IdentifierCollectionEnd(ctrlHby)
    app.add_route("/identifiers", idsEnd)
    idEnd = IdentifierResourceEnd(ctrlHby)
    app.add_route("/identifiers/{name}", idEnd)

    return [bootEnd]


class BootEnd(doing.DoDoer):
    """ Resource class for creating datastore in cloud ahab """

    def __init__(self, agentHby, agentHab, ctrlHby, ctrlAid):
        """ Provides endpoints for initializing and unlocking an agent

        Parameters:
            agentHby (Habery): Habery for Signify Agent
            agentHab (Hab): Hab for Signify Agent
            ctrlAid (str): qb64 of ctrlAid AID

        """
        self.authn = authing.Authenticater(agent=agentHab, ctrlAid=ctrlAid)
        self.agentHby = agentHby
        self.ctrlHby = ctrlHby
        self.agent = agentHab
        self.ctrlAid = ctrlAid
        doers = []
        super(BootEnd, self).__init__(doers=doers)

    def on_get(self, _, rep):
        """ GET endpoint for Keystores

        Get keystore status

        Args:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        """
        kel = cloneAid(db=self.agent.db, pre=self.agent.pre)
        pidx = self.ctrlHby.db.habs.cntAll()
        body = dict(kel=kel, pidx=pidx)

        if (ctrlHab := self.agentHby.habByName(self.ctrlAid)) is not None:
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

        if "stem" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "stem" missing from body')
        stem = body["stem"]

        if "pidx" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "pidx" missing from body')
        pidx = body["pidx"]

        if "tier" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "tier" missing from body')
        tier = body["tier"]

        if "temp" not in body:
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'required field "temp" missing from body')
        temp = body["temp"]

        ctrlHab = self.agentHby.makeSignifyHab(name=self.ctrlAid, serder=icp, sigers=[siger], stem=stem, pidx=pidx,
                                               tier=tier, temp=temp)

        if ctrlHab.pre != self.ctrlAid:
            self.agentHby.deleteHab(self.ctrlAid)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid icp event for ctrlAid {self.ctrlAid}')

        if not self.authn.verify(req):
            self.agentHby.deleteHab(self.ctrlAid)
            raise falcon.HTTPBadRequest(title="invalid inception",
                                        description=f'invalid signature on rquest')

        rep.status = falcon.HTTP_202


class IdentifierCollectionEnd:
    """ Resource class for creating and managing identifiers """

    def __init__(self, hby):
        """

        Parameters:
            hby (Habery): Controller database and keystore environment
        """
        self.hby = hby
        pass

    def on_get(self, _, rep):
        """ Identifier List GET endpoint

        Parameters:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        """
        res = []

        for pre, hab in self.hby.habs.items():
            data = info(hab)
            res.append(data)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    def on_post(self, req, rep):
        """ Inception event POST endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """
        try:
            body = req.get_media()
            icp = body.get("icp")
            if icp is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'icp' missing from request"}).encode("utf-8")
                return

            name = body.get("name")
            if name is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'name' missing from request"}).encode("utf-8")
                return
            
            stem = body.get("stem")
            if stem is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'stem' missing from request"}).encode("utf-8")
                return
            
            pidx = body.get("pidx")
            if pidx is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'pidx' missing from request"}).encode("utf-8")
                return
            
            sigs = body.get("sigs")
            if sigs is None or len(sigs) == 0:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'sigs' missing from request"}).encode("utf-8")
                return

            tier = body.get("tier")
            if tier not in coring.Tiers:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'tier' missing from request"}).encode("utf-8")
                return

            temp = body.get("temp")
            serder = coring.Serder(ked=icp)
            sigers = [coring.Siger(qb64=sig) for sig in sigs]

            self.hby.makeSignifyHab(name, serder=serder, sigers=sigers, pidx=pidx, stem=stem, tier=tier,
                                    temp=temp)

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]


class IdentifierResourceEnd:
    """ Resource class for updating and deleting identifiers """

    def __init__(self, hby):
        """

        Parameters:
            hby (Habery): Controller database and keystore environment
        """
        self.hby = hby
        pass

    def on_get(self, _, rep, name):
        """ Identifier GET endpoint

        Parameters:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab to GET

        """
        hab = self.hby.habByName(name)
        if hab is None:
            rep.status = falcon.HTTP_400
            return

        data = info(hab, full=True)
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(data).encode("utf-8")

    def on_put(self, req, rep, name):
        """ Identifier UPDATE endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object
            name (str): human readable name for Hab to rotate or interact

        """
        try:
            body = req.get_media()
            typ = Ilks.ixn if req.params.get("type") == "ixn" else Ilks.rot

            if typ in (Ilks.rot,):
                serder = self.rotate(name, body)
            else:
                serder = self.interact(name, body)

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            raise falcon.HTTPBadRequest(description=e.args[0])

    def rotate(self, name, body):
        hab = self.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID {name} found")

        rot = body.get("rot")
        if rot is None:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'rot' missing from request")

        sigs = body.get("sigs")
        if sigs is None or len(sigs) == 0:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'sigs' missing from request")

        serder = coring.Serder(ked=rot)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        hab.rotate(serder=serder, sigers=sigers, )

        return serder

    def interact(self, name, body):
        hab = self.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID {name} found")

        ixn = body.get("ixn")
        if ixn is None:
            raise falcon.HTTPBadRequest(title="invalid interaction",
                                        description=f"required field 'ixn' missing from request")

        sigs = body.get("sigs")
        if sigs is None or len(sigs) == 0:
            raise falcon.HTTPBadRequest(title="invalid interaction",
                                        description=f"required field 'sigs' missing from request")

        serder = coring.Serder(ked=ixn)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        hab.interact(serder=serder, sigers=sigers)

        return serder


def info(hab, full=False):
    data = dict(
        name=hab.name,
        prefix=hab.pre,
    )

    if isinstance(hab, habbing.GroupHab):
        data["group"] = dict(
            pid=hab.mhab.pre,
            aids=hab.smids,
            accepted=hab.accepted
        )
    elif isinstance(hab, habbing.SignifySaltyHab):
        data["stem"] = hab.stem
        data["pidx"] = hab.pidx
        data["tier"] = hab.tier
        data["temp"] = hab.temp

    if hab.accepted and full:
        kever = hab.kevers[hab.pre]
        data["state"] = kever.state().ked

    return data
