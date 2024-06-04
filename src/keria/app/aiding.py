# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.aiding module

"""
import json
from dataclasses import asdict
from urllib.parse import urlparse, urljoin

import falcon
from keri import kering
from keri import core
from keri.app import habbing
from keri.app.keeping import Algos
from keri.core import coring, serdering
from keri.core.coring import Ilks
from keri.db import dbing
from keri.help import ogler
from mnemonic import mnemonic

from ..core import longrunning, httping

logger = ogler.getLogger()


def loadEnds(app, agency, authn):
    groupEnd = AgentResourceEnd(agency=agency, authn=authn)
    app.add_route("/agent/{caid}", groupEnd)

    aidsEnd = IdentifierCollectionEnd()
    app.add_route("/identifiers", aidsEnd)
    aidEnd = IdentifierResourceEnd()
    app.add_route("/identifiers/{name}", aidEnd)
    app.add_route("/identifiers/{name}/events", aidEnd)

    aidOOBIsEnd = IdentifierOOBICollectionEnd()
    app.add_route("/identifiers/{name}/oobis", aidOOBIsEnd)

    endRolesEnd = EndRoleCollectionEnd()
    app.add_route("/identifiers/{name}/endroles", endRolesEnd)
    app.add_route("/identifiers/{name}/endroles/{role}", endRolesEnd)
    app.add_route("/endroles/{aid}", endRolesEnd)
    app.add_route("/endroles/{aid}/{role}", endRolesEnd)

    endRoleEnd = EndRoleResourceEnd()
    app.add_route("/identifiers/{name}/endroles/{role}/{eid}", endRoleEnd)

    rpyEscrowEnd = RpyEscrowCollectionEnd()
    app.add_route("/escrows/rpy", rpyEscrowEnd)

    chaEnd = ChallengeCollectionEnd()
    app.add_route("/challenges", chaEnd)
    chaResEnd = ChallengeResourceEnd()
    app.add_route("/challenges/{name}", chaResEnd)
    chaVerResEnd = ChallengeVerifyResourceEnd()
    app.add_route("/challenges_verify/{source}", chaVerResEnd)

    contactColEnd = ContactCollectionEnd()
    app.add_route("/contacts", contactColEnd)
    contactResEnd = ContactResourceEnd()
    app.add_route("/contacts/{prefix}", contactResEnd)
    contactImgEnd = ContactImageResourceEnd()
    app.add_route("/contacts/{prefix}/img", contactImgEnd)

    groupEnd = GroupMemberCollectionEnd()
    app.add_route("/identifiers/{name}/members", groupEnd)

    return aidEnd


class AgentResourceEnd:
    """ Resource class for getting agent specific launch information """

    def __init__(self, agency, authn):
        self.agency = agency
        self.authn = authn

    def on_get(self, _, rep, caid):
        """ GET endpoint for Keystores

        Get keystore status

        Args:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            caid(str): qb64 identifier prefix of Controller

        ---
        summary: Retrieve key state record of an agent by controller AID.
        description: This endpoint retrieves the key state record for a given controller of an agent.
        tags:
        - Agent
        parameters:
        - in: path
          name: caid
          schema:
            type: string
          required: true
          description: The qb64 identifier prefix of Controller.
        responses:
          200:
            description: Successfully retrieved the key state record.
          400:
            description: Bad request. This could be due to an invalid agent or controller configuration.
          404:
            description: The requested controller or agent was not found.
        """
        agent = self.agency.get(caid)
        if agent is None:
            raise falcon.HTTPNotFound(description=f"not agent found for controller {caid}")

        if agent.pre not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(description=f"invalid agent configuration, {agent.pre} not found")

        if agent.caid not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(description=f"invalid controller configuration, {agent.caid} not found")

        pidx = 0
        for name, _ in agent.hby.db.names.getItemIter():
            if name[0] != "agent":
                pidx += 1

        # pidx = agent.hby.db.habs.cntAll()

        state = asdict(agent.hby.kevers[agent.caid].state())
        key = dbing.dgKey(state['i'], state['ee']['d'])  # digest key
        msg = agent.hby.db.getEvt(key)
        eserder = serdering.SerderKERI(raw=bytes(msg))

        body = dict(
            agent=asdict(agent.hby.kevers[agent.pre].state()),
            controller=dict(
                state=state,
                ee=eserder.ked
            ),
            pidx=pidx
        )

        if (sxlt := agent.mgr.sxlt) is not None:
            body["sxlt"] = sxlt

        rep.content_type = "application/json"
        rep.data = json.dumps(body).encode("utf-8")
        rep.status = falcon.HTTP_200

    def on_put(self, req, rep, caid):
        """

        Parameters:
            req (Request): falcon.Request HTTP request
            rep (Response): falcon.Response HTTP response
            caid(str): qb64 identifier prefix of Controller

        ---
        summary: Update agent configuration by controller AID.
        description: This endpoint updates the agent configuration based on the provided request parameters and body.
        tags:
        - Agent
        parameters:
        - in: path
          name: caid
          schema:
            type: string
          required: true
          description: The qb64 identifier prefix of Controller.
        requestBody:
            required: true
            content:
              application/json:
                schema:
                  type: object
                  required:
                    - rot
                    - sigs
                    - sxlt
                    - kyes
                  properties:
                    rot:
                      type: object
                      description: The rotation event.
                    sigs:
                      type: array
                      items:
                          type: string
                      description: The signatures.
                    sxlt:
                      type: string
                      description: The salty parameters.
                    keys:
                      type: object
                      description: The keys.
        responses:
            204:
              description: Successfully updated the agent configuration.
            400:
              description: Bad request. This could be due to missing or invalid parameters.
            404:
              description: The requested agent was not found.
            500:
              description: Internal server error. This could be due to an issue with updating the agent configuration.
        """
        agent = self.agency.get(caid)
        if agent is None:
            raise falcon.HTTPNotFound(description=f"no agent for {caid}")

        typ = req.params.get("type")
        if typ == "ixn":
            ixn = self.interact(req, rep, agent, caid)
            self.anchorSeals(agent, ixn)
            return

        body = req.get_media()

        if "rot" not in body:
            raise falcon.HTTPBadRequest(description="required field 'rot' missing from body")

        if "sigs" not in body:
            raise falcon.HTTPBadRequest(description="required field 'sigs' missing from body")

        if "sxlt" not in body:
            raise falcon.HTTPBadRequest(description="required field 'sxlt' missing from body")

        if "keys" not in body:
            raise falcon.HTTPBadRequest(description="required field 'keys' missing from body")

        rot = serdering.SerderKERI(sad=body["rot"])
        sigs = body["sigs"]

        ctrlHab = agent.hby.habByName(caid, ns="agent")
        ctrlHab.rotate(serder=rot, sigers=[core.Siger(qb64=sig) for sig in sigs])

        if not self.authn.verify(req):
            raise falcon.HTTPForbidden(description="invalid signature on request")

        sxlt = body["sxlt"]
        agent.mgr.sxlt = sxlt

        keys = body["keys"]
        for pre, val in keys.items():
            if "sxlt" in val:
                if (sp := agent.mgr.rb.sprms.get(pre)) is None:
                    raise ValueError("Attempt to update sxlt for nonexistent or invalid pre={}.".format(pre))

                sp.sxlt = val["sxlt"]

                if not agent.mgr.rb.sprms.pin(pre, val=sp):
                    raise ValueError("Unable to update sxlt prms for pre={}.".format(pre))

            elif "prxs" in val:
                hab = agent.hby.habs[pre]
                verfers = hab.kever.verfers
                digers = hab.kever.digers
                prxs = val["prxs"]

                for idx, prx in enumerate(prxs):
                    cipher = core.Cipher(qb64=prx)
                    agent.mgr.rb.prxs.put(keys=verfers[idx].qb64b, val=cipher)

                if "nxts" in val:
                    nxts = val["nxts"]
                    if len(nxts) != len(digers):
                        raise ValueError("If encrypted private next keys are provided, must match digers")

                    for idx, prx in enumerate(nxts):
                        cipher = core.Cipher(qb64=prx)
                        agent.mgr.rb.nxts.put(keys=digers[idx].qb64b, val=cipher)

        agent.mgr.delete_sxlt()

        rep.status = falcon.HTTP_204

    @staticmethod
    def interact(req, rep, agent, caid):
        body = req.get_media()

        if "ixn" not in body:
            raise falcon.HTTPBadRequest(description="required field 'ixn' missing from body")

        if "sigs" not in body:
            raise falcon.HTTPBadRequest(description="required field 'sigs' missing from body")

        ked = body['ixn']
        sigs = body['sigs']
        ixn = serdering.SerderKERI(sad=ked)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        ctrlHab = agent.hby.habByName(caid, ns="agent")

        ctrlHab.interact(serder=ixn, sigers=sigers)
        agent.agentHab.kvy.processEvent(serder=ixn, sigers=sigers)

        rep.status = falcon.HTTP_204

        return ixn

    @staticmethod
    def anchorSeals(agent, ixn):
        a = ixn.ked["a"]
        if len(a) == 0:
            return

        delegator = coring.Saider(qb64=ixn.ked['d'])
        delegatorsn = coring.Seqner(snh=ixn.ked['s'])

        seal = a[0]
        prefixer = coring.Prefixer(qb64=seal['i'])
        saider = coring.Saider(qb64=seal["d"])

        couple = delegatorsn.qb64b + delegator.qb64b
        dgkey = dbing.dgKey(prefixer.qb64b, saider.qb64)
        agent.hby.db.setAes(dgkey, couple)  # authorizer event seal (delegator/issuer)


class IdentifierCollectionEnd:
    """ Resource class for creating and managing identifiers """

    @staticmethod
    def on_options(req, rep):
        rep.add_header("Accept-Ranges", "aids")
        rep.status = falcon.HTTP_200

    @staticmethod
    def on_get(req, rep):
        """ Identifier List GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Retrieve a list of identifiers associated with the agent.
        description: This endpoint retrieves a list of identifiers associated with the agent.
                     It supports pagination through the 'Range' header.
        tags:
          - Identifier
        parameters:
        - in: header
          name: Range
          schema:
            type: string
          required: false
          description: The 'Range' header is used for pagination. The default range is 0-9.
        responses:
            200:
                description: Successfully retrieved identifiers.
            206:
                description: Successfully retrieved identifiers within the specified range.
        """
        agent = req.context.agent
        res = []

        rng = req.get_header("Range")
        if rng is None:
            rep.status = falcon.HTTP_200
            start = 0
            end = 9
        else:
            rep.status = falcon.HTTP_206
            start, end = httping.parseRangeHeader(rng, "aids")

        count = agent.hby.db.habs.cntAll()
        it = agent.hby.db.names.getItemIter()
        for _ in range(start):
            try:
                next(it)
            except StopIteration:
                break

        for (ns, name), pre in it:
            if ns == "agent":
                continue

            hab = agent.hby.habs[pre]
            data = info(hab, agent.mgr)
            res.append(data)

            if (not end == -1) and len(res) == (end - start) + 1:
                break

        end = start + (len(res) - 1) if len(res) > 0 else 0
        rep.set_header("Accept-Ranges", "aids")
        rep.set_header("Content-Range", f"aids {start}-{end}/{count - 1}")
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    @staticmethod
    def on_post(req, rep):
        """ Inception event POST endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        ---
        summary: Create an identifier.
        description: This endpoint creates an identifier with the provided inception event, name, and signatures.
        tags:
        - Identifier
        requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    icp:
                      type: object
                      description: The inception event for the identifier.
                    name:
                      type: string
                      description: The name of the identifier.
                    sigs:
                      type: array
                      items:
                          type: string
                      description: The signatures for the inception event.
                    group:
                      type: object
                      description: Multisig group information.
                    salty:
                      type: object
                      description: Salty parameters.
                    randy:
                      type: object
                      description: Randomly generated materials.
                    extern:
                      type: object
                      description: External parameters.
        responses:
            202:
                description: Identifier creation is in progress. The response is a long running operation.
            400:
                description: Bad request. This could be due to missing or invalid parameters.
        """
        agent = req.context.agent
        try:
            body = req.get_media()
            icp = httping.getRequiredParam(body, "icp")
            name = httping.getRequiredParam(body, "name")
            sigs = httping.getRequiredParam(body, "sigs")

            serder = serdering.SerderKERI(sad=icp)

            sigers = [core.Siger(qb64=sig) for sig in sigs]

            if agent.hby.habByName(name) is not None:
                raise falcon.HTTPBadRequest(title=f"AID with name {name} already incepted")

            if 'b' in icp:
                for wit in icp['b']:
                    urls = agent.agentHab.fetchUrls(eid=wit, scheme=kering.Schemes.http)
                    if not urls and wit not in agent.hby.kevers:
                        raise falcon.HTTPBadRequest(description=f'unknown witness {wit}')

            if 'di' in icp and icp["di"] not in agent.hby.kevers:
                raise falcon.HTTPBadRequest(description=f'unknown delegator {icp["di"]}')

            # client is requesting agent to join multisig group
            if "group" in body:
                group = body["group"]

                if "mhab" not in group:
                    raise falcon.HTTPBadRequest(description=f'required field "mhab" missing from body.group')
                mpre = group["mhab"]["prefix"]

                if mpre not in agent.hby.habs:
                    raise falcon.HTTPBadRequest(description=f'signing member {mpre} not a local AID')
                mhab = agent.hby.habs[mpre]

                if "keys" not in group:
                    raise falcon.HTTPBadRequest(description=f'required field "keys" missing from body.group')
                keys = group["keys"]
                verfers = [coring.Verfer(qb64=key) for key in keys]

                if mhab.kever.fetchLatestContribTo(verfers=verfers) is None:
                    raise falcon.HTTPBadRequest(description=f"Member hab={mhab.pre} not a participant in "
                                                            f"event for this group hab.")

                if "ndigs" not in group:
                    raise falcon.HTTPBadRequest(description=f'required field "ndigs" missing from body.group')
                ndigs = group["ndigs"]
                digers = [coring.Diger(qb64=ndig) for ndig in ndigs]

                states = httping.getRequiredParam(body, "smids")
                rstates = httping.getRequiredParam(body, "rmids")
                smids = [state['i'] for state in states]
                rmids = [rstate['i'] for rstate in rstates]
                hab = agent.hby.makeSignifyGroupHab(name, mhab=mhab, smids=smids, rmids=rmids, serder=serder,
                                                    sigers=sigers)
                try:
                    agent.inceptGroup(pre=serder.pre, mpre=mhab.pre, verfers=verfers, digers=digers)
                except ValueError as e:
                    agent.hby.deleteHab(name=name)
                    raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                # Generate response, a long running operaton indicator for the type
                agent.groups.append(dict(pre=hab.pre, serder=serder, sigers=sigers, smids=states, rmids=rstates))
                op = agent.monitor.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=0))

                rep.content_type = "application/json"
                rep.status = falcon.HTTP_202
                rep.data = op.to_json().encode("utf-8")

            else:
                # client is requesting that the Agent track the Salty parameters
                if Algos.salty in body:
                    salt = body[Algos.salty]
                    hab = agent.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        agent.inceptSalty(pre=serder.pre, **salt)
                    except ValueError as e:
                        agent.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                # client is storing encrypted randomly generated key material on agent
                elif Algos.randy in body:
                    rand = body[Algos.randy]
                    hab = agent.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        agent.inceptRandy(pre=serder.pre, verfers=serder.verfers, digers=serder.ndigers, **rand)
                    except ValueError as e:
                        agent.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                elif Algos.extern in body:
                    extern = body[Algos.extern]
                    hab = agent.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        agent.inceptExtern(pre=serder.pre, verfers=serder.verfers, digers=serder.ndigers, **extern)
                    except ValueError as e:
                        agent.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                else:
                    raise falcon.HTTPBadRequest(
                        description="invalid request: one of group, rand or salt field required")

                # create Hab and incept the key store (if any)
                # Generate response, either the serder or a long running operaton indicator for the type
                rep.content_type = "application/json"
                if hab.kever.delpre:
                    agent.anchors.append(dict(pre=hab.pre, sn=0))
                    op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.delegation,
                                              metadata=dict(pre=hab.pre, sn=0))
                    rep.status = falcon.HTTP_202
                    rep.data = op.to_json().encode("utf-8")

                elif hab.kever.wits:
                    agent.witners.append(dict(serder=serder))
                    op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.witness,
                                              metadata=dict(sn=0))
                    rep.status = falcon.HTTP_202
                    rep.data = op.to_json().encode("utf-8")

                else:
                    rep.status = falcon.HTTP_202
                    op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.done,
                                              metadata=dict(response=serder.ked))
                    rep.data = op.to_json().encode("utf-8")

        except (kering.AuthError, ValueError) as e:
            raise falcon.HTTPBadRequest(description=e.args[0])


class IdentifierResourceEnd:
    """ Resource class for updating and deleting identifiers """

    @staticmethod
    def on_get(req, rep, name):
        """ Identifier GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human-readable name for Hab to GET

        ---
        summary: Retrieve an identifier.
        description: This endpoint retrieves an identifier by its human-readable name.
        tags:
        - Identifier
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The human-readable name of the identifier.
        responses:
            200:
                description: Successfully retrieved the identifier details.
            400:
                description: Bad request. This could be due to a missing or invalid name parameter.
            404:
                description: The requested identifier was not found.
        """
        if not name:
            raise falcon.HTTPBadRequest(description="name is required")

        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid identifier name")

        data = info(hab, agent.mgr, full=True)
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(data).encode("utf-8")

    def on_put(self, req, rep, name):
        """ Identifier rename endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object
            name (str): human readable name for Hab to rename

        ---
        summary: Rename an identifier.
        description: This endpoint renames an identifier with the provided new name.
        tags:
        - Identifier
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The current human-readable name of the identifier.
        requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    name:
                      type: string
                      description: The new name for the identifier.
                  required:
                  - name
        responses:
            200:
              description: Successfully renamed the identifier and returns the updated information.
            400:
              description: Bad request. This could be due to a missing or invalid name parameter.
            404:
              description: The requested identifier was not found.
        """
        if not name:
            raise falcon.HTTPBadRequest(description="name is required")
        agent = req.context.agent
        hab = agent.hby.habByName(name)

        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID with name {name} found")
        body = req.get_media()
        newName = body.get("name")
        habord = hab.db.habs.get(keys=(hab.pre,))
        habord.name = newName
        hab.db.habs.pin(keys=(hab.pre,),
                        val=habord)
        hab.db.names.pin(keys=("", newName), val=hab.pre)
        hab.db.names.rem(keys=("", name))
        hab.name = newName
        hab = agent.hby.habByName(newName)
        data = info(hab, agent.mgr, full=True)
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(data).encode("utf-8")

    def on_delete(self, req, rep, name):
        """ Identifier delete endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object
            name (str): human-readable name for Hab to delete
        ---
        summary: Delete an identifier.
        description: This endpoint deletes an identifier by its name.
        tags:
        - Identifier
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The human-readable name of the identifier.
        responses:
            200:
                description: Successfully deleted the identifier.
            400:
                description: Bad request. This could be due to a missing or invalid name parameter.
            404:
                description: The requested identifier was not found.
        """
        if not name:
            raise falcon.HTTPBadRequest(description="name is required")
        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID with name {name} found")
        agent.hby.deleteHab(name)
        rep.status = falcon.HTTP_200

    def on_post(self, req, rep, name):
        """ Identifier events endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object
            name (str): human-readable name for Hab to rotate or interact

        ---
        summary: Process identifier events.
        description: This endpoint handles the 'rot' or 'ixn' events of an identifier based on the provided request.
        tags:
        - Identifier
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The human-readable name of the identifier.
        requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    rot:
                      type: object
                      description: The rotation event details.
                    ixn:
                      type: object
                      description: The interaction event details.
                  oneOf:
                  - required:
                    - rot
                  - required:
                    - ixn
        responses:
            200:
              description: Successfully processed the identifier's event.
            400:
              description: Bad request. This could be due to missing or invalid parameters.
        """
        if not name:
            raise falcon.HTTPBadRequest(description="name is required")
        agent = req.context.agent
        try:
            body = req.get_media()
            if body.get("rot") is not None:
                op = self.rotate(agent, name, body)
            elif body.get("ixn") is not None:
                op = self.interact(agent, name, body)
            else:
                raise falcon.HTTPBadRequest(title="invalid request",
                                            description=f"required field 'rot' or 'ixn' missing from request")

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = op.to_json().encode("utf-8")

        except (kering.AuthError, ValueError) as e:
            raise falcon.HTTPBadRequest(description=e.args[0])

    @staticmethod
    def rotate(agent, name, body):
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(title=f"No AID with name {name} found")

        rot = body.get("rot")
        if rot is None:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'rot' missing from request")

        if 'ba' in rot:
            for wit in rot['ba']:
                urls = agent.agentHab.fetchUrls(eid=wit, scheme=kering.Schemes.http)
                if not urls and wit not in agent.hby.kevers:
                    raise falcon.HTTPBadRequest(description=f'unknown witness {wit}')

        sigs = body.get("sigs")
        if sigs is None or len(sigs) == 0:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'sigs' missing from request")

        serder = serdering.SerderKERI(sad=rot)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        if Algos.salty in body:
            hab.rotate(serder=serder, sigers=sigers)

            salt = body[Algos.salty]
            keeper = agent.mgr.get(Algos.salty)

            try:
                keeper.rotate(pre=serder.pre, **salt)
            except ValueError as e:
                agent.hby.deleteHab(name=name)
                raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

        elif Algos.randy in body:
            hab.rotate(serder=serder, sigers=sigers)

            rand = body[Algos.randy]
            keeper = agent.mgr.get(Algos.randy)

            keeper.rotate(pre=serder.pre, verfers=serder.verfers, digers=serder.ndigers, **rand)

        elif Algos.group in body:
            smids = httping.getRequiredParam(body, "smids")
            rmids = httping.getRequiredParam(body, "rmids")

            hab.rotate(serder=serder, sigers=sigers, smids=smids, rmids=rmids)

            keeper = agent.mgr.get(Algos.group)

            keeper.rotate(pre=serder.pre, verfers=serder.verfers, digers=serder.ndigers)

            agent.groups.append(dict(pre=hab.pre, serder=serder, sigers=sigers, smids=smids, rmids=rmids))
            op = agent.monitor.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=serder.sn))

            return op

        if hab.kever.delpre:
            agent.anchors.append(dict(alias=name, pre=hab.pre, sn=serder.sn))
            op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.delegation,
                                      metadata=dict(pre=hab.pre, sn=serder.sn))
            return op

        if hab.kever.wits:
            agent.witners.append(dict(serder=serder))
            op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.witness,
                                      metadata=dict(sn=serder.sn))
            return op

        op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.done,
                                  metadata=dict(response=serder.ked))
        return op

    @staticmethod
    def interact(agent, name, body):
        hab = agent.hby.habByName(name)
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

        serder = serdering.SerderKERI(sad=ixn)
        sigers = [core.Siger(qb64=sig) for sig in sigs]

        hab.interact(serder=serder, sigers=sigers)

        if "group" in body:
            agent.groups.append(dict(pre=hab.pre, serder=serder, sigers=sigers))
            op = agent.monitor.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=serder.sn))

            return op

        if hab.kever.wits:
            agent.witners.append(dict(serder=serder))
            op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.witness,
                                      metadata=dict(sn=serder.sn))
            return op

        op = agent.monitor.submit(hab.kever.prefixer.qb64, longrunning.OpTypes.done,
                                  metadata=dict(response=serder.ked))
        return op


def info(hab, rm, full=False):
    data = dict(
        name=hab.name,
        prefix=hab.pre,
    )

    if not isinstance(hab, habbing.SignifyHab) and not isinstance(hab, habbing.SignifyGroupHab):
        raise kering.ConfigurationError(f"agent only allows SignifyHab instances, {type(hab)}")

    keeper = rm.get(pre=hab.pre)
    data.update(keeper.params(pre=hab.pre))
    if isinstance(hab, habbing.SignifyGroupHab):
        data["group"]["mhab"] = info(hab.mhab, rm, full)

    if hab.accepted and full:
        kever = hab.kevers[hab.pre]
        data["transferable"] = kever.transferable
        data["state"] = asdict(kever.state())
        dgkey = dbing.dgKey(kever.prefixer.qb64b, kever.serder.saidb)
        wigs = hab.db.getWigs(dgkey)
        data["windexes"] = [core.Siger(qb64b=bytes(wig)).index for wig in wigs]

    return data


class IdentifierOOBICollectionEnd:
    """
      This class represents the OOBI subresource collection endpoint for identifiers

    """

    @staticmethod
    def on_get(req, rep, name):
        """ Identifier GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name for Hab to GET

        """
        agent = req.context.agent
        if not name:
            raise falcon.HTTPBadRequest(description="name is required")

        hab = agent.hby.habByName(name)
        if not hab:
            raise falcon.HTTPNotFound(description="invalid alias {name}")

        if "role" not in req.params:
            raise falcon.HTTPBadRequest(description="role parameter required")

        role = req.params["role"]

        res = dict(role=role)
        if role in (kering.Roles.witness,):  # Fetch URL OOBIs for all witnesses
            oobis = []
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http) or hab.fetchUrls(eid=wit,
                                                                                           scheme=kering.Schemes.https)
                if not urls:
                    raise falcon.HTTPNotFound(description=f"unable to query witness {wit}, no http endpoint")

                url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
                up = urlparse(url)
                oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/witness/{wit}"))
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http) or hab.fetchUrls(eid=hab.pre,
                                                                                           scheme=kering.Schemes.https)
            if not urls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            url = urls[kering.Schemes.http] if kering.Schemes.http in urls else urls[kering.Schemes.https]
            up = urlparse(url)
            oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/controller"))
            res["oobis"] = oobis
        elif role in (kering.Roles.agent,):  # Fetch URL OOBIs for all witnesses
            roleUrls = hab.fetchRoleUrls(cid=hab.pre, role=kering.Roles.agent,
                                         scheme=kering.Schemes.http) or hab.fetchRoleUrls(cid=hab.pre,
                                                                                          role=kering.Roles.agent,
                                                                                          scheme=kering.Schemes.https)
            if kering.Roles.agent not in roleUrls:
                res['oobis'] = []
            else:
                aoobis = roleUrls[kering.Roles.agent]

                oobis = list()
                for agent in set(aoobis.keys()):
                    murls = aoobis.naball(agent)
                    for murl in murls:
                        urls = []
                        if kering.Schemes.http in murl:
                            urls.extend(murl.naball(kering.Schemes.http))
                        if kering.Schemes.https in murl:
                            urls.extend(murl.naball(kering.Schemes.https))
                        for url in urls:
                            up = urlparse(url)
                            oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/agent/{agent}"))

                res["oobis"] = oobis
        elif role in (kering.Roles.mailbox,):  # Fetch URL OOBIs for all witnesses
            roleUrls = (hab.fetchRoleUrls(cid=hab.pre, role=kering.Roles.mailbox, scheme=kering.Schemes.http) or
                        hab.fetchRoleUrls(cid=hab.pre, role=kering.Roles.mailbox, scheme=kering.Schemes.https))
            if kering.Roles.mailbox not in roleUrls:
                res['oobis'] = []
            else:
                aoobis = roleUrls[kering.Roles.mailbox]

                oobis = list()
                for mailbox in set(aoobis.keys()):
                    murls = aoobis.naball(mailbox)
                    for murl in murls:
                        urls = []
                        if kering.Schemes.http in murl:
                            urls.extend(murl.naball(kering.Schemes.http))
                        if kering.Schemes.https in murl:
                            urls.extend(murl.naball(kering.Schemes.https))
                        for url in urls:
                            up = urlparse(url)
                            oobis.append(urljoin(up.geturl(), f"/oobi/{hab.pre}/mailbox/{mailbox}"))

                res["oobis"] = oobis
        else:
            raise falcon.HTTPBadRequest(description=f"unsupport role type {role} for oobi request")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")


class EndRoleCollectionEnd:

    @staticmethod
    def on_get(req, rep, name=None, aid=None, role=None):
        """  GET endpoint for end role collection

        Parameters:
            req (Request): falcon HTTP request object
            rep (Response): falcon HTTP response object
            name (str): human readable alias for AID
            aid (str): aid to use instead of name
            role (str): optional role to search for

        ---
        summary: Retrieve end roles.
        description: This endpoint retrieves the end roles associated with AID or human-readable name.
                     It can also filter the end roles based on a specific role.
        tags:
        - End Role
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: false
          description: The human-readable name of the identifier.
        - in: path
          name: aid
          schema:
            type: string
          required: false
          description: The identifier (AID).
        - in: path
          name: role
          schema:
            type: string
          required: false
          description: The specific role to filter the end roles.
        responses:
            200:
                description: Successfully retrieved the end roles. The response body contains the end roles.
            400:
                description: Bad request. This could be due to missing or invalid parameters.
            404:
                description: The requested identifier was not found.
        """
        agent = req.context.agent

        if name is not None:
            hab = agent.hby.habByName(name)
            if hab is None:
                raise falcon.errors.HTTPNotFound(description=f"invalid alias {name}")
            pre = hab.pre
        elif aid is not None:
            pre = aid
        else:
            raise falcon.HTTPBadRequest(description="either `aid` or `name` are required in the path")

        if role is not None:
            keys = (pre, role,)
        else:
            keys = (pre,)

        ends = []
        for (_, erole, eid), end in agent.hby.db.ends.getItemIter(keys=keys):
            ends.append(dict(cid=pre, role=erole, eid=eid))

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(ends).encode("utf-8")

    @staticmethod
    def on_post(req, rep, name, aid=None, role=None):
        """ POST endpoint for end role collection

        Args:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object
            name (str): human readable alias for AID
            aid (str): Not supported for POST.  If provided, a 404 is returned
            role (str): Not supported for POST.  If provided, a 404 is returned

        ---
        summary: Create an end role.
        description: This endpoint creates an end role associated with a given identifier (AID) or name.
        tags:
        - End Role
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: The human-readable name of the identifier.
        - in: path
          name: aid
          schema:
            type: string
          required: false
          description: Not supported for POST. If provided, a 404 is returned.
        requestBody:
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    rpy:
                      type: object
                      description: The reply object.
                    sigs:
                      type: array
                      items:
                        type: string
                      description: The signatures.
        responses:
            202:
                description: Accepted. The end role creation is in progress.
            400:
                description: Bad request. This could be due to missing or invalid parameters.
            404:
                description: Not found. The requested identifier was not found.
        """
        if role is not None or aid is not None:
            raise falcon.HTTPNotFound(description="route not found")

        agent = req.context.agent
        body = req.get_media()

        rpy = httping.getRequiredParam(body, "rpy")
        rsigs = httping.getRequiredParam(body, "sigs")

        rserder = serdering.SerderKERI(sad=rpy)
        data = rserder.ked['a']
        pre = data['cid']
        role = data['role']
        eid = data['eid']

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.errors.HTTPNotFound(description=f"invalid alias {name}")

        if pre != hab.pre:
            raise falcon.errors.HTTPBadRequest(
                description=f"error trying to create end role for unknown local AID {pre}")

        rsigers = [core.Siger(qb64=rsig) for rsig in rsigs]
        tsg = (hab.kever.prefixer, coring.Seqner(sn=hab.kever.sn), coring.Saider(qb64=hab.kever.serder.said), rsigers)
        try:
            agent.hby.rvy.processReply(rserder, tsgs=[tsg])
        except kering.UnverifiedReplyError:
            pass

        oid = ".".join([pre, role, eid])
        op = agent.monitor.submit(oid, longrunning.OpTypes.endrole, metadata=dict(cid=pre, role=role, eid=eid))

        rep.content_type = "application/json"
        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class EndRoleResourceEnd:

    def on_delete(self, req, rep):
        pass


class RpyEscrowCollectionEnd:

    @staticmethod
    def on_get(req, rep):
        """
        GET endpoint for reply escrow collection

        Parameters:
            req (falcon.Request): The request object.
            rep (falcon.Response): The response object.

        ---
        summary: Retrieve reply escrows.
        description: This endpoint retrieves the reply escrows and can filter the collection based on a specific route.
        tags:
        - Reply Escrow
        parameters:
        - in: query
          name: route
          schema:
            type: string
          required: false
          description: The specific route to filter the reply escrow collection.
        responses:
            200:
                description: Successfully retrieved the reply escrows.
            400:
                description: Bad request. This could be due to missing or invalid parameters.
        """
        agent = req.context.agent

        # Optional Route parameter
        route = req.params.get("route")
        keys = (route,) if route is not None else ()
        events = []
        for saider in agent.hby.db.rpes.get(keys=keys):
            serder = agent.hby.db.rpys.get(keys=(saider.qb64,))
            events.append(serder.ked)

        rep.set_header("Content-Type", "application/json")
        rep.status = falcon.HTTP_200
        rep.data = json.dumps(events).encode("utf-8")


class ChallengeCollectionEnd:
    """ Resource for Challenge/Response Endpoints """

    @staticmethod
    def on_get(req, rep):
        """ Challenge GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary:  Get random list of words for a 2 factor auth challenge
        description:  Get the list of identifiers associated with this agent
        tags:
           - Challenge/Response
        parameters:
           - in: query
             name: strength
             schema:
                type: integer
             description:  cryptographic strength of word list
             required: false
        responses:
            200:
              description: An array of random words
              content:
                  application/json:
                    schema:
                        description: Random word list
                        type: object
                        properties:
                            words:
                                type: array
                                description: random challenge word list
                                items:
                                    type: string

        """
        mnem = mnemonic.Mnemonic(language='english')
        s = req.params.get("strength")
        strength = int(s) if s is not None else 128

        words = mnem.generate(strength=strength)
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        msg = dict(words=words.split(" "))
        rep.data = json.dumps(msg).encode("utf-8")


class ChallengeResourceEnd:
    """ Resource for Challenge/Response Endpoints """

    @staticmethod
    def on_post(req, rep, name):
        """ Challenge POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name: human readable name of identifier to use to sign the challenge/response

        ---
        summary:  Sign challenge message and forward to peer identifier
        description:  Sign a challenge word list received out of bands and send `exn` peer to peer message
                      to recipient
        tags:
           - Challenge/Response
        parameters:
          - in: path
            name: name
            schema:
              type: string
            required: true
            description: Human readable alias for the identifier to create
        requestBody:
            required: true
            content:
              application/json:
                schema:
                    description: Challenge response
                    properties:
                        recipient:
                          type: string
                          description: human readable alias recipient identifier to send signed challenge to
                        words:
                          type: array
                          description:  challenge in form of word list
                          items:
                              type: string
        responses:
           202:
              description: Success submission of signed challenge/response
        """
        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPBadRequest(description="no matching Hab for alias {name}")

        body = req.get_media()
        if "exn" not in body or "sig" not in body or "recipient" not in body:
            raise falcon.HTTPBadRequest(description="challenge response requires 'words', 'sig' and 'recipient'")

        exn = body["exn"]
        sig = body["sig"]
        recpt = body["recipient"]
        serder = serdering.SerderKERI(sad=exn)

        ims = bytearray(serder.raw)
        ims.extend(sig.encode("utf-8"))

        agent.hby.psr.parseOne(ims=bytearray(ims))

        agent.exchanges.append(dict(said=serder.said, pre=hab.pre, rec=recpt, topic='challenge'))

        rep.status = falcon.HTTP_202


class ChallengeVerifyResourceEnd:
    """ Resource for Challenge/Response Verification Endpoints """

    @staticmethod
    def on_post(req, rep, source):
        """ Challenge POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            source: qb64 AID of of source of signed response to verify

        ---
        summary:  Sign challenge message and forward to peer identifier
        description:  Sign a challenge word list received out of bands and send `exn` peer to peer message
                      to recipient
        tags:
           - Challenge/Response
        parameters:
          - in: path
            name: source
            schema:
              type: string
            required: true
            description: Human readable alias for the identifier to create
        requestBody:
            required: true
            content:
              application/json:
                schema:
                    description: Challenge response
                    properties:
                        recipient:
                          type: string
                          description: human readable alias recipient identifier to send signed challenge to
                        words:
                          type: array
                          description:  challenge in form of word list
                          items:
                              type: string
        responses:
           202:
              description: Success submission of signed challenge/response
        """
        agent = req.context.agent

        body = req.get_media()
        words = httping.getRequiredParam(body, "words")
        if source not in agent.hby.kevers:
            raise falcon.HTTPNotFound(description=f"challenge response source={source} not found")

        meta = dict(words=words)
        op = agent.monitor.submit(source, longrunning.OpTypes.challenge, metadata=meta)
        rep.status = falcon.HTTP_202
        rep.content_type = "application/json"
        rep.data = op.to_json().encode("utf-8")

        rep.status = falcon.HTTP_202

    @staticmethod
    def on_put(req, rep, source):
        """ Challenge PUT accept endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            source: qb64 AID of of source of signed response to verify

        ---
        summary:  Mark challenge response exn message as signed
        description:  Mark challenge response exn message as signed
        tags:
           - Challenge/Response
        parameters:
        - in: path
          name: source
          schema:
            type: string
          required: true
          description: Human readable alias for the identifier to create
        requestBody:
            required: true
            content:
              application/json:
                schema:
                    description: Challenge response
                    properties:
                        aid:
                          type: string
                          description: aid of signer of accepted challenge response
                        said:
                          type: array
                          description:  SAID of challenge message signed
                          items:
                              type: string
        responses:
           202:
              description: Success submission of signed challenge/response
        """
        agent = req.context.agent
        body = req.get_media()
        if "said" not in body:
            raise falcon.HTTPBadRequest(description="challenge response acceptance requires 'aid' and 'said'")

        if source not in agent.hby.kevers:
            raise falcon.HTTPNotFound(description=f"challenge response source={source} not found")

        said = body["said"]
        saider = coring.Saider(qb64=said)
        agent.hby.db.chas.add(keys=(source,), val=saider)

        rep.status = falcon.HTTP_202


class ContactCollectionEnd:

    def on_get(self, req, rep):
        """ Contact plural GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
        ---
        summary:  Get list of contact information associated with remote identifiers
        description:  Get list of contact information associated with remote identifiers.  All
                      information is metadata and kept in local storage only
        tags:
           - Contacts
        parameters:
          - in: query
            name: group
            schema:
              type: string
            required: false
            description: field name to group results by
          - in: query
            name: filter_field
            schema:
               type: string
            description: field name to search
            required: false
          - in: query
            name: filter_value
            schema:
               type: string
            description: value to search for
            required: false
        responses:
           200:
              description: List of contact information for remote identifiers
        """
        # TODO:  Add support for sorting
        agent = req.context.agent
        group = req.params.get("group")
        field = req.params.get("filter_field")
        val = req.params.get("filter_value")

        if group is not None:
            data = dict()
            values = agent.org.values(group, val)
            for value in values:
                contacts = agent.org.find(group, value)
                self.authn(agent, contacts)
                data[value] = contacts

            rep.status = falcon.HTTP_200
            rep.data = json.dumps(data).encode("utf-8")

        elif field is not None:
            val = req.params.get("filter_value")
            if val is None:
                raise falcon.HTTPBadRequest(description="filter_value if required if field_field is specified")

            contacts = agent.org.find(field=field, val=val)
            self.authn(agent, contacts)
            rep.status = falcon.HTTP_200
            rep.data = json.dumps(contacts).encode("utf-8")

        else:
            data = []
            contacts = agent.org.list()

            for contact in contacts:
                aid = contact["id"]
                if aid in agent.hby.kevers and aid not in agent.hby.prefixes:
                    data.append(contact)

            self.authn(agent, data)
            rep.status = falcon.HTTP_200
            rep.data = json.dumps(data).encode("utf-8")

    @staticmethod
    def authn(agent, contacts):
        for contact in contacts:
            aid = contact['id']

            ends = agent.agentHab.endsFor(aid)
            contact['ends'] = ends

            accepted = [saider.qb64 for saider in agent.hby.db.chas.get(keys=(aid,))]
            received = [saider.qb64 for saider in agent.hby.db.reps.get(keys=(aid,))]

            challenges = []
            for said in received:
                exn = agent.hby.db.exns.get(keys=(said,))
                challenges.append(dict(dt=exn.ked['dt'], words=exn.ked['a']['words'], said=said,
                                       authenticated=said in accepted))

            contact["challenges"] = challenges

            wellKnowns = []
            wkans = agent.hby.db.wkas.get(keys=(aid,))
            for wkan in wkans:
                wellKnowns.append(dict(url=wkan.url, dt=wkan.dt))

            contact["wellKnowns"] = wellKnowns


class ContactImageResourceEnd:

    @staticmethod
    def on_post(req, rep, prefix):
        """

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            prefix: qb64 identifier prefix of contact to associate with image

        ---
         summary: Uploads an image to associate with identifier.
         description: Uploads an image to associate with identifier.
         tags:
            - Contacts
         parameters:
           - in: path
             name: prefix
             schema:
                type: string
             description: identifier prefix to associate image to
         requestBody:
             required: true
             content:
                image/jpg:
                  schema:
                    type: string
                    format: binary
                image/png:
                  schema:
                    type: string
                    format: binary
         responses:
           200:
              description: Image successfully uploaded

        """
        agent = req.context.agent
        if prefix not in agent.hby.kevers:
            raise falcon.HTTPNotFound(description=f"{prefix} is not a known identifier.")

        if req.content_length > 1000000:
            raise falcon.HTTPBadRequest(description="image too big to save")

        agent.org.setImg(pre=prefix, typ=req.content_type, stream=req.bounded_stream)
        rep.status = falcon.HTTP_202

    @staticmethod
    def on_get(req, rep, prefix):
        """ Contact image GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            prefix: qb64 identifier prefix of contact information to get

       ---
        summary:  Get contact image for identifer prefix
        description:  Get contact image for identifer prefix
        tags:
           - Contacts
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of contact image to get
        responses:
           200:
              description: Contact information successfully retrieved for prefix
              content:
                  image/jpg:
                    schema:
                        description: Image
                        type: binary
           404:
              description: No contact information found for prefix
        """
        agent = req.context.agent
        if prefix not in agent.hby.kevers:
            raise falcon.HTTPNotFound(description=f"{prefix} is not a known identifier.")

        data = agent.org.getImgData(pre=prefix)
        if data is None:
            raise falcon.HTTPNotFound(description=f"no image available for {prefix}.")

        rep.status = falcon.HTTP_200
        rep.set_header('Content-Type', data["type"])
        rep.set_header('Content-Length', data["length"])
        rep.stream = agent.org.getImg(pre=prefix)


class ContactResourceEnd:

    @staticmethod
    def on_get(req, rep, prefix):
        """ Contact GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            prefix: qb64 identifier prefix of contact information to get

       ---
        summary:  Get contact information associated with single remote identifier
        description:  Get contact information associated with single remote identifier.  All
                      information is meta-data and kept in local storage only
        tags:
           - Contacts
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of contact to get
        responses:
           200:
              description: Contact information successfully retrieved for prefix
           404:
              description: No contact information found for prefix
        """
        agent = req.context.agent
        if prefix not in agent.hby.kevers:
            raise falcon.HTTPNotFound(description=f"{prefix} is not a known identifier.")

        contact = agent.org.get(prefix)
        if contact is None:
            raise falcon.HTTPNotFound(description="NOT FOUND")

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(contact).encode("utf-8")

    @staticmethod
    def on_post(req, rep, prefix):
        """ Contact plural GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            prefix: human readable name of identifier to replace contact information

       ---
        summary:  Create new contact information for an identifier
        description:  Creates new information for an identifier, overwriting all existing
                      information for that identifier
        tags:
           - Contacts
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix to add contact metadata to
        requestBody:
            required: true
            content:
              application/json:
                schema:
                    description: Contact information
                    type: object

        responses:
           200:
              description: Updated contact information for remote identifier
           400:
              description: Invalid identifier used to update contact information
           404:
              description: Prefix not found in identifier contact information
        """
        agent = req.context.agent
        body = req.get_media()
        if prefix not in agent.hby.kevers:
            raise falcon.HTTPNotFound(description="{prefix} is not a known identifier.  oobi required before contact "
                                                  "information")

        if prefix in agent.hby.prefixes:
            raise falcon.HTTPBadRequest(description=f"{prefix} is a local identifier, contact information only for "
                                                    f"remote identifiers")

        if "id" in body:
            del body["id"]

        if agent.org.get(prefix):
            raise falcon.HTTPBadRequest(description=f"contact data for {prefix} already exists")

        agent.org.replace(prefix, body)
        contact = agent.org.get(prefix)

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(contact).encode("utf-8")

    @staticmethod
    def on_put(req, rep, prefix):
        """ Contact PUT endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            prefix: qb64 identifier to update contact information

        ---
        summary:  Update provided fields in contact information associated with remote identifier prefix
        description:  Update provided fields in contact information associated with remote identifier prefix.  All
                      information is metadata and kept in local storage only
        tags:
           - Contacts
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix to add contact metadata to
        requestBody:
            required: true
            content:
              application/json:
                schema:
                    description: Contact information
                    type: object

        responses:
           200:
              description: Updated contact information for remote identifier
           400:
              description: Invalid identifier used to update contact information
           404:
              description: Prefix not found in identifier contact information
        """
        agent = req.context.agent
        body = req.get_media()
        if prefix not in agent.hby.kevers:
            raise falcon.HTTPNotFound(
                description=f"{prefix} is not a known identifier.  oobi required before contact information")

        if prefix in agent.hby.prefixes:
            raise falcon.HTTPBadRequest(
                description=f"{prefix} is a local identifier, contact information only for remote identifiers")

        if "id" in body:
            del body["id"]

        agent.org.update(prefix, body)
        contact = agent.org.get(prefix)

        rep.status = falcon.HTTP_200
        rep.data = json.dumps(contact).encode("utf-8")

    @staticmethod
    def on_delete(req, rep, prefix):
        """ Contact plural GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            prefix: qb64 identifier prefix to delete contact information

        ---
        summary:  Delete contact information associated with remote identifier
        description:  Delete contact information associated with remote identifier
        tags:
           - Contacts
        parameters:
          - in: path
            name: prefix
            schema:
              type: string
            required: true
            description: qb64 identifier prefix of contact to delete
        responses:
           202:
              description: Contact information successfully deleted for prefix
           404:
              description: No contact information found for prefix
        """
        agent = req.context.agent
        deleted = agent.org.rem(prefix)
        if not deleted:
            raise falcon.HTTPNotFound(description=f"no contact information to delete for {prefix}")

        rep.status = falcon.HTTP_202


class GroupMemberCollectionEnd:

    @staticmethod
    def on_get(req, rep, name):
        agent = req.context.agent

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.errors.HTTPNotFound(description=f"invalid alias {name}")

        if not isinstance(hab, habbing.SignifyGroupHab):
            raise falcon.HTTPBadRequest(description="members endpoint only available for group AIDs")

        smids = hab.db.signingMembers(hab.pre)
        rmids = hab.db.rotationMembers(hab.pre)

        signing = []
        for smid in smids:
            ends = hab.endsFor(smid)
            signing.append(dict(aid=smid, ends=ends))

        rotation = []
        for rmid in rmids:
            ends = hab.endsFor(rmid)
            rotation.append(dict(aid=rmid, ends=ends))

        data = dict(signing=signing, rotation=rotation)
        rep.status = falcon.HTTP_200
        rep.data = json.dumps(data).encode("utf-8")
