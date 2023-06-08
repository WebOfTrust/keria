# -*- encoding: utf-8 -*-
"""
KERI
keria.app.credentialing module

services and endpoint for ACDC credential managements
"""
import json

import falcon
from keri.core import coring

from keria.core import httping, longrunning


def loadEnds(app, identifierResource):
    registryEnd = RegistryEnd(identifierResource)
    app.add_route("/registries", registryEnd)

    schemaColEnd = SchemaCollectionEnd()
    app.add_route("/schema", schemaColEnd)
    schemaResEnd = SchemaResourceEnd()
    app.add_route("/schema/{said}", schemaResEnd)


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
                state=registry.tever.state().ked
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

        registry = agent.rgy.makeSignifyRegistry(name=name, prefix=hab.pre, regser=vcp)
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
