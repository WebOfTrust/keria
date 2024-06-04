# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.credentialing module

services and endpoint for ACDC credential managements
"""
import json
from dataclasses import asdict

import falcon
from keri import kering
from keri.app import signing
from keri.app.habbing import SignifyGroupHab
from keri.core import coring, scheming, serdering
from keri.db import dbing
from keri.db.dbing import dgKey
from keri.vdr import viring

from keria.core import httping, longrunning


def loadEnds(app, identifierResource):
    schemaColEnd = SchemaCollectionEnd()
    app.add_route("/schema", schemaColEnd)
    schemaResEnd = SchemaResourceEnd()
    app.add_route("/schema/{said}", schemaResEnd)

    registryEnd = RegistryCollectionEnd(identifierResource)
    app.add_route("/identifiers/{name}/registries", registryEnd)

    registryResEnd = RegistryResourceEnd()
    app.add_route("/identifiers/{name}/registries/{registryName}", registryResEnd)

    credentialCollectionEnd = CredentialCollectionEnd(identifierResource)
    app.add_route("/identifiers/{name}/credentials", credentialCollectionEnd)
    
    credentialResourceEnd = CredentialResourceEnd()
    app.add_route("/credentials/{said}", credentialResourceEnd)
    credentialResourceDelEnd = CredentialResourceDeleteEnd(identifierResource)
    app.add_route("/identifiers/{name}/credentials/{said}", credentialResourceDelEnd)

    queryCollectionEnd = CredentialQueryCollectionEnd()
    app.add_route("/credentials/query", queryCollectionEnd)


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
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identifier")

        res = []
        for name, registry in agent.rgy.regs.items():
            if registry.regk not in registry.tevers:  # defensive programming for a registry not being fully committed
                continue

            if registry.hab.pre == hab.pre:
                rd = dict(
                    name=registry.name,
                    regk=registry.regk,
                    pre=registry.hab.pre,
                    state=asdict(registry.tever.state())
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
                      description: List of qb64 AIDs of witnesses to be used for the new group identifier.
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
        vcp = serdering.SerderKERI(sad=ked)

        ked = httping.getRequiredParam(body, "ixn")
        ixn = serdering.SerderKERI(sad=ked)

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description="alias is not a valid reference to an identifier")

        if agent.rgy.registryByName(name=rname) is not None:
            raise falcon.HTTPBadRequest(description=f"registry name {rname} already in use")

        registry = agent.rgy.makeSignifyRegistry(name=rname, prefix=hab.pre, regser=vcp)

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        anchor = dict(i=registry.regk, s="0", d=registry.regk)
        # Create registry long running OP that embeds the above received OP or Serder.

        seqner = coring.Seqner(sn=ixn.sn)
        prefixer = coring.Prefixer(qb64=ixn.pre)
        agent.registrar.incept(hab, registry, prefixer=prefixer, seqner=seqner, saider=coring.Saider(qb64=ixn.said))
        op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.registry,
                                  metadata=dict(anchor=anchor, depends=op))

        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class RegistryResourceEnd:

    @staticmethod
    def on_get(req, rep, name, registryName):
        """  Registry Resource GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for AID
            registryName(str): human readable name for registry

        ---
        summary: Get a single credential issuance and revocation registy
        description: Get a single credential issuance and revocation registy
        tags:
           - Registries
        responses:
           200:
              description:  credential issuance and revocation registy

        """
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

        registry = agent.rgy.registryByName(registryName)
        if registry is None:
            raise falcon.HTTPNotFound(description=f"{registryName} is not a valid reference to a credential registry")

        if not registry.hab.pre == hab.pre:
            raise falcon.HTTPNotFound(description=f"{registryName} is not a valid registry for AID {name}")

        rd = dict(
            name=registry.name,
            regk=registry.regk,
            pre=registry.hab.pre,
            state=asdict(registry.tever.state())
        )
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(rd).encode("utf-8")

    @staticmethod
    def on_put(req, rep, name, registryName):
        """  Registry Resource PUT endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for AID
            registryName(str): human readable name for registry or its SAID

        ---
        summary: Get a single credential issuance and revocation registy
        description: Get a single credential issuance and revocation registy
        tags:
           - Registries
        responses:
           200:
              description:  credential issuance and revocation registy

        """
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

        body = req.get_media()
        if 'name' not in body:
            raise falcon.HTTPBadRequest(description="'name' is required in body")

        name = body['name']
        if agent.rgy.registryByName(name) is not None:
            raise falcon.HTTPBadRequest(description=f"{name} is already in use for a registry")

        registry = agent.rgy.registryByName(registryName)
        if registry is None:
            if registryName in agent.rgy.regs:  # Check to see if the registryName parameter is a SAID
                registry = agent.rgy.regs[registryName]
            else:
                regk = registryName
                key = dgKey(regk, regk)
                raw = agent.rgy.reger.getTvt(key=key)
                if raw is None:
                    raise falcon.HTTPNotFound(
                        description=f"{registryName} is not a valid reference to a credential registry")

                regser = serdering.SerderKERI(raw=bytes(raw))
                registry = agent.rgy.makeSignifyRegistry(name, hab.pre, regser)

        regord = viring.RegistryRecord(registryKey=registry.regk, prefix=hab.pre)
        agent.rgy.reger.regs.pin(keys=(name,), val=regord)
        agent.rgy.reger.regs.rem(keys=(registryName,))
        registry.name = name

        rd = dict(
            name=registry.name,
            regk=registry.regk,
            pre=registry.hab.pre,
            state=asdict(registry.tever.state())
        )
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(rd).encode("utf-8")


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
    def on_post(req, rep):
        """ Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary:  List credentials in credential store (wallet)
        description: List issued or received credentials current verified
        tags:
           - Credentials
        parameters:
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
        creds = agent.rgy.reger.cloneCreds(saids=saids, db=agent.hby.db)

        end = skip + (len(creds) - 1) if len(creds) > 0 else 0
        rep.set_header("Accept-Ranges", "credentials")
        rep.set_header("Content-Range", f"credentials {skip}-{end}/{limit}")

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
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identifier")
        try: 
            creder = serdering.SerderACDC(sad=httping.getRequiredParam(body, "acdc"))
            iserder = serdering.SerderKERI(sad=httping.getRequiredParam(body, "iss"))
            if "ixn" in body:
                anc = serdering.SerderKERI(sad=httping.getRequiredParam(body, "ixn"))
            else:
                anc = serdering.SerderKERI(sad=httping.getRequiredParam(body, "rot"))
        except (kering.ValidationError, json.decoder.JSONDecodeError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
            return

        regk = iserder.ked['ri']
        if regk not in agent.rgy.tevers:
            raise falcon.HTTPNotFound(description=f"issue against invalid registry SAID {regk}")

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        try:
            agent.credentialer.validate(creder)
            agent.registrar.issue(regk, iserder, anc)
            agent.credentialer.issue(creder=creder, serder=iserder)
            op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.credential,
                                      metadata=dict(ced=creder.sad, depends=op))

        except kering.ConfigurationError as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
            return

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")


