# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.ending module

"""
import json
from dataclasses import asdict
from urllib.parse import urlparse

import falcon
from keri import kering
from keri.app import habbing
from keri.app.keeping import Algos
from keri.core import coring
from keri.core.coring import Ilks
from keri.db import dbing
from keri.help import ogler
from mnemonic import mnemonic

from ..core import longrunning, httping

logger = ogler.getLogger()


def loadEnds(app, agency, authn):
    agentEnd = AgentResourceEnd(agency=agency, authn=authn)
    app.add_route("/agent/{caid}", agentEnd)

    aidsEnd = IdentifierCollectionEnd()
    app.add_route("/identifiers", aidsEnd)
    aidEnd = IdentifierResourceEnd()
    app.add_route("/identifiers/{name}", aidEnd)

    aidOOBIsEnd = IdentifierOOBICollectionEnd()
    app.add_route("/identifiers/{name}/oobis", aidOOBIsEnd)

    endRolesEnd = EndRoleCollectionEnd()
    app.add_route("/identifiers/{name}/endroles", endRolesEnd)

    endRoleEnd = EndRoleResourceEnd()
    app.add_route("/identifiers/{name}/endroles/{cid}/{role}/{eid}", endRoleEnd)

    chaEnd = ChallengeCollectionEnd()
    app.add_route("/challenges", chaEnd)
    chaResEnd = ChallengeResourceEnd()
    app.add_route("/challenges/{name}", chaResEnd)

    contactColEnd = ContactCollectionEnd()
    app.add_route("/contacts", contactColEnd)
    contactResEnd = ContactResourceEnd()
    app.add_route("/contacts/{prefix}", contactResEnd)
    contactImgEnd = ContactImageResourceEnd()
    app.add_route("/contacts/{prefix}/img", contactImgEnd)

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

        """
        agent = self.agency.get(caid)
        if agent is None:
            raise falcon.HTTPNotFound(description=f"not agent found for controller {caid}")

        if agent.pre not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(description=f"invalid agent configuration, {agent.pre} not found")

        if agent.caid not in agent.hby.kevers:
            raise falcon.HTTPBadRequest(description=f"invalid controller configuration, {agent.caid} not found")

        pidx = agent.hby.db.habs.cntAll()

        state = asdict(agent.hby.kevers[agent.caid].state())
        key = dbing.dgKey(state['i'], state['ee']['d'])  # digest key
        msg = agent.hby.db.getEvt(key)
        eserder = coring.Serder(raw=bytes(msg))

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

        """
        agent = self.agency.get(caid)
        if agent is None:
            raise falcon.HTTPNotFound(f"no agent for {caid}")

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

        rot = coring.Serder(ked=body["rot"])
        sigs = body["sigs"]

        ctrlHab = agent.hby.habByName(caid, ns="agent")
        ctrlHab.rotate(serder=rot, sigers=[coring.Siger(qb64=sig) for sig in sigs])

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
                    cipher = coring.Cipher(qb64=prx)
                    agent.mgr.rb.prxs.put(keys=verfers[idx].qb64b, val=cipher)

                if "nxts" in val:
                    nxts = val["nxts"]
                    if len(nxts) != len(digers):
                        raise ValueError("If encrypted private next keys are provided, must match digers")

                    for idx, prx in enumerate(nxts):
                        cipher = coring.Cipher(qb64=prx)
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
        ixn = coring.Serder(ked=ked)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

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
    def on_get(req, rep):
        """ Identifier List GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        """
        agent = req.context.agent
        res = []

        last = req.params.get("last")
        limit = req.params.get("limit")

        limit = limit if not limit is None else "25"
        last = last if last is not None else ""

        for name, habord in agent.hby.db.habs.getItemIter(keys=(last,)):
            name = ".".join(name)  # detupleize the database key name
            if len(res) == int(limit, 10):
                break

            hab = agent.hby.habByName(name)
            data = info(hab, agent.mgr)
            res.append(data)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    @staticmethod
    def on_post(req, rep):
        """ Inception event POST endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """
        agent = req.context.agent
        deserialized_media = req.get_media()
        try:
            body = req.get_media()
            icp = httping.getRequiredParam(body, "icp")
            name = httping.getRequiredParam(body, "name")
            sigs = httping.getRequiredParam(body, "sigs")

            serder = coring.Serder(ked=icp)

            sigers = [coring.Siger(qb64=sig) for sig in sigs]

            # client is requesting agent to join multisig group
            if "group" in body:
                agent.agency.intercepts.append(dict(event="creat multisig aid", data=deserialized_media))
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

                smids = httping.getRequiredParam(body, "smids")
                rmids = httping.getRequiredParam(body, "rmids")

                hab = agent.hby.makeSignifyGroupHab(name, mhab=mhab, serder=serder, sigers=sigers)
                try:
                    agent.inceptGroup(pre=serder.pre, mpre=mhab.pre, verfers=verfers, digers=digers)
                except ValueError as e:
                    agent.hby.deleteHab(name=name)
                    raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")
                agent.agency.intercepts.append(dict(event="multisig created", data=serder.pretty()))
                # Generate response, a long running operaton indicator for the type
                agent.groups.append(dict(pre=hab.pre, serder=serder, sigers=sigers, smids=smids, rmids=rmids))
                op = agent.monitor.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=0))

                rep.content_type = "application/json"
                rep.status = falcon.HTTP_202
                rep.data = op.to_json().encode("utf-8")

            else:
                # client is requesting that the Agent track the Salty parameters
                if Algos.salty in body:
                    agent.agency.intercepts.append(dict(event="create salty aid", data=serder.pretty()))
                    salt = body[Algos.salty]
                    hab = agent.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        agent.inceptSalty(pre=serder.pre, **salt)
                    except ValueError as e:
                        agent.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                # client is storing encrypted randomly generated key material on agent
                elif Algos.randy in body:
                    agent.agency.intercepts.append(dict(event="create randy aid", data=serder.pretty()))
                    rand = body[Algos.randy]
                    hab = agent.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        agent.inceptRandy(pre=serder.pre, verfers=serder.verfers, digers=serder.digers, **rand)
                    except ValueError as e:
                        agent.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                elif Algos.extern in body:
                    agent.agency.intercepts.append(dict(event="create extern aid", data=serder.pretty()))
                    extern = body[Algos.extern]
                    hab = agent.hby.makeSignifyHab(name, serder=serder, sigers=sigers)
                    try:
                        agent.inceptExtern(pre=serder.pre, verfers=serder.verfers, digers=serder.digers, **extern)
                    except ValueError as e:
                        agent.hby.deleteHab(name=name)
                        raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

                else:
                    raise falcon.HTTPBadRequest(
                        description="invalid request: one of group, rand or salt field required")

                # create Hab and incept the key store (if any)
                # Generate response, either the serder or a long running operaton indicator for the type
                rep.content_type = "application/json"
                if hab.kever.delegator:
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
            name (str): human readable name for Hab to GET

        """
        agent = req.context.agent
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPNotFound(description=f"{name} is not a valid identifier name")

        data = info(hab, agent.mgr, full=True)
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
        agent = req.context.agent
        try:
            body = req.get_media()
            typ = Ilks.ixn if req.params.get("type") == "ixn" else Ilks.rot

            if typ in (Ilks.rot,):
                op = self.rotate(agent, name, body)
            else:
                op = self.interact(agent, name, body)

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

        sigs = body.get("sigs")
        if sigs is None or len(sigs) == 0:
            raise falcon.HTTPBadRequest(title="invalid rotation",
                                        description=f"required field 'sigs' missing from request")

        serder = coring.Serder(ked=rot)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

        hab.rotate(serder=serder, sigers=sigers)

        if Algos.salty in body:
            salt = body[Algos.salty]
            keeper = agent.mgr.get(Algos.salty)

            try:
                keeper.rotate(pre=serder.pre, **salt)
            except ValueError as e:
                agent.hby.deleteHab(name=name)
                raise falcon.HTTPInternalServerError(description=f"{e.args[0]}")

        elif Algos.randy in body:
            rand = body[Algos.randy]
            keeper = agent.mgr.get(Algos.randy)

            keeper.rotate(pre=serder.pre, verfers=serder.verfers, digers=serder.digers, **rand)

        elif Algos.group in body:
            keeper = agent.mgr.get(Algos.group)

            keeper.rotate(pre=serder.pre, verfers=serder.verfers, digers=serder.digers)

            smids = httping.getRequiredParam(body, "smids")
            rmids = httping.getRequiredParam(body, "rmids")

            agent.groups.append(dict(pre=hab.pre, serder=serder, sigers=sigers, smids=smids, rmids=rmids))
            op = agent.monitor.submit(serder.pre, longrunning.OpTypes.group, metadata=dict(sn=serder.sn))

            return op

        if hab.kever.delegator:
            agent.anchors.append(dict(alias=name, pre=hab.pre, sn=0))
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

        serder = coring.Serder(ked=ixn)
        sigers = [coring.Siger(qb64=sig) for sig in sigs]

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

    if not isinstance(hab, habbing.SignifyHab):
        raise kering.ConfigurationError("agent only allows SignifyHab instances")

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
        data["windexes"] = [coring.Siger(qb64b=bytes(wig)).index for wig in wigs]

    return data


