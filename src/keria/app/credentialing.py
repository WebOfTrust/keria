# -*- encoding: utf-8 -*-
"""
KERI
keria.app.credentialing module

services and endpoint for ACDC credential managements
"""
import json
from dataclasses import asdict

import falcon
from keri.core import coring
from keri.core.eventing import proofize

from keria.core import httping, longrunning


def loadEnds(app, identifierResource):
    schemaColEnd = SchemaCollectionEnd()
    app.add_route("/schema", schemaColEnd)
    schemaResEnd = SchemaResourceEnd()
    app.add_route("/schema/{said}", schemaResEnd)

    registryEnd = RegistryEnd(identifierResource)
    app.add_route("/registries", registryEnd)

    credentialCollectionEnd = CredentialCollectionEnd()
    app.add_route("/aids/{aid}/credentials", credentialCollectionEnd)
    
    credentialResourceEnd = CredentialResourceEnd()
    app.add_route("/aids/{aid}/credentials/{said}", credentialResourceEnd)


class RegistryEnd:
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
    def on_get(req, rep):
        """  Registries GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

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

        res = []
        for name, registry in agent.rgy.regs.items():
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

    def on_post(self, req, rep):
        """  Registries POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

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

        alias = httping.getRequiredParam(body, "alias")
        name = httping.getRequiredParam(body, "name")
        ked = httping.getRequiredParam(body, "vcp")
        vcp = coring.Serder(ked=ked)

        hab = agent.hby.habByName(alias)
        if hab is None:
            raise falcon.HTTPNotFound(description="alias is not a valid reference to an identfier")

        agent.rgy.makeSignifyRegistry(name=name, prefix=hab.pre, regser=vcp)
        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, alias, body)
        else:
            op = self.identifierResource.interact(agent, alias, body)

        # Create registry long running OP that embeds the above received OP or Serder.
        agent.registries.append(dict(pre=hab.pre, regk=vcp.pre, sn=vcp.ked["s"], regd=vcp.said))
        op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.registry,
                                  metadata=dict(anchor=op))

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


class CredentialCollectionEnd:

    @staticmethod
    def on_get(req, rep, aid):
        """ Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            aid (str): AID of Hab to load credentials for

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
        
        typ = req.params.get("type")
        schema = req.params.get("schema")

        if aid not in agent.hby.habs:
            raise falcon.HTTPBadRequest(description=f"Invalid identifier {aid} for credentials")

        hab = agent.hby.habs[aid]

        if typ == "issued":
            saids = agent.rgy.reger.issus.get(keys=hab.pre)
        elif typ == "received":
            saids = agent.rgy.reger.subjs.get(keys=hab.pre)
        else:
            raise falcon.HTTPBadRequest(description=f"Invalid type {typ}")

        if schema is not None:
            scads = agent.rgy.reger.schms.get(keys=schema)
            saids = [saider for saider in saids if saider.qb64 in [saider.qb64 for saider in scads]]

        creds = agent.rgy.reger.cloneCreds(saids)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(creds).encode("utf-8")


class CredentialResourceEnd:

    @staticmethod
    def on_get(req, rep, aid, said):
        """ Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            aid (str): identifier to load credential for
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

        if aid not in agent.hby.habs:
            raise falcon.HTTPBadRequest(description=f"Invalid identifier {aid} for credentials")

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