class CredentialResourceEnd:
    def __init__(self):
        """

        """

    @staticmethod
    def on_get(req, rep, said):
        """ Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said (str): SAID of credential to export

        ---
        summary:  Export credential and all supporting cryptographic material
        description: Export credential and all supporting cryptographic material
        tags:
           - Credentials
        parameters:
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
           400:
             description: The requested credential was not found.
        """
        agent = req.context.agent
        accept = req.get_header("accept")
        if accept == "application/json+cesr":
            rep.content_type = "application/json+cesr"
            data = CredentialResourceEnd.outputCred(agent.hby, agent.rgy, said)
        else:
            rep.content_type = "application/json"
            creds = agent.rgy.reger.cloneCreds([coring.Saider(qb64=said)], db=agent.hby.db)
            if not creds:
                raise falcon.HTTPNotFound(description=f"credential for said {said} not found.")

            data = json.dumps(creds[0]).encode("utf-8")

        rep.status = falcon.HTTP_200
        rep.data = bytes(data)

    @staticmethod
    def outputCred(hby, rgy, said):
        out = bytearray()
        creder, prefixer, seqner, saider = rgy.reger.cloneCred(said=said)
        chains = creder.edge or dict()
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
            serder = serdering.SerderKERI(raw=msg)
            atc = msg[serder.size:]
            out.extend(serder.raw)
            out.extend(atc)

        if "i" in creder.attrib:
            subj = creder.attrib["i"]
            for msg in hby.db.clonePreIter(pre=subj):
                serder = serdering.SerderKERI(raw=msg)
                atc = msg[serder.size:]
                out.extend(serder.raw)
                out.extend(atc)

        if creder.regi is not None:
            for msg in rgy.reger.clonePreIter(pre=creder.regi):
                serder = serdering.SerderKERI(raw=msg)
                atc = msg[serder.size:]
                out.extend(serder.raw)
                out.extend(atc)

            for msg in rgy.reger.clonePreIter(pre=creder.said):
                serder = serdering.SerderKERI(raw=msg)
                atc = msg[serder.size:]
                out.extend(serder.raw)
                out.extend(atc)

        out.extend(signing.serialize(creder, prefixer, seqner, saider))

        return out