class IdentifierOOBICollectionEnd:
    """
      This class represents the OOBI subresource collection endpoint for Identfiiers

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
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http)
                if not urls:
                    raise falcon.HTTPNotFound(f"unable to query witness {wit}, no http endpoint")

                up = urlparse(urls[kering.Schemes.http])
                oobis.append(f"{kering.Schemes.http}://{up.hostname}:{up.port}/oobi/{hab.pre}/witness/{wit}")
            res["oobis"] = oobis
        elif role in (kering.Roles.controller,):  # Fetch any controller URL OOBIs
            oobis = []
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http)
            if not urls:
                raise falcon.HTTPNotFound(description=f"unable to query controller {hab.pre}, no http endpoint")

            up = urlparse(urls[kering.Schemes.http])
            oobis.append(f"{kering.Schemes.http}://{up.hostname}:{up.port}/oobi/{hab.pre}/controller")
            res["oobis"] = oobis
        elif role in (kering.Roles.agent,):  # Fetch URL OOBIs for all witnesses
            roleUrls = hab.fetchRoleUrls(cid=hab.pre, role=kering.Roles.agent, scheme=kering.Schemes.http)
            aoobis = roleUrls[kering.Roles.agent]

            oobis = list()
            for agent in set(aoobis.keys()):
                murls = aoobis.naball(agent)
                for murl in murls:
                    for url in murl.naball(kering.Schemes.http):
                        up = urlparse(url)
                        oobis.append(f"{kering.Schemes.http}://{up.hostname}:{up.port}/oobi/{hab.pre}/agent/{agent}")

            res["oobis"] = oobis
        else:
            raise falcon.HTTPBadRequest(description=f"unsupport role type {role} for oobi request")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")


class EndRoleCollectionEnd:

    @staticmethod
    def on_post(req, rep, name):
        """

        Args:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object
            name (str): human readable alias for AID

        """
        agent = req.context.agent
        body = req.get_media()

        rpy = httping.getRequiredParam(body, "rpy")
        rsigs = httping.getRequiredParam(body, "sigs")

        rserder = coring.Serder(ked=rpy)
        data = rserder.ked['a']
        pre = data['cid']
        role = data['role']
        eid = data['eid']

        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.errors.HTTPNotFound(f"invalid alias {name}")

        if pre != hab.pre:
            raise falcon.errors.HTTPBadRequest(description=f"error trying to create end role for unknown local AID {pre}")

        rsigers = [coring.Siger(qb64=rsig) for rsig in rsigs]
        tsg = (hab.kever.prefixer, coring.Seqner(sn=hab.kever.sn), hab.kever.serder.saider, rsigers)
        agent.hby.rvy.processReply(rserder, tsgs=[tsg])

        msg = hab.loadEndRole(cid=pre, role=role, eid=eid)
        if msg is None:
            raise falcon.errors.HTTPBadRequest(description=f"invalid end role rpy={rserder.ked}")

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = rserder.raw


class EndRoleResourceEnd:

    def on_delete(self, req, rep):
        pass


class ChallengeCollectionEnd:
    """ Resource for Challenge/Response Endpoints """

    @staticmethod
    def on_get(req, rep):
        """ Challenge GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary:  Get list of agent identifiers
        description:  Get the list of identifiers associated with this agent
        tags:
           - Challenge/Response
        parameters:
           - in: query
             name: strength
             schema:
                type: int
             description:  cryptographic strength of word list
             required: false
        responses:
            200:
              description: An array of Identifier key state information
              content:
                  application/json:
                    schema:
                        description: Randon word list
                        type: object
                        properties:
                            words:
                                type: array
                                description: random challange word list
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
            name: human readable name of identifier to use to sign the challange/response

        ---
        summary:  Sign challange message and forward to peer identfiier
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
        serder = coring.Serder(ked=exn)
        atc = bytearray(sig.encode("utf-8"))
        agent.postman.send(hab=agent.agentHab, dest=recpt, topic="challenge", serder=serder, attachment=atc)

        rep.status = falcon.HTTP_202

    @staticmethod
    def on_put(req, rep, name):
        """ Challenge PUT accept endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name: human readable name of identifier to use to sign the challange/response

        ---
        summary:  Mark challenge response exn message as signed
        description:  Mark challenge response exn message as signed
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
        hab = agent.hby.habByName(name)
        if hab is None:
            raise falcon.HTTPBadRequest(description="no matching Hab for alias {name}")

        body = req.get_media()
        if "aid" not in body or "said" not in body:
            raise falcon.HTTPBadRequest(description="challenge response acceptance requires 'aid' and 'said'")

        aid = body["aid"]
        said = body["said"]
        saider = coring.Saider(qb64=said)
        agent.hby.db.chas.add(keys=(aid,), val=saider)

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
         summary: Uploads an image to associate with identfier.
         description: Uploads an image to associate with identfier.
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
        summary:  Get contact information associated with single remote identfier
        description:  Get contact information associated with single remote identfier.  All
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
              description: Invalid identfier used to update contact information
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
        summary:  Update provided fields in contact information associated with remote identfier prefix
        description:  Update provided fields in contact information associated with remote identfier prefix.  All
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
              description: Invalid identfier used to update contact information
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
        summary:  Delete contact information associated with remote identfier
        description:  Delete contact information associated with remote identfier
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

