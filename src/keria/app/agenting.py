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
from keri.core import coring, parsing
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying, credentialing

from ..core.authing import Authenticater
from ..core import authing


def setup(name, base, bran, conAid, adminPort, configFile=None, configDir=None, httpPort=None):
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
    cagHby = habbing.Habery(name=name, base=base, bran=bran)

    # Create Agent AID if it does not already exist
    cagHab = cagHby.habByName(name)
    if cagHab is None:
        cagHab = cagHby.makeHab(name, transferable=True)
        print(f"Created Agent AID {cagHab.pre}")
    else:
        print(f"Loading Agent AID {cagHab.pre}")

    # Create the Hab for the Controller AIDs.
    conHby = habbing.Habery(name=conAid, base=base, cf=cf)
    doers = [habbing.HaberyDoer(habery=cagHby), habbing.HaberyDoer(habery=conHby)]

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agent=cagHab, caid=conAid)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*',
        expose_headers=['cesr-attachment', 'cesr-date', 'content-type', 'signature', 'signature-input']))
    app.add_middleware(authing.SignatureValidationComponent(authn=authn, allowed=["/boot"]))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    cues = decking.Deck()
    mbx = storing.Mailboxer(name=conHby.name)
    rep = storing.Respondant(hby=conHby, mbx=mbx)
    rgy = credentialing.Regery(hby=conHby, name=name, base=base)
    verifier = verifying.Verifier(hby=conHby, reger=rgy.reger)

    signaler = signaling.Signaler()
    notifier = notifying.Notifier(hby=conHby, signaler=signaler)
    issueHandler = protocoling.IssueHandler(hby=conHby, rgy=rgy, notifier=notifier)
    requestHandler = protocoling.PresentationRequestHandler(hby=conHby, notifier=notifier)
    applyHandler = protocoling.ApplyHandler(hby=conHby, rgy=rgy, verifier=verifier, name=conHby.name)
    proofHandler = protocoling.PresentationProofHandler(notifier=notifier)

    handlers = [issueHandler, requestHandler, proofHandler, applyHandler]
    exchanger = exchanging.Exchanger(db=conHby.db, handlers=handlers)
    mbd = indirecting.MailboxDirector(hby=conHby,
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

    doers += loadEnds(app=app, cagHab=cagHab, conHby=conHby, conAid=conAid)

    return doers


def loadEnds(app, cagHab, conHby, conAid):

    bootEnd = BootEnd(cagHab, conAid)
    app.add_route("/boot", bootEnd)

    habEnd = HabEnd(conHby)
    app.add_route("/aids", habEnd)

    return [bootEnd]


class BootEnd(doing.DoDoer):
    """ Resource class for creating datastore in cloud ahab """

    def __init__(self, ahab, caid):
        """ Provides endpoints for initializing and unlocking an agent

        Parameters:
            ahab (Hab): Hab for Signify Agent
            caid (str): qb64 of conAid AID

        """
        self.agent = ahab
        self.caid = caid
        doers = []
        super(BootEnd, self).__init__(doers=doers)

    def on_get(self, _, rep):
        """ GET endpoint for Keystores

        Get keystore status

        Args:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Query KERI environment for keystore name
        tags:
           - Boot
        parameters:
          - in: path
            name: name
            schema:
              type: string
            required: true
            description: predetermined name of keep keystore
            example: alice
        responses:
           202:
              description: Keystore exists
           404:
              description: No keystore exists

        """
        body = dict(aaid=self.agent.pre, caid=self.caid)

        rep.content_type = "application/json"
        rep.data = json.dumps(body).encode("utf-8")
        rep.status = falcon.HTTP_200

    def on_post(self, _, rep):
        """ Inception event POST endpoint

        Parameters:
            _ (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """
        if self.caid not in self.agent.kevers:
            rep.status = falcon.HTTP_417
            rep.data = json.dumps({'msg': f'system ahab AEID not loaded'}).encode("utf-8")
            return


class HabEnd:
    """ Resource class for creating and managing identifiers """

    def __init__(self, hby):
        """

        Parameters:
            hby (HAbery): Controller database and keystore environment
        """
        self.hby = hby
        pass

    def on_get(self, _, rep):
        """ Identifier GET endpoint

        Parameters:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary:  Get list of ahab identifiers
        description:  Get the list of identifiers associated with this ahab
        tags:
           - Identifiers
        responses:
            200:
              description: An array of Identifier key state information
              content:
                  application/json:
                    schema:
                        description: Key state information for current identifiers
                        type: array
                        items:
                           type: object
                           properties:
                              name:
                                 description: habitat local alias
                                 type: string
                              prefix:
                                 description: qualified base64 identifier prefix
                                 type: string
                              seq_no:
                                 description: current key event sequence number
                                 type: integer
                              delegated:
                                 description: Flag indicating whether this identifier is delegated
                                 type: boolean
                              delegator:
                                 description: qualified base64 identifier prefix of delegator
                                 type: string
                              witnesses:
                                 description: list of qualified base64 identfier prefixes of witnesses
                                 type: string
                              public_keys:
                                 description: list of current public keys
                                 type: array
                                 items:
                                    type: string
                              toad:
                                 description: Current witness threshold
                                 type: integer
                              isith:
                                 description: Current signing threshold
                                 type: string
                              receipts:
                                 description:  Count of witness receipts received for last key event
                                 type: integer
        """
        res = []

        for pre, hab in self.hby.habs.items():
            info = self.info(hab)
            res.append(info)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    def info(self, hab, dbing=None):
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

        if hab.accepted:
            kever = hab.kevers[hab.pre]
            ser = kever.serder
            dgkey = dbing.dgKey(ser.preb, ser.saidb)
            wigs = hab.db.getWigs(dgkey)
            data |= dict(
                seq_no=kever.sn,
                isith=kever.tholder.sith,
                public_keys=[verfer.qb64 for verfer in kever.verfers],
                nsith=kever.ntholder.sith,
                next_keys=kever.digs,  # this is misnamed these are not keys but digests of keys
                toad=kever.toader.num,
                witnesses=kever.wits,
                estOnly=kever.estOnly,
                DnD=kever.doNotDelegate,
                receipts=len(wigs)
            )

            if kever.delegated:
                data["delegated"] = kever.delegated
                data["delegator"] = kever.delegator
                dgkey = dbing.dgKey(hab.kever.prefixer.qb64b, hab.kever.lastEst.d)
                anchor = self.hby.db.getAes(dgkey)
                data["anchored"] = anchor is not None

        return data

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
            
            ipath = body.get("ipath")
            if ipath is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'ipath' missing from request"}).encode("utf-8")
                return
            
            npath = body.get("npath")
            if npath is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'npath' missing from request"}).encode("utf-8")
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

            temp = body.get("temp") == "true"
            serder = coring.Serder(ked=icp)
            sigers = [coring.Siger(qb64=sig) for sig in sigs]

            self.hby.makeSignifyHab(name, serder=serder, sigers=sigers, ipath=ipath, npath=npath, tier=tier,
                                    temp=temp)

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