class CredentialResourceDeleteEnd:
    def __init__(self, identifierResource):
            """

            Parameters:
                identifierResource (IdentifierResourceEnd): endpoint class for creating rotation and interaction events

            """
            self.identifierResource = identifierResource

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
            raise falcon.HTTPNotFound(description="name is not a valid reference to an identifier")

        rserder = serdering.SerderKERI(sad=httping.getRequiredParam(body, "rev"))

        regk = rserder.ked['ri']
        if regk not in agent.rgy.tevers:
            raise falcon.HTTPNotFound(description=f"revocation against invalid registry SAID {regk}")

        try:
            agent.rgy.reger.cloneCreds([coring.Saider(qb64=said)], db=agent.hby.db)
        except:
            raise falcon.HTTPNotFound(description=f"credential for said {said} not found.")

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
            anc = httping.getRequiredParam(body, "rot")
        else:
            op = self.identifierResource.interact(agent, name, body)
            anc = httping.getRequiredParam(body, "ixn")

        try:
            agent.registrar.revoke(regk, rserder, anc)
        except Exception as e:
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

    def __init__(self, agentHab, hby, rgy, counselor, witDoer, witPub, verifier):
        self.hby = hby
        self.agentHab = agentHab
        self.rgy = rgy
        self.counselor = counselor
        self.witDoer = witDoer
        self.witPub = witPub
        self.verifier = verifier

    def incept(self, hab, registry, prefixer=None, seqner=None, saider=None):
        """

        Parameters:
            hab (Hab): human readable name for the registry
            registry (SignifyRegistry): qb64 identifier prefix of issuing identifier in control of this registry
            prefixer (Prefixer):
            seqner (Seqner): sequence number class of anchoring event
            saider (Saider): SAID class of anchoring event

        Returns:
            Registry:  created registry

        """
        rseq = coring.Seqner(sn=0)
        if not isinstance(hab, SignifyGroupHab):

            seqner = coring.Seqner(sn=hab.kever.sner.num)
            saider = coring.Saider(qb64=hab.kever.serder.said)
            registry.anchorMsg(pre=registry.regk, regd=registry.regd, seqner=seqner, saider=saider)
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))
            self.rgy.reger.tpwe.add(keys=(registry.regk, rseq.qb64), val=(hab.kever.prefixer, seqner, saider))

        else:
            print("Waiting for TEL registry vcp event mulisig anchoring event")
            self.rgy.reger.tmse.add(keys=(registry.regk, rseq.qb64, registry.regd), val=(prefixer, seqner, saider))

    def issue(self, regk, iserder, anc):
        """
        Create and process the credential issuance TEL events on the given registry

        Parameters:
            regk (str): qb64 identifier prefix of the credential registry
            iserder (Serder): TEL issuance event
            anc (Serder): Anchoring KEL event

        """
        registry = self.rgy.regs[regk]
        registry.processEvent(serder=iserder)
        hab = registry.hab

        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])

        if not isinstance(hab, SignifyGroupHab):  # not a multisig group
            seqner = coring.Seqner(sn=hab.kever.sner.num)
            saider = coring.Saider(qb64=hab.kever.serder.said)
            registry.anchorMsg(pre=vcid, regd=iserder.said, seqner=seqner, saider=saider)

            print("Waiting for TEL event witness receipts")
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))
            self.rgy.reger.tpwe.add(keys=(vcid, rseq.qb64), val=(hab.kever.prefixer, seqner, saider))
            return vcid, rseq.sn

        else:  # multisig group hab
            sn = anc.sn
            said = anc.said

            prefixer = coring.Prefixer(qb64=hab.pre)
            seqner = coring.Seqner(sn=sn)
            saider = coring.Saider(qb64=said)

            print(f"Waiting for TEL iss event mulisig anchoring event {seqner.sn}")
            self.rgy.reger.tmse.add(keys=(vcid, rseq.qb64, iserder.said), val=(prefixer, seqner, saider))
            return vcid, rseq.sn

    def revoke(self, regk, rserder, anc):
        """
        Create and process the credential revocation TEL events on the given registry

        Parameters:
            regk (str): qb64 identifier prefix of the credential registry
            rserder (Serder): TEL revocation event
            anc (Serder): KEL anchoring event
        """
        registry = self.rgy.regs[regk]
        registry.processEvent(serder=rserder)
        hab = registry.hab

        vcid = rserder.ked["i"]
        rseq = coring.Seqner(snh=rserder.ked["s"])

        if not isinstance(hab, SignifyGroupHab):

            seqner = coring.Seqner(sn=hab.kever.sner.num)
            saider = coring.Saider(qb64=hab.kever.serder.said)
            registry.anchorMsg(pre=vcid, regd=rserder.said, seqner=seqner, saider=saider)

            print("Waiting for TEL event witness receipts")
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))

            self.rgy.reger.tpwe.add(keys=(vcid, rseq.qb64), val=(hab.kever.prefixer, seqner, saider))
            return vcid, rseq.sn
        else:
            serder = serdering.SerderKERI(sad=anc)
            sn = serder.sn
            said = serder.said

            prefixer = coring.Prefixer(qb64=hab.pre)
            seqner = coring.Seqner(sn=sn)
            saider = coring.Saider(qb64=said)

            self.counselor.start(prefixer=prefixer, seqner=seqner, saider=saider, ghab=hab)

            print(f"Waiting for TEL rev event mulisig anchoring event {seqner.sn}")
            self.rgy.reger.tmse.add(keys=(vcid, rseq.qb64, rserder.said), val=(prefixer, seqner, saider))
            return vcid, rseq.sn

    def complete(self, pre, sn=0):
        """ Determine if registry event (inception, issuance, revocation, etc.) is finished validation

        Parameters:
            pre (str): qb64 identifier of registry event
            sn (int): integer sequence number of regsitry event

        Returns:
            bool: True means event has completed and is commited to database
        """

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


