# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.credentialing module

services and endpoint for ACDC credential managements
"""
import json

import falcon
from keri import kering
from keri.app import signing
from keri.app.habbing import SignifyGroupHab
from keri.core import coring, scheming, parsing
from keri.core.eventing import proofize, SealEvent
from keri.db import dbing
from keri.vc import proving, protocoling

from keria.core import httping, longrunning


def loadEnds(app, identifierResource):
    schemaColEnd = SchemaCollectionEnd()
    app.add_route("/schema", schemaColEnd)
    schemaResEnd = SchemaResourceEnd()
    app.add_route("/schema/{said}", schemaResEnd)

    registryEnd = RegistryCollectionEnd(identifierResource)
    app.add_route("/identifiers/{name}/registries", registryEnd)

    credentialCollectionEnd = CredentialCollectionEnd(identifierResource)
    app.add_route("/identifiers/{name}/credentials", credentialCollectionEnd)
    
    credentialResourceEnd = CredentialResourceEnd(identifierResource)
    app.add_route("/identifiers/{name}/credentials/{said}", credentialResourceEnd)

    queryCollectionEnd = CredentialQueryCollectionEnd()
    app.add_route("/identifiers/{name}/credentials/query", queryCollectionEnd)


class RegistryCollectionEnd:
    """
    ReST API for admin of credential issuance and revocation registries

    """

    def __init__(self, identifierResource):
        """

        Parameters:
            identifierResource (IdentifierResourceEnd): endpoint class for creating rotation and interaction events

        """
        self.identifierResource = identifierResource

    @staticmethod
    def on_get(req, rep, name):
        """  Registries GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for AID

        ---
        summary: List credential issuance and revocation registies
        description: List credential issuance and revocation registies
        tags:
           - Registries
        responses:
           200:
              description:  array of current credential issuance and revocation registies

        """
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identfier")

        res = []
        for name, registry in agent.rgy.regs.items():
            if registry.hab.pre == hab.pre:
                rd = dict(
                    name=registry.name,
                    regk=registry.regk,
                    pre=registry.hab.pre,
                    state=registry.tever.state().ked
                )
                res.append(rd)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    def on_post(self, req, rep, name):
        """  Registries POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): AID of Hab to load credentials for

        ---
        summary: Request to create a credential issuance and revocation registry
        description: Request to create a credential issuance and revocation registry
        tags:
           - Registries
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    name:
                      type: string
                      description: name of the new registry
                    alias:
                      type: string
                      description: name of identifier to associate as the issuer of the new credential registry
                    toad:
                      type: integer
                      description: Backer receipt threshold
                    nonce:
                      type: string
                      description: qb64 encoded ed25519 random seed for registry
                    noBackers:
                      type: boolean
                      required: False
                      description: True means to not allow seperate backers from identifier's witnesses.
                    baks:
                      type: array
                      items:
                         type: string
                      description: List of qb64 AIDs of witnesses to be used for the new group identfier.
                    estOnly:
                      type: boolean
                      required: false
                      default: false
                      description: True means to not allow interaction events to anchor credential events.
        responses:
           202:
              description:  registry inception request has been submitted

        """
        agent = req.context.agent
        body = req.get_media()

        rname = httping.getRequiredParam(body, "name")
        ked = httping.getRequiredParam(body, "vcp")
        vcp = coring.Serder(ked=ked)

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="alias is not a valid reference to an identfier")

        registry = agent.rgy.makeSignifyRegistry(name=rname, prefix=hab.pre, regser=vcp)
        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        anchor = dict(i=registry.regk, s="0", d=registry.regk)
        # Create registry long running OP that embeds the above received OP or Serder.

        agent.registrar.incept(hab, registry)
        op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.registry,
                                  metadata=dict(anchor=anchor, depends=op))

        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class SchemaResourceEnd:

    @staticmethod
    def on_get(req, rep, said):
        """ Schema GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said: qb64 self-addressing identifier of schema to load

       ---
        summary:  Get schema JSON of specified schema
        description:  Get schema JSON of specified schema
        tags:
           - Schema
        parameters:
          - in: path
            name: said
            schema:
              type: string
            required: true
            description: qb64 self-addressing identifier of schema to get
        responses:
           200:
              description: Schema JSON successfully returned
           404:
              description: No schema found for SAID
        """
        agent = req.context.agent
        schemer = agent.hby.db.schema.get(keys=(said,))
        if schemer is None:
            raise falcon.HTTPNotFound(description="Schema not found")

        data = schemer.sed
        rep.status = falcon.HTTP_200
        rep.data = json.dumps(data).encode("utf-8")


class SchemaCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """ Schema GET plural endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

       ---
        summary:  Get schema JSON of all schema
        description:  Get schema JSON of all schema
        tags:
           - Schema
        responses:
           200:
              description: Array of all schema JSON
        """
        agent = req.context.agent

        data = []
        for said, schemer in agent.hby.db.schema.getItemIter():
            data.append(schemer.sed)

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(data).encode("utf-8")


class CredentialQueryCollectionEnd:
    """ This class provides a collection endpoint for creating credential queries.

    I fully admit that the semantics here are a big stretch.  I would rather have this as a GET against the
    credential collection endpoint, but the nature of the complicated input to this endpoint dictate a BODY
    and certain client libraries (and possibly reverse proxies) don't support a BODY in a GET request.  So
    I'm moving the credential query code to this endpoint class and mapping to `.../credentials/queries` and
    making it a post against that path and calling it "creating a creaential query".  Meh.

    """

    @staticmethod
    def on_post(req, rep, name):
        """ Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable alias for AID to use as issuer

        ---
        summary:  List credentials in credential store (wallet)
        description: List issued or received credentials current verified
        tags:
           - Credentials
        parameters:
           - in: path
             name: aid
             schema:
               type: string
             required: true
             description: identifier to load credentials for
           - in: query
             name: type
             schema:
                type: string
             description:  type of credential to return, [issued|received]
             required: true
           - in: query
             name: schema
             schema:
                type: string
             description:  schema to filter by if provided
             required: false
        responses:
           200:
              description: Credential list.
              content:
                  application/json:
                    schema:
                        description: Credentials
                        type: array
                        items:
                           type: object

        """
        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identfier")

        try:
            body = req.get_media()
            if "filter" in body:
                filtr = body["filter"]
            else:
                filtr = {}

            if "sort" in body:
                sort = body["sort"]
            else:
                sort = None

            if "skip" in body:
                skip = body["skip"]
            else:
                skip = 0

            if "limit" in body:
                limit = body["limit"]
            else:
                limit = 25
        except falcon.HTTPError:
            filtr = {}
            sort = {}
            skip = 0
            limit = 25

        cur = agent.seeker.find(filtr=filtr, sort=sort, skip=skip, limit=limit)
        saids = [coring.Saider(qb64=said) for said in cur]
        creds = agent.rgy.reger.cloneCreds(saids=saids)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(creds).encode("utf-8")


class CredentialCollectionEnd:

    def __init__(self, identifierResource):
        """

        Parameters:
            identifierResource (IdentifierResourceEnd): endpoint class for creating rotation and interaction events

        """
        self.identifierResource = identifierResource

    def on_post(self, req, rep, name):
        """ Initiate a credential issuance

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable alias for AID to use as issuer

        ---
        summary: Perform credential issuance
        description: Perform credential issuance
        tags:
           - Credentials
        parameters:
          - in: path
            name: alias
            schema:
              type: string
            required: true
            description: Human readable alias for the identifier to create
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    registry:
                      type: string
                      description: Alias of credential issuance/revocation registry (aka status)
                    recipient:
                      type: string
                      description: AID of credential issuance/revocation recipient
                    schema:
                      type: string
                      description: SAID of credential schema being issued
                    rules:
                      type: object
                      description: Rules section (Ricardian contract) for credential being issued
                    source:
                      type: object
                      description: ACDC edge or edge group for chained credentials
                      properties:
                         d:
                            type: string
                            description: SAID of reference chain
                         s:
                            type: string
                            description: SAID of reference chain schema
                    credentialData:
                      type: object
                      description: dynamic map of values specific to the schema
                    private:
                      type: boolean
                      description: flag to inidicate this credential should support privacy preserving presentations
        responses:
           200:
              description: Credential issued.
              content:
                  application/json:
                    schema:
                        description: Credential
                        type: object

        """
        agent = req.context.agent

        body = req.get_media()
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identfier")

        creder = proving.Creder(ked=httping.getRequiredParam(body, "cred"))
        csigers = [coring.Siger(qb64=sig) for sig in httping.getRequiredParam(body, "csigs")]
        pather = coring.Pather(qb64=httping.getRequiredParam(body, "path"))
        iserder = coring.Serder(ked=httping.getRequiredParam(body, "iss"))

        regk = iserder.ked['ri']
        if regk not in agent.rgy.tevers:
            raise falcon.HTTPNotFound(description=f"issue against invalid registry SAID {regk}")

        sadsigers = signPaths(hab, pather=pather, sigers=csigers)

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        try:
            agent.credentialer.validate(creder)
            agent.registrar.issue(regk, iserder)
            agent.credentialer.issue(creder=creder, sadsigers=sadsigers)
            op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.credential,
                                      metadata=dict(ced=creder.ked, depends=op))

        except kering.ConfigurationError as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
            return

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")


class CredentialResourceEnd:
    def __init__(self, identifierResource):
        """

        Parameters:
            identifierResource (IdentifierResourceEnd): endpoint class for creating rotation and interaction events

        """
        self.identifierResource = identifierResource

    @staticmethod
    def on_get(req, rep, name, said):
        """ Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable alias for AID to use as issuer
            said (str): SAID of credential to export

        ---
        summary:  Export credential and all supporting cryptographic material
        description: Export credential and all supporting cryptographic material
        tags:
           - Credentials
        parameters:
           - in: path
             name: aid
             schema:
               type: string
             required: true
             description: The identifier to create
           - in: path
             name: said
             schema:
               type: string
             required: true
             description: SAID of credential to get
        responses:
           200:
              description: Credential export.
              content:
                  application/json+cesr:
                    schema:
                        description: Credential
                        type: object

        """
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identfier")

        accept = req.get_header("accept")
        if accept == "application/json+cesr":
            rep.content_type = "application/json+cesr"
            data = CredentialResourceEnd.outputCred(agent.hby, agent.rgy, said)
        else:
            rep.content_type = "application/json"
            creds = agent.rgy.reger.cloneCreds([coring.Saider(qb64=said)])
            if not creds:
                raise falcon.HTTPNotFound(description=f"credential for said {said} not found.")

            data = json.dumps(creds[0]).encode("utf-8")

        rep.status = falcon.HTTP_200
        rep.data = bytes(data)

    @staticmethod
    def outputCred(hby, rgy, said):
        out = bytearray()
        creder, sadsigers, sadcigars = rgy.reger.cloneCred(said=said)
        chains = creder.chains
        saids = []
        for key, source in chains.items():
            if key == 'd':
                continue

            if not isinstance(source, dict):
                continue

            saids.append(source['n'])

        for said in saids:
            out.extend(CredentialResourceEnd.outputCred(hby, rgy, said))

        issr = creder.issuer
        for msg in hby.db.clonePreIter(pre=issr):
            serder = coring.Serder(raw=msg)
            atc = msg[serder.size:]
            out.extend(serder.raw)
            out.extend(atc)

        if "i" in creder.subject:
            subj = creder.subject["i"]
            for msg in hby.db.clonePreIter(pre=subj):
                serder = coring.Serder(raw=msg)
                atc = msg[serder.size:]
                out.extend(serder.raw)
                out.extend(atc)

        if creder.status is not None:
            for msg in rgy.reger.clonePreIter(pre=creder.status):
                serder = coring.Serder(raw=msg)
                atc = msg[serder.size:]
                out.extend(serder.raw)
                out.extend(atc)

            for msg in rgy.reger.clonePreIter(pre=creder.said):
                serder = coring.Serder(raw=msg)
                atc = msg[serder.size:]
                out.extend(serder.raw)
                out.extend(atc)

        out.extend(creder.raw)
        out.extend(proofize(sadtsgs=sadsigers, sadcigars=sadcigars, pipelined=True))

        return out
    
    def on_delete(self, req, rep, name, said):
        """ Initiate a credential revocation

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable alias for AID to use as issuer
            said (str): SAID of credential to revoke

        RequestBody:
            rev (str): serialized revocation event
            ixn (str): serialized interaction event
            rot (str): serialized rotation event
            sigs (list): list of signatures for the revocation event
        ---
        summary: Perform credential revocation
        description: Perform credential revocation
        """

        agent = req.context.agent

        body = req.get_media()
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identfier")

        rserder = coring.Serder(ked=httping.getRequiredParam(body, "rev"))

        regk = rserder.ked['ri']
        if regk not in agent.rgy.tevers:
            raise falcon.HTTPNotFound(description=f"revocation against invalid registry SAID {regk}")
        
        try:
            agent.rgy.reger.cloneCreds([coring.Saider(qb64=said)])
        except:
            raise falcon.HTTPNotFound(description=f"credential for said {said} not found.")

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        try:
            agent.registrar.revoke(regk, rserder)
        except:
            raise falcon.HTTPBadRequest(description=f"invalid revocation event.")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")

def signPaths(hab, pather, sigers):
    """ Sign the SAD or SAIDs with the keys from the Habitat.

    Sign the SADs or SAIDs of the SADs as identified by the paths.

    Parameters:
        hab (Habitat): environment used to sign the SAD
        pather (Pather): Pather for the signatures
        sigers (list): list of signatures over the paths

    Returns:
        list: pathed signature tuples

    """

    sadsigers = []

    prefixer, seqner, saider, indices = signing.transSeal(hab)
    sadsigers.append((pather, prefixer, seqner, saider, sigers))

    return sadsigers


class Registrar:

    def __init__(self, agentHab, hby, rgy, counselor, witDoer, witPub, postman, verifier):
        self.hby = hby
        self.agentHab = agentHab
        self.rgy = rgy
        self.counselor = counselor
        self.witDoer = witDoer
        self.witPub = witPub
        self.postman = postman
        self.verifier = verifier

    def incept(self, hab, registry, prefixer=None, seqner=None, saider=None):
        """

        Parameters:
            hab (Hab): human readable name for the registry
            registry (SignifyRegistry): qb64 identifier prefix of issuing identifier in control of this registry
            prefixer (Prefixer):
            seqner (Seqner):
            saider (Saider):

        Returns:
            Registry:  created registry

        """
        rseq = coring.Seqner(sn=0)
        if not isinstance(hab, SignifyGroupHab):

            seqner = coring.Seqner(sn=hab.kever.sner.num)
            saider = hab.kever.serder.saider
            registry.anchorMsg(pre=registry.regk, regd=registry.regd, seqner=seqner, saider=saider)
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))
            self.rgy.reger.tpwe.add(keys=(registry.regk, rseq.qb64), val=(hab.kever.prefixer, seqner, saider))

        else:
            self.counselor.start(prefixer=prefixer, seqner=seqner, saider=saider, ghab=hab)

            print("Waiting for TEL registry vcp event mulisig anchoring event")
            self.rgy.reger.tmse.add(keys=(registry.regk, rseq.qb64, registry.regd), val=(prefixer, seqner, saider))

    def issue(self, regk, iserder):
        """
        Create and process the credential issuance TEL events on the given registry

        Parameters:
            regk (str): qb64 identifier prefix of the credential registry
            iserder (Serder): TEL issuance event

        """
        registry = self.rgy.regs[regk]
        registry.processEvent(serder=iserder)
        hab = registry.hab

        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        if not isinstance(hab, SignifyGroupHab):  # not a multisig group
            seqner = coring.Seqner(sn=hab.kever.sner.num)
            saider = hab.kever.serder.saider
            registry.anchorMsg(pre=vcid, regd=iserder.said, seqner=seqner, saider=saider)

            print("Waiting for TEL event witness receipts")
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))
            self.rgy.reger.tpwe.add(keys=(vcid, rseq.qb64), val=(hab.kever.prefixer, seqner, saider))
            return vcid, rseq.sn

        else:  # multisig group hab
            prefixer, seqner, saider = self.multisigIxn(hab, rseal)
            self.counselor.start(prefixer=prefixer, seqner=seqner, saider=saider, ghab=hab)

            print(f"Waiting for TEL iss event mulisig anchoring event {seqner.sn}")
            self.rgy.reger.tmse.add(keys=(vcid, rseq.qb64, iserder.said), val=(prefixer, seqner, saider))
            return vcid, rseq.sn

    def revoke(self, regk, rserder):
        """
        Create and process the credential revocation TEL events on the given registry

        Parameters:
            regk (str): qb64 identifier prefix of the credential registry
            rserder (Serder): TEL revocation event
        """
        registry = self.rgy.regs[regk]
        registry.processEvent(serder=rserder)
        hab = registry.hab

        vcid = rserder.ked["i"]
        rseq = coring.Seqner(snh=rserder.ked["s"])
        rseal = SealEvent(vcid, rseq.snh, rserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        if not isinstance(hab, SignifyGroupHab):

            seqner = coring.Seqner(sn=hab.kever.sner.num)
            saider = hab.kever.serder.saider
            registry.anchorMsg(pre=vcid, regd=rserder.said, seqner=seqner, saider=saider)

            print("Waiting for TEL event witness receipts")
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))

            self.rgy.reger.tpwe.add(keys=(vcid, rseq.qb64), val=(hab.kever.prefixer, seqner, saider))
            return vcid, rseq.sn
        else:
            prefixer, seqner, saider = self.multisigIxn(hab, rseal)
            self.counselor.start(prefixer=prefixer, seqner=seqner, saider=saider, ghab=hab)

            print(f"Waiting for TEL rev event mulisig anchoring event {seqner.sn}")
            self.rgy.reger.tmse.add(keys=(vcid, rseq.qb64, rserder.said), val=(prefixer, seqner, saider))
            return vcid, rseq.sn

    @staticmethod
    def multisigIxn(hab, rseal):
        ixn = hab.interact(data=[rseal])
        gserder = coring.Serder(raw=ixn)

        sn = gserder.sn
        said = gserder.said

        prefixer = coring.Prefixer(qb64=hab.pre)
        seqner = coring.Seqner(sn=sn)
        saider = coring.Saider(qb64=said)

        return prefixer, seqner, saider

    def complete(self, pre, sn=0):
        seqner = coring.Seqner(sn=sn)
        said = self.rgy.reger.ctel.get(keys=(pre, seqner.qb64))
        return said is not None

    def processEscrows(self):
        """
        Process credential registry anchors:

        """
        self.processWitnessEscrow()
        self.processMultisigEscrow()
        self.processDiseminationEscrow()

    def processWitnessEscrow(self):
        """
        Process escrow of group multisig events that do not have a full compliment of receipts
        from witnesses yet.  When receipting is complete, remove from escrow and cue up a message
        that the event is complete.

        """
        for (regk, snq), (prefixer, seqner, saider) in self.rgy.reger.tpwe.getItemIter():  # partial witness escrow
            kever = self.hby.kevers[prefixer.qb64]
            dgkey = dbing.dgKey(prefixer.qb64b, saider.qb64)

            # Load all the witness receipts we have so far
            wigs = self.hby.db.getWigs(dgkey)
            if kever.wits:
                if len(wigs) == len(kever.wits):  # We have all of them, this event is finished
                    hab = self.hby.habs[prefixer.qb64]
                    witnessed = False
                    for cue in self.witDoer.cues:
                        if cue["pre"] == hab.pre and cue["sn"] == seqner.sn:
                            witnessed = True

                    if not witnessed:
                        continue
                else:
                    continue

            rseq = coring.Seqner(qb64=snq)
            self.rgy.reger.tpwe.rem(keys=(regk, snq))

            self.rgy.reger.tede.add(keys=(regk, rseq.qb64), val=(prefixer, seqner, saider))

    def processMultisigEscrow(self):
        """
        Process escrow of group multisig events that do not have a full compliment of receipts
        from witnesses yet.  When receipting is complete, remove from escrow and cue up a message
        that the event is complete.

        """
        for (regk, snq, regd), (prefixer, seqner, saider) in self.rgy.reger.tmse.getItemIter():  # multisig escrow
            try:
                if not self.counselor.complete(prefixer, seqner, saider):
                    continue
            except kering.ValidationError:
                self.rgy.reger.tmse.rem(keys=(regk, snq, regd))
                continue

            rseq = coring.Seqner(qb64=snq)

            # Anchor the message, registry or otherwise
            key = dbing.dgKey(regk, regd)
            sealet = seqner.qb64b + saider.qb64b
            self.rgy.reger.putAnc(key, sealet)

            self.rgy.reger.tmse.rem(keys=(regk, snq, regd))
            self.rgy.reger.tede.add(keys=(regk, rseq.qb64), val=(prefixer, seqner, saider))

    def processDiseminationEscrow(self):
        for (regk, snq), (prefixer, seqner, saider) in self.rgy.reger.tede.getItemIter():  # group multisig escrow
            rseq = coring.Seqner(qb64=snq)
            dig = self.rgy.reger.getTel(key=dbing.snKey(pre=regk, sn=rseq.sn))
            if dig is None:
                continue

            self.rgy.reger.tede.rem(keys=(regk, snq))

            tevt = bytearray()
            for msg in self.rgy.reger.clonePreIter(pre=regk, fn=rseq.sn):
                tevt.extend(msg)

            print(f"Sending TEL events to witnesses")
            # Fire and forget the TEL event to the witnesses.  Consumers will have to query
            # to determine when the Witnesses have received the TEL events.
            self.witPub.msgs.append(dict(pre=prefixer.qb64, msg=tevt))
            self.rgy.reger.ctel.put(keys=(regk, rseq.qb64), val=saider)  # idempotent
            if rseq.sn == 1:
                print("Credential revocation completed, sending to recipients")
                revt = self.rgy.reger.getTvt(dbing.dgKey(pre=regk, dig=dig))
                rserder = coring.Serder(raw=bytes(revt))
                creder = self.rgy.reger.creds.get(keys=(rserder.ked["i"],))
                self.sendToRecipients(creder)

    def sendToRecipients(self, creder):
        issr = creder.issuer
        regk = creder.status
        if "i" in creder.subject:
            recp = creder.subject["i"]

            hab = self.hby.habs[issr]
            if isinstance(hab, SignifyGroupHab):
                sender = hab.mhab.pre
            else:
                sender = issr

            ikever = self.hby.db.kevers[issr]
            for msg in self.hby.db.cloneDelegation(ikever):
                serder = coring.Serder(raw=msg)
                atc = msg[serder.size:]
                self.postman.send(src=sender, dest=recp, topic="credential", serder=serder, attachment=atc)

            for msg in self.hby.db.clonePreIter(pre=issr):
                serder = coring.Serder(raw=msg)
                atc = msg[serder.size:]
                self.postman.send(src=sender, dest=recp, topic="credential", serder=serder, attachment=atc)

            if regk is not None:
                for msg in self.verifier.reger.clonePreIter(pre=regk):
                    serder = coring.Serder(raw=msg)
                    atc = msg[serder.size:]
                    self.postman.send(src=sender, dest=recp, topic="credential", serder=serder, attachment=atc)

            for msg in self.verifier.reger.clonePreIter(pre=creder.said):
                serder = coring.Serder(raw=msg)
                atc = msg[serder.size:]
                self.postman.send(src=sender, dest=recp, topic="credential", serder=serder, attachment=atc)

            sources = self.verifier.reger.sources(self.hby.db, creder)
            for source, atc in sources:
                regk = source.status
                vci = source.said

                issr = source.crd["i"]
                ikever = self.hby.db.kevers[issr]
                for msg in self.hby.db.cloneDelegation(ikever):
                    serder = coring.Serder(raw=msg)
                    atc = msg[serder.size:]
                    self.postman.send(src=sender, dest=recp, topic="credential", serder=serder, attachment=atc)

                for msg in self.hby.db.clonePreIter(pre=issr):
                    serder = coring.Serder(raw=msg)
                    atc = msg[serder.size:]
                    self.postman.send(src=sender, dest=recp, topic="credential", serder=serder,
                                    attachment=atc)

                for msg in self.verifier.reger.clonePreIter(pre=regk):
                    serder = coring.Serder(raw=msg)
                    atc = msg[serder.size:]
                    self.postman.send(src=sender, dest=recp, topic="credential", serder=serder, attachment=atc)

                for msg in self.verifier.reger.clonePreIter(pre=vci):
                    serder = coring.Serder(raw=msg)
                    atc = msg[serder.size:]
                    self.postman.send(src=sender, dest=recp, topic="credential", serder=serder,
                                    attachment=atc)

                serder, sadsigs, sadcigs = self.rgy.reger.cloneCred(source.said)
                atc = signing.provision(serder=source, sadcigars=sadcigs, sadsigers=sadsigs)
                del atc[:serder.size]
                self.postman.send(src=sender, dest=recp, topic="credential", serder=source, attachment=atc)

            serder, sadsigs, sadcigs = self.rgy.reger.cloneCred(creder.said)
            atc = signing.provision(serder=creder, sadcigars=sadcigs, sadsigers=sadsigs)
            del atc[:serder.size]
            self.postman.send(src=sender, dest=recp, topic="credential", serder=creder, attachment=atc)

            exn, atc = protocoling.credentialIssueExn(hab=self.agentHab, issuer=issr, schema=creder.schema, said=creder.said)
            self.postman.send(src=sender, dest=recp, topic="credential", serder=exn, attachment=atc)

            # Escrow until postman has successfully sent the notification
            self.rgy.reger.crse.put(keys=(exn.said,), val=creder)
        else:
            # Credential complete, mark it in the database
            self.rgy.reger.ccrd.put(keys=(creder.said,), val=creder)        


class Credentialer:

    def __init__(self, agentHab, hby, rgy, postman, registrar, verifier, notifier):
        self.agentHab = agentHab
        self.hby = hby
        self.rgy = rgy
        self.registrar = registrar
        self.verifier = verifier
        self.postman = postman
        self.notifier = notifier

    def validate(self, creder):
        """

        Args:
            creder (Creder): creder object representing the credential to validate

        Returns:
            bool: true if credential is valid against a known schema

        """
        schema = creder.crd['s']
        scraw = self.verifier.resolver.resolve(schema)
        if not scraw:
            raise kering.ConfigurationError("Credential schema {} not found.  It must be loaded with data oobi before "
                                            "issuing credentials".format(schema))

        schemer = scheming.Schemer(raw=scraw)
        try:
            schemer.verify(creder.raw)
        except kering.ValidationError as ex:
            raise kering.ConfigurationError(f"Credential schema validation failed for {schema}: {ex}")

        return True

    def issue(self, creder, sadsigers, smids=None):
        """ Issue the credential creder and handle witness propagation and communication

        Args:
            creder (Creder): Credential object to issue
            sadsigers (list): list of pathed signature tuples
            smids (list[str] | None): optional group signing member ids for multisig
                need to contributed current signing key
        """
        regk = creder.crd["ri"]
        registry = self.rgy.regs[regk]
        hab = registry.hab
        rseq = coring.Seqner(sn=0)

        craw = signing.provision(creder, sadsigers=sadsigers)
        atc = bytearray(craw[creder.size:])

        if isinstance(hab, SignifyGroupHab):
            smids.remove(hab.mhab.pre)

            print(f"Sending signed credential to {len(smids)} other participants")
            for recpt in smids:
                self.postman.send(src=hab.mhab.pre, dest=recpt, topic="multisig", serder=creder, attachment=atc)

            # escrow waiting for other signatures
            self.rgy.reger.cmse.put(keys=(creder.said, rseq.qb64), val=creder)
        else:
            # escrow waiting for registry anchors to be complete
            self.rgy.reger.crie.put(keys=(creder.said, rseq.qb64), val=creder)

        parsing.Parser().parse(ims=craw, vry=self.verifier)

    def processCredentialMissingSigEscrow(self):
        for (said, snq), creder in self.rgy.reger.cmse.getItemIter():
            rseq = coring.Seqner(qb64=snq)

            # Look for the saved saider
            saider = self.rgy.reger.saved.get(keys=said)
            if saider is None:
                continue

            # Remove from this escrow
            self.rgy.reger.cmse.rem(keys=(said, snq))

            hab = self.hby.habs[creder.issuer]
            kever = hab.kever
            # place in escrow to diseminate to other if witnesser and if there is an issuee
            self.rgy.reger.crie.put(keys=(creder.said, rseq.qb64), val=creder)

    def processCredentialIssuedEscrow(self):
        for (said, snq), creder in self.rgy.reger.crie.getItemIter():
            rseq = coring.Seqner(qb64=snq)

            if not self.registrar.complete(pre=said, sn=rseq.sn):
                continue

            saider = self.rgy.reger.saved.get(keys=said)
            if saider is None:
                continue

            print("Credential issuance complete, sending to recipient")
            self.registrar.sendToRecipients(creder)

            self.rgy.reger.crie.rem(keys=(said, snq))

    def processCredentialSentEscrow(self):
        """
        Process Poster cues to ensure that the last message (exn notification) has
        been sent before declaring the credential complete

        """
        for (said,), creder in self.rgy.reger.crse.getItemIter():
            found = False
            while self.postman.cues:
                cue = self.postman.cues.popleft()
                if cue["said"] == said:
                    found = True
                    break

            if found:
                self.rgy.reger.crse.rem(keys=(said,))
                self.rgy.reger.ccrd.put(keys=(creder.said,), val=creder)
                self.notifier.add(dict(
                    r=f"/credential/iss/complete",
                    a=dict(d=said),
                ))

    def complete(self, said):
        return self.rgy.reger.ccrd.get(keys=(said,)) is not None and len(self.postman.evts) == 0

    def processEscrows(self):
        """
        Process credential registry anchors:

        """
        self.processCredentialIssuedEscrow()
        self.processCredentialMissingSigEscrow()
        self.processCredentialSentEscrow()
