# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.credentialing module

services and endpoint for ACDC credential managements
"""
import json
from dataclasses import asdict, dataclass, field

import falcon
from keri import kering
from keri.app import signing
from keri.app.habbing import SignifyGroupHab
from keri.core import coring, scheming, serdering
from keri.db import dbing
from keri.db.dbing import dgKey
from keri.vdr import viring

from ..core import httping, longrunning
from marshmallow import fields, Schema
from typing import List, Dict, Any, Optional, Tuple, Literal


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

    credentialRegistryResEnd = CredentialRegistryResourceEnd()
    app.add_route("/registries/{ri}/{vci}", credentialRegistryResEnd)

    credentialResourceEnd = CredentialResourceEnd()
    app.add_route("/credentials/{said}", credentialResourceEnd)
    credentialResourceDelEnd = CredentialResourceDeleteEnd(identifierResource)
    app.add_route("/identifiers/{name}/credentials/{said}", credentialResourceDelEnd)

    queryCollectionEnd = CredentialQueryCollectionEnd()
    app.add_route("/credentials/query", queryCollectionEnd)

    credentialVerificationEnd = CredentialVerificationCollectionEnd()
    app.add_route("/credentials/verify", credentialVerificationEnd)

class EmptyDictSchema(Schema):
    class Meta:
        additional = ()

@dataclass
class ACDCAttributes:
    dt: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    i: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    u: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    # Override the schema to force additionalProperties=True

@dataclass
class Seal:
    s: str
    d: str
    i: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})

@dataclass
class ACDC:
    v: str
    d: str
    i: str
    s: str
    ri: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    a: Optional[ACDCAttributes] = field(default=None, metadata={"marshmallow_field": fields.Dict(allow_none=False)})
    u: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    e: Optional[List[Any]] = field(default=None, metadata={"marshmallow_field": fields.List(fields.Raw(), allow_none=False)})
    r: Optional[List[Any]] = field(default=None, metadata={"marshmallow_field": fields.List(fields.Raw(), allow_none=False)})

@dataclass
class IssEvt:
    v: str
    t: str
    d: str
    i: str
    s: str
    ri: str
    dt: str

@dataclass
class Schema:
    _id: str = field(metadata={"data_key": "$id"})
    _schema: str = field(metadata={"data_key": "$schema"})
    title: str
    description: str
    type: str
    credentialType: str
    version: str
    properties: Dict[str, Any]
    additionalProperties: bool
    required: List[str]

@dataclass
class StatusAnchor:
    s: int
    d: str

@dataclass
class Status:
    vn: List[int]
    i: str
    s: str
    d: str
    ri: str
    ra: Dict[str, Any]
    a: StatusAnchor
    dt: str
    et: str

@dataclass
class CredentialStateBase:
    vn: Tuple[int, int]
    i: str
    s: str
    d: str
    ri: str
    a: Seal
    dt: str
    et: str  # Will be narrowed in the subclasses

@dataclass
class CredentialStateIssOrRev(CredentialStateBase):
    et: Literal['iss', 'rev']
    ra: Dict[str, Any] = field(
        metadata={
            "marshmallow_field": fields.Nested(EmptyDictSchema(), allow_none=False, required=True)
        }
    )

@dataclass
class RaFields:
    i: str
    s: str
    d: str

@dataclass
class CredentialStateBisOrBrv(CredentialStateBase):
    et: Literal['bis', 'brv']
    ra: RaFields

@dataclass
class Anchor:
    pre: str
    sn: int
    d: str

@dataclass
class ANC:
    v: str
    t: str
    d: str
    i: str
    s: str
    p: str
    di: Optional[str] = field(default=None, metadata={"marshmallow_field": fields.String(allow_none=False)})
    a: Optional[List[Seal]] = field(default=None, metadata={"marshmallow_field": fields.List(fields.Raw(), allow_none=False)})

@dataclass
class ClonedCredential:
    sad: ACDC
    atc: str
    iss: IssEvt
    issatc: str
    pre: str
    schema: Schema
    chains: List[Dict[str, Any]]
    status: CredentialStateBase
    anchor: Anchor
    anc: ANC
    ancatc: str

@dataclass
class Registry:
    name: str
    regk: str
    pre: str
    state: CredentialStateBase

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
            name (str): human readable name or prefix for AID

        ---
        summary: List credential issuance and revocation registies
        description: List credential issuance and revocation registies
        tags:
           - Registries
        responses:
           200:
              description:  array of current credential issuance and revocation registies
              content:
                  application/json:
                    schema:
                        description: Registries
                        type: array
                        items:
                           $ref: '#/components/schemas/Registry'

        """
        agent = req.context.agent

        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

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
            name (str): human readable name or prefix of Hab to load credentials for

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
              content:
                  application/json:
                    schema:
                        $ref: '#/components/schemas/Operation'

        """
        agent = req.context.agent
        body = req.get_media()

        rname = httping.getRequiredParam(body, "name")
        ked = httping.getRequiredParam(body, "vcp")
        vcp = serdering.SerderKERI(sad=ked)

        ked = httping.getRequiredParam(body, "ixn")
        ixn = serdering.SerderKERI(sad=ked)

        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

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
        op = agent.monitor.submit(registry.regk, longrunning.OpTypes.registry,
                                  metadata=dict(pre=hab.kever.prefixer.qb64, anchor=anchor, depends=op))

        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class RegistryResourceEnd:

    @staticmethod
    def on_get(req, rep, name, registryName):
        """  Registry Resource GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID
            registryName(str): human readable name for registry

        ---
        summary: Get a single credential issuance and revocation registy
        description: Get a single credential issuance and revocation registy
        tags:
           - Registries
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The human-readable name of the identifier.
        - in: path
          name: registryName
          schema:
            type: string
          required: true
          description: The human-readable name of the registry.
        responses:
           200:
              description:  credential issuance and revocation registy
              content:
                  application/json:
                    schema:
                      $ref: '#/components/schemas/Registry'
           404:
            description: The requested registry was not found.
        """
        agent = req.context.agent

        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
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
            name (str): human readable name or prefix for AID
            registryName(str): human readable name for registry or its SAID

        ---
        summary: Get a single credential issuance and revocation registy
        description: Get a single credential issuance and revocation registy
        tags:
           - Registries
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The human-readable name of the identifier.
        - in: path
          name: registryName
          schema:
            type: string
          required: true
          description: The human-readable name of the registry.
        requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    name:
                      type: string
                      description: The new name for the registry.
        responses:
           200:
                description:  credential issuance and revocation registy
                content:
                  application/json:
                    schema:
                      $ref: '#/components/schemas/Registry'
           400:
                description: Bad request. This could be due to missing or invalid parameters.
           404:
                description: The requested registry was not found.
        """
        agent = req.context.agent

        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
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
              content:
                  application/json:
                    schema:
                      $ref: '#/components/schemas/Schema'
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
              content:
                  application/json:
                    schema:
                        type: array
                        items:
                           $ref: '#/components/schemas/Schema'
        """
        agent = req.context.agent

        data = []
        for said, schemer in agent.hby.db.schema.getItemIter():
            data.append(schemer.sed)

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(data).encode("utf-8")


class CredentialVerificationCollectionEnd:
    @staticmethod
    def on_post(req, rep):
        """ Verify credential endpoint (no IPEX)

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Verify a credential without IPEX
        description: Verify a credential without using IPEX (TEL should be updated separately)
        tags:
           - Credentials
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  required:
                    - acdc
                    - iss
                  properties:
                    acdc:
                      type: object
                      description: KED of ACDC
                    iss:
                      type: object
                      description: KED of issuing event in VC TEL
        responses:
           202:
              description: Credential accepted for parsing
              content:
                  application/json:
                    schema:
                        description: long running operation of credential processing
                        $ref: '#/components/schemas/Operation'
           404:
              description: Malformed ACDC or iss event
        """
        agent = req.context.agent
        body = req.get_media()

        try:
            creder = serdering.SerderACDC(sad=httping.getRequiredParam(body, "acdc"))
            iserder = serdering.SerderKERI(sad=httping.getRequiredParam(body, "iss"))
        except (kering.ValidationError, json.decoder.JSONDecodeError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
            return

        prefixer = coring.Prefixer(qb64=iserder.pre)
        seqner = coring.Seqner(sn=iserder.sn)
        saider = coring.Saider(qb64=iserder.said)

        agent.parser.ims.extend(signing.serialize(creder, prefixer, seqner, saider))
        op = agent.monitor.submit(creder.said, longrunning.OpTypes.credential,
                                  metadata=dict(ced=creder.sad))
        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


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
                           $ref: '#/components/schemas/Credential'

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
            name (str): human readable alias or prefix for AID to use as issuer

        ---
        summary: Perform credential issuance
        description: Perform credential issuance
        tags:
           - Credentials
        parameters:
          - in: path
            name: alias or prefix
            schema:
              type: string
            required: true
            description: Human readable alias or prefix for the identifier to create
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
                        $ref: '#/components/schemas/Credential'

        """
        agent = req.context.agent

        body = req.get_media()
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")
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
            op = agent.monitor.submit(creder.said, longrunning.OpTypes.credential,
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
                        $ref: '#/components/schemas/Credential'
           400:
             description: The requested credential was not found.
        """
        agent = req.context.agent
        accept = req.get_header("accept")
        try:
            if accept == "application/json+cesr":
                rep.content_type = "application/json+cesr"
                data = CredentialResourceEnd.outputCred(agent.hby, agent.rgy, said)
            else:
                rep.content_type = "application/json"
                creds = agent.rgy.reger.cloneCreds([coring.Saider(qb64=said)], db=agent.hby.db)
                data = json.dumps(creds[0]).encode("utf-8")
        except kering.MissingEntryError:
            raise falcon.HTTPNotFound(description=f"credential for said {said} not found.")

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

    @staticmethod
    def on_delete(req, rep, said):
        """ Credentials DELETE endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said (str): SAID of credential to delete

        ---
        summary: Delete a credential from the database
        description: Delete a credential from the database and remove any associated indices
        tags:
           - Credentials
        parameters:
           - in: path
             name: said
             schema:
               type: string
             required: true
             description: SAID of credential to delete
        responses:
           204:
              description: Credential deleted successfully
           400:
             description: The requested credential was not found
        """
        agent = req.context.agent
        reger = agent.rgy.reger

        try:
            creder, _, _, _ = reger.cloneCred(said)
        except kering.MissingEntryError:
            raise falcon.HTTPNotFound(description=f"credential for said {said} not found.")

        agent.seeker.unindex(said)

        saider = coring.Saider(qb64b=said)
        if not isinstance(creder.attrib, str) and 'i' in creder.attrib:
            subj = creder.attrib["i"]
            if subj:
                reger.subjs.rem(keys=subj, val=saider)

        reger.schms.rem(keys=creder.sad["s"], val=saider)
        reger.issus.rem(keys=creder.sad["i"], val=saider)
        reger.saved.rem(keys=said)
        reger.creds.rem(keys=said)
        reger.cancs.rem(keys=said)

        rep.status = falcon.HTTP_204


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
            name (str): human readable alias or prefix for AID to use as issuer
            said (str): SAID of credential to revoke

        RequestBody:
            rev (str): serialized revocation event
            ixn (str): serialized interaction event
            rot (str): serialized rotation event
            sigs (list): list of signatures for the revocation event
        ---
        summary: Perform credential revocation
        description: Initiates a credential revocation for a given identifier and SAID.
        tags:
         - Credentials
        parameters:
        - in: path
          name: name or prefix
          schema:
            type: string
          required: true
          description: The human-readable alias or prefix for the AID to use as issuer.
        - in: path
          name: said
          schema:
            type: string
          required: true
          description: The SAID of the credential to revoke.
        requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    rev:
                      type: string
                      description: Serialized revocation event.
                    ixn:
                      type: string
                      description: Serialized interaction event.
                    rot:
                      type: string
                      description: Serialized rotation event.
                    sigs:
                      type: array
                      items:
                        type: string
                      description: List of signatures for the revocation event.
        responses:
            200:
                description: Credential revocation initiated successfully.
                content:
                  application/json+cesr:
                    schema:
                        $ref: '#/components/schemas/Operation'
            400:
                description: Bad request. This could be due to invalid revocation event or other invalid parameters.
            404:
                description: The requested identifier or credential was not found.
        """

        agent = req.context.agent

        body = req.get_media()
        hab = agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid reference to an identifier")

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


class CredentialRegistryResourceEnd:
    @staticmethod
    def on_get(req, rep, ri, vci):
        """ Get credential registry state

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Get credential registry state
        description: Get credential registry state from any known Tever (does not need be controlled by us)
        tags:
           - Credentials
        parameters:
           - in: path
             name: ri
             schema:
               type: string
             required: true
             description: SAID of management TEL
           - in: path
             name: vci
             schema:
               type: string
             required: true
             description: SAID of credential
        responses:
           200:
              description: Credential registry state
              content:
                  application/json:
                    schema:
                        description: Credential registry state
                        $ref: '#/components/schemas/CredentialState'
           404:
              description: Unknown management registry or credential
        """
        agent = req.context.agent
        if ri not in agent.tvy.tevers:
            raise falcon.HTTPNotFound(description=f"registry {ri} not found")
        tever = agent.tvy.tevers[ri]

        state = tever.vcState(vci)
        if not state:
            raise falcon.HTTPNotFound(description=f"credential {vci} not found in registry {ri}")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(asdict(state)).encode("utf-8")


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