class Credentialer:

    def __init__(self, agentHab, hby, rgy, registrar, verifier, notifier):
        self.agentHab = agentHab
        self.hby = hby
        self.rgy = rgy
        self.registrar = registrar
        self.verifier = verifier
        self.notifier = notifier

    def validate(self, creder):
        """

        Args:
            creder (Creder): creder object representing the credential to validate

        Returns:
            bool: true if credential is valid against a known schema

        """
        schema = creder.sad['s']
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

    def issue(self, creder, serder):
        """ Issue the credential creder and handle witness propagation and communication

        Parameters:
            creder (Creder): Credential object to issue
            serder (Serder): KEL or TEL anchoring event

        """
        prefixer = coring.Prefixer(qb64=serder.pre)
        seqner = coring.Seqner(sn=serder.sn)

        self.rgy.reger.cmse.put(keys=(creder.said, seqner.qb64), val=creder)

        try:
            self.verifier.processCredential(creder=creder, prefixer=prefixer, seqner=seqner,
                                            saider=coring.Saider(qb64=serder.said))
        except kering.MissingRegistryError:
            pass

    def processCredentialMissingSigEscrow(self):
        for (said, snq), creder in self.rgy.reger.cmse.getItemIter():
            rseq = coring.Seqner(qb64=snq)
            if not self.registrar.complete(pre=said, sn=rseq.sn):
                continue

            saider = self.rgy.reger.saved.get(keys=said)
            if saider is None:
                continue

            # Remove from this escrow
            self.rgy.reger.cmse.rem(keys=(said, snq))

            # place in escrow to diseminate to other if witnesser and if there is an issuee
            self.rgy.reger.ccrd.put(keys=(creder.said,), val=creder)

    def complete(self, said):
        return self.rgy.reger.ccrd.get(keys=(said,)) is not None

    def processEscrows(self):
        """
        Process credential registry anchors:

        """
        self.processCredentialMissingSigEscrow()
