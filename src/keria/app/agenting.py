# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.agenting module

"""
import json
from urllib.parse import urlparse

import falcon
from falcon import media
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri import kering
from keri.app import configing, keeping, habbing, storing, signaling, notifying, oobiing, agenting, delegating
from keri.app.indirecting import HttpEnd
from keri.core import coring, parsing, eventing, routing
from keri.core.coring import Ilks
from keri.db import dbing
from keri.db.basing import OobiRecord
from keri.help import helping
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying, credentialing
from keri.vdr.eventing import Tevery

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
    acf = None
    if configDir is not None:
        acf = configing.Configer(name=name,
                                 base="",
                                 headDirPath=configDir,
                                 temp=False,
                                 reopen=True,
                                 clear=False)

    # Create the Hab for the Agent with only 2 AIDs
    agentHby = habbing.Habery(name=name, base=base, bran=bran, cf=acf)

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
    rgy = credentialing.Regery(hby=ctrlHby, name=name, base=base)
    verifier = verifying.Verifier(hby=ctrlHby, reger=rgy.reger)

    witDoer = agenting.WitnessReceiptor(hby=ctrlHby)
    anchorer = delegating.Boatswain(hby=ctrlHby)

    signaler = signaling.Signaler()
    notifier = notifying.Notifier(hby=ctrlHby, signaler=signaler)
    issueHandler = protocoling.IssueHandler(hby=ctrlHby, rgy=rgy, notifier=notifier)
    requestHandler = protocoling.PresentationRequestHandler(hby=ctrlHby, notifier=notifier)
    applyHandler = protocoling.ApplyHandler(hby=ctrlHby, rgy=rgy, verifier=verifier, name=ctrlHby.name)
    proofHandler = protocoling.PresentationProofHandler(notifier=notifier)

    handlers = [issueHandler, requestHandler, proofHandler, applyHandler]
    exchanger = exchanging.Exchanger(db=ctrlHby.db, handlers=handlers)

    adminServer = http.Server(port=adminPort, app=app)
    adminServerDoer = http.ServerDoer(server=adminServer)
    oobiery = oobiing.Oobiery(hby=ctrlHby)
    doers.extend([exchanger, adminServerDoer, witDoer, anchorer, *oobiery.doers])

    if httpPort is not None:
        rvy = routing.Revery(db=ctrlHby.db, cues=cues)
        kvy = eventing.Kevery(db=ctrlHby.db,
                              lax=True,
                              local=False,
                              rvy=rvy,
                              cues=cues)
        kvy.registerReplyRoutes(router=rvy.rtr)

        tvy = Tevery(reger=verifier.reger,
                     db=ctrlHby.db,
                     local=False,
                     cues=cues)

        tvy.registerReplyRoutes(router=rvy.rtr)
        parser = parsing.Parser(framed=True,
                                kvy=kvy,
                                tvy=tvy,
                                exc=exchanger,
                                rvy=rvy)

        httpEnd = HttpEnd(rxbs=parser.ims, mbx=mbx)
        app.add_route("/", httpEnd)

        server = http.Server(port=httpPort, app=app)
        httpServerDoer = http.ServerDoer(server=server)
        doers.append(httpServerDoer)

    doers += loadEnds(app=app, agentHby=agentHby, agentHab=agentHab, ctrlHby=ctrlHby, ctrlAid=ctrlAid,
                      witners=witDoer.msgs, anchors=anchorer.msgs)

    return doers


def loadEnds(app, agentHby, agentHab, ctrlHby, ctrlAid, witners, anchors):
    bootEnd = BootEnd(agentHby, agentHab, ctrlHby, ctrlAid)
    app.add_route("/boot", bootEnd)

    aidsEnd = IdentifierCollectionEnd(ctrlHby, witners=witners, anchors=anchors)
    app.add_route("/identifiers", aidsEnd)
    aidEnd = IdentifierResourceEnd(ctrlHby, witners=witners, anchors=anchors)
    app.add_route("/identifiers/{name}", aidEnd)
    aidOOBIsEnd = IdentifierOOBICollectionEnd(ctrlHby)
    app.add_route("/identifiers/{name}/oobis", aidOOBIsEnd)

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

    def __init__(self, hby, witners, anchors):
        """

        Parameters:
            hby (Habery): Controller database and keystore environment
        """
        self.hby = hby
        self.witners = witners
        self.anchors = anchors
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
                raise falcon.HTTPBadRequest(title=f"required field 'icp' missing from request")

            name = body.get("name")
            if name is None:
                raise falcon.HTTPBadRequest(title=f"required field 'name' missing from request")

            stem = body.get("stem")
            if stem is None:
                raise falcon.HTTPBadRequest(title=f"required field 'stem' missing from request")

            pidx = body.get("pidx")
            if pidx is None:
                raise falcon.HTTPBadRequest(title=f"required field 'pidx' missing from request")

            sigs = body.get("sigs")
            if sigs is None or len(sigs) == 0:
                raise falcon.HTTPBadRequest(title=f"required field 'sigs' missing from request")

            tier = body.get("tier")
            if tier not in coring.Tiers:
                raise falcon.HTTPBadRequest(title=f"required field 'tier' missing from request")

            temp = body.get("temp")
            serder = coring.Serder(ked=icp)
            sigers = [coring.Siger(qb64=sig) for sig in sigs]

            hab = self.hby.makeSignifyHab(name, serder=serder, sigers=sigers, pidx=pidx, stem=stem, tier=tier,
                                          temp=temp)

            rpy = body.get("rpy")
            if rpy is not None:
                rserder = coring.Serder(ked=rpy)
                rsigs = body.get("rsigs")
                rsigers = [coring.Siger(qb64=rsig) for rsig in rsigs]
                tsg = (hab.kever.prefixer, coring.Seqner(sn=hab.kever.sn), hab.kever.serder.saider, rsigers)
                self.hby.rvy.processReply(rserder, tsgs=[tsg])

            msgs = bytearray()
            for (_, erole, eid), end in hab.db.ends.getItemIter(keys=(hab.pre,)):
                if end.enabled or end.allowed:
                    msgs.extend(hab.loadLocScheme(eid=eid))

            if hab.kever.delegator:
                self.anchors.append(dict(alias=name, pre=hab.pre, sn=0))
                # TODO: return long running operation

            if hab.kever.wits:
                self.witners.append(dict(pre=hab.pre))
                # TODO: return long running operation

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]


class IdentifierResourceEnd:
    """ Resource class for updating and deleting identifiers """

    def __init__(self, hby, witners, anchors):
        """

        Parameters:
            hby (Habery): Controller database and keystore environment
        """
        self.hby = hby
        self.witners = witners
        self.anchors = anchors

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
            raise falcon.HTTPNotFound(title=f"No AID with name {name} found")

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

        if hab.kever.delegator:
            self.anchors.append(dict(alias=name, pre=hab.pre, sn=0))
            # TODO: return long running operation

        if hab.kever.wits:
            self.witners.append(dict(pre=hab.pre))
            # TODO: return long running operation

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

        if hab.kever.wits:
            self.witners.append(dict(pre=hab.pre))
            # TODO: return long running operation

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
        dgkey = dbing.dgKey(kever.prefixer.qb64b, kever.serder.saidb)
        wigs = hab.db.getWigs(dgkey)
        data["windexes"] = [coring.Siger(qb64b=bytes(wig)).index for wig in wigs]

    return data


class IdentifierOOBICollectionEnd:
    """
      This class represents the OOBI subresource collection endpoint for Identfiiers

    """

    def __init__(self, hby):
        """  Initialize Identifier / OOBI subresource endpoint

        Parameters:
            hby (Habery): database environment for controller AIDs

        """
        self.hby = hby

    def on_get(self, req, rep, name):
        """ Identifier GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab to GET

        """

        hab = self.hby.habByName(name)
        if not hab:
            raise falcon.HTTPNotFound(f"invalid alias {name}")

        role = req.params["role"]

        res = dict(role=role)
        if role in (kering.Roles.witness,):  # Fetch URL OOBIs for all witnesses
            oobis = []
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http)
                if not urls:
                    raise falcon.HTTPNotFound(f"unable to query witness {wit}, no http endpoint")

                up = urlparse(urls[kering.Schemes.http])
                oobis.append(f"http://{up.hostname}:{up.port}/oobi/{hab.pre}/witness/{wit}")
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http)
            if not urls:
                raise falcon.HTTPNotFound(f"unable to query controller {hab.pre}, no http endpoint")

            up = urlparse(urls[kering.Schemes.http])
            oobis.append(f"http://{up.hostname}:{up.port}/oobi/{hab.pre}/controller")
            res["oobis"] = oobis
        else:
            rep.status = falcon.HTTP_404
            return

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")


class OOBICollectionEnd:

    def __init__(self, hby):
        self.hby = hby


class OOBIResourceEnd:

    def __init__(self, hby):
        self.hby = hby

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

        elif "rpy" in body:
            raise falcon.HTTPNotImplemented("'rpy' support not implemented yet")

        else:
            raise falcon.HTTPBadRequest("invalid OOBI request body, either 'rpy' or 'url' is required")

        rep.status = falcon.HTTP_202
