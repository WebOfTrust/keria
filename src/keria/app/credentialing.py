# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.credentialing module

services and endpoint for ACDC credential managements
"""

import json
from dataclasses import asdict, dataclass, field

import falcon
from hio.base import doing
from keri import kering, help
from keri.app import signing, grouping as keri_grouping
from keri.app.habbing import SignifyGroupHab
from keri.core import coring, scheming, serdering
from keri.db import dbing
from keri.db.dbing import dgKey
from keri.help import helping
from keri.peer import exchanging
from keri.vdr import viring, credentialing as vdr_credentialing

from ..utils.openapi import dataclassFromFielddom
from keri.core.serdering import Protocols, Vrsn_1_0, Vrsn_2_0, SerderKERI
from ..core import httping, longrunning
from .multisig import replay_multisig_embeds
from marshmallow import fields, Schema as MarshmallowSchema
from typing import List, Dict, Any, Optional, Tuple, Literal, Union
from .aiding import (
    Seal,
    ICP_V_1,
    ICP_V_2,
    ROT_V_1,
    ROT_V_2,
    DIP_V_1,
    DIP_V_2,
    DRT_V_1,
    DRT_V_2,
    IXN_V_1,
    IXN_V_2,
)


logger = help.ogler.getLogger()


def loadEnds(app, identifierResource):
    schemaColEnd = SchemaCollectionEnd()
    app.add_route("/schema", schemaColEnd)
    schemaResEnd = SchemaResourceEnd()
    app.add_route("/schema/{said}", schemaResEnd)

    registryEnd = RegistryCollectionEnd(identifierResource)
    app.add_route("/identifiers/{name}/registries", registryEnd)
    registrySyncEnd = RegistrySyncCollectionEnd()
    app.add_route("/identifiers/{name}/registries/sync", registrySyncEnd)

    registryResEnd = RegistryResourceEnd()
    app.add_route("/identifiers/{name}/registries/{registryName}", registryResEnd)

    credentialCollectionEnd = CredentialCollectionEnd(identifierResource)
    app.add_route("/identifiers/{name}/credentials", credentialCollectionEnd)
    credentialSyncEnd = CredentialSyncCollectionEnd()
    app.add_route("/identifiers/{name}/credentials/sync", credentialSyncEnd)

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


def loadHandlers(agent, exc):
    """Register machine-handled EXN routes for late-join sync workflows."""
    exc.addHandler(RegistrySyncRequestHandler(agent=agent))
    exc.addHandler(RegistrySyncResponseHandler(agent=agent))
    exc.addHandler(CredentialSyncRequestHandler(agent=agent))
    exc.addHandler(CredentialSyncResponseHandler(agent=agent))


def _resolve_identifier(agent, name):
    return agent.hby.habs[name] if name in agent.hby.habs else agent.hby.habByName(name)


def _resolve_group_identifier(agent, name):
    hab = _resolve_identifier(agent, name)
    if hab is None:
        raise falcon.HTTPNotFound(
            description=f"{name} is not a valid reference to an identifier"
        )
    if not isinstance(hab, SignifyGroupHab):
        raise falcon.HTTPConflict(
            description=f"hab for alias or prefix {name} is not a multisig"
        )
    return hab


def _has_endpoint(agent, aid):
    ends = agent.agentHab.endsFor(aid)
    for role_ends in ends.values():
        for locs in role_ends.values():
            if locs:
                return True
    return False


def _agent_authorized_for_member(agent, member, eid):
    return eid in agent.agentHab.endsFor(member).get("agent", {})


def _eligible_regsync_sources(agent, hab):
    members = hab.db.signingMembers(pre=hab.pre) or []
    eligible = [
        member
        for member in sorted(members)
        if member != hab.mhab.pre and member in agent.hby.kevers and _has_endpoint(agent, member)
    ]
    return eligible


def _select_regsync_source(agent, hab, source=None):
    eligible = _eligible_regsync_sources(agent, hab)
    if source is None:
        if not eligible:
            raise falcon.HTTPConflict(
                description=f"no eligible registry sync sources found for {hab.pre}"
            )
        return eligible[0]

    try:
        coring.Prefixer(qb64=source)
    except kering.ValidationError as ex:
        raise falcon.HTTPBadRequest(description=str(ex)) from ex

    if source not in eligible:
        raise falcon.HTTPConflict(
            description=f"{source} is not an eligible registry sync source for {hab.pre}"
        )

    return source


def _sync_op_name(optype, pre):
    return f"{optype}.{pre}"


def _regsync_op_name(pre):
    return _sync_op_name(longrunning.OpTypes.regsync, pre)


def _credsync_op_name(pre):
    return _sync_op_name(longrunning.OpTypes.credsync, pre)


def _update_sync_error(agent, name, code, message, details=None):
    op = agent.monitor.opr.ops.get(keys=(name,))
    if op is None:
        return

    metadata = dict(op.metadata)
    metadata["error"] = dict(code=code, message=message, details=details)
    agent.monitor.update(name, metadata=metadata)


def _update_regsync_error(agent, name, code, message, details=None):
    _update_sync_error(agent, name, code, message, details=details)


def _update_credsync_error(agent, name, code, message, details=None):
    _update_sync_error(agent, name, code, message, details=details)


def _find_sync_by_request(agent, request_said, optype):
    for _, op in agent.monitor.opr.ops.getItemIter():
        if op.type != optype:
            continue
        if op.metadata.get("request") != request_said:
            continue
        return _sync_op_name(op.type, op.oid), op

    return None, None


def _find_regsync_by_request(agent, request_said):
    return _find_sync_by_request(agent, request_said, longrunning.OpTypes.regsync)


def _find_credsync_by_request(agent, request_said):
    return _find_sync_by_request(agent, request_said, longrunning.OpTypes.credsync)


def _current_credential_regk(creder):
    if getattr(creder, "regi", None) is not None:
        return creder.regi

    sad = creder.sad if hasattr(creder, "sad") else creder
    if sad.get("ri") is not None:
        return sad["ri"]
    if sad.get("rd") is not None:
        return sad["rd"]

    return None


def _materialize_signify_registry(agent, name, prefix, regk):
    hab = agent.hby.habs[prefix]
    if hab is None:
        raise kering.ConfigurationError(
            f"Unknown prefix {prefix} for creating Registry {name}"
        )

    registry = vdr_credentialing.SignifyRegistry(
        hab=hab,
        name=name,
        reger=agent.rgy.reger,
        tvy=agent.rgy.tvy,
        psr=agent.rgy.psr,
        cues=agent.rgy.cues,
        regk=regk,
    )
    registry.inited = True

    agent.rgy.reger.regs.put(
        keys=name,
        val=viring.RegistryRecord(registryKey=regk, prefix=prefix),
    )
    agent.rgy.reger.registries.add(regk)
    agent.rgy.regs[regk] = registry

    return registry


def _validate_sync_saids(body):
    saids = body.get("saids")
    if not isinstance(saids, list) or len(saids) == 0:
        raise falcon.HTTPBadRequest(
            description="'saids' is required and must be a non-empty list"
        )

    deduped = []
    seen = set()
    for said in saids:
        if not isinstance(said, str):
            raise falcon.HTTPBadRequest(
                description="'saids' entries must be qb64 credential SAIDs"
            )
        try:
            coring.Saider(qb64=said)
        except kering.ValidationError as ex:
            raise falcon.HTTPBadRequest(description=str(ex)) from ex

        if said in seen:
            continue

        seen.add(said)
        deduped.append(said)

    return deduped


def _registry_sync_request_exn(hab, gid, mid=None):
    helper = getattr(keri_grouping, "multisigRegistrySyncRequestExn", None)
    if helper is not None and mid is None:
        return helper(hab=hab, gid=gid)

    payload = dict(gid=gid)
    if mid is not None:
        payload["mid"] = mid

    exn, end = exchanging.exchange(
        route="/multisig/registry/sync",
        payload=payload,
        sender=hab.pre,
    )
    evt = hab.endorse(serder=exn, last=False, pipelined=False)
    atc = bytearray(evt[exn.size:])
    atc.extend(end)
    return exn, atc


def _credential_sync_request_exn(hab, gid, saids, mid=None):
    helper = getattr(keri_grouping, "multisigCredentialSyncRequestExn", None)
    if helper is not None:
        try:
            return helper(hab=hab, gid=gid, saids=saids, mid=mid)
        except TypeError:
            pass

    payload = dict(gid=gid, saids=saids)
    if mid is not None:
        payload["mid"] = mid

    exn, end = exchanging.exchange(
        route="/multisig/credential/sync",
        payload=payload,
        sender=hab.pre,
    )
    evt = hab.endorse(serder=exn, last=False, pipelined=False)
    atc = bytearray(evt[exn.size:])
    atc.extend(end)
    return exn, atc


def _registry_sync_response_exn(hab, gid, registries, dig, history=None, messages=None):
    helper = getattr(keri_grouping, "multisigRegistrySyncResponseExn", None)
    if helper is not None and history is None and messages is None:
        try:
            return helper(
                hab=hab,
                gid=gid,
                registries=registries,
                dig=dig,
            )
        except TypeError:
            return helper(hab=hab, gid=gid, registries=registries, dig=dig)

    if messages is not None:
        embeds = _message_embeds(messages, prefix="vcpmsg")
    else:
        embeds = dict(history=history) if history is not None else None

    exn, end = exchanging.exchange(
        route="/multisig/registry/sync/response",
        payload=dict(gid=gid, registries=registries),
        sender=hab.pre,
        dig=dig,
        embeds=embeds,
    )
    evt = hab.endorse(serder=exn, last=False, pipelined=False)
    atc = bytearray(evt[exn.size:])
    atc.extend(end)
    return exn, atc


def _credential_sync_response_exn(
    hab,
    gid,
    said,
    dig,
    credential=None,
    error=None,
    messages=None,
    schemas=None,
):
    helper = getattr(keri_grouping, "multisigCredentialSyncResponseExn", None)
    if helper is not None and error is None and messages is None:
        try:
            return helper(hab=hab, gid=gid, said=said, credential=credential, dig=dig)
        except TypeError:
            pass

    payload = dict(gid=gid, said=said)
    if error is not None:
        payload["error"] = error
    if schemas is not None:
        payload["schemas"] = schemas

    if messages is not None:
        embeds = _message_embeds(messages, prefix="credmsg")
    else:
        embeds = dict(cred=credential) if credential is not None else None
    exn, end = exchanging.exchange(
        route="/multisig/credential/sync/response",
        payload=payload,
        sender=hab.pre,
        dig=dig,
        embeds=embeds,
    )
    evt = hab.endorse(serder=exn, last=False, pipelined=False)
    atc = bytearray(evt[exn.size:])
    atc.extend(end)
    return exn, atc


def _embedded_stream_from_attachments(serder, attachments, label):
    embeds = serder.ked.get("e", {})
    if label not in embeds:
        return None

    if attachments:
        for pather, atc in attachments:
            if not pather.path or pather.path[0] != label:
                continue

            ked = pather.resolve(embeds)
            sadder = coring.Sadder(ked=ked)
            ims = bytearray(sadder.raw)
            ims.extend(atc)
            return ims

    return bytearray(coring.Sadder(ked=embeds[label]).raw)


def _embedded_messages_from_attachments(serder, attachments, prefix):
    embeds = serder.ked.get("e", {})
    labels = sorted(
        label for label in embeds.keys() if label != "d" and label.startswith(prefix)
    )

    if not labels:
        return []

    attachment_map = {}
    for pather, atc in attachments:
        if not pather.path:
            continue

        attachment_map[pather.path[0]] = atc

    messages = []
    for label in labels:
        ims = bytearray(coring.Sadder(ked=embeds[label]).raw)
        if label in attachment_map:
            ims.extend(attachment_map[label])
        messages.append(ims)

    return messages


def _credential_chain_saids(creder):
    chains = creder.edge or dict()
    saids = []
    for key, source in chains.items():
        if key == "d":
            continue

        if not isinstance(source, dict):
            continue

        saids.append(source["n"])

    return saids


def _message_embeds(messages, prefix):
    return {
        f"{prefix}{idx:04d}": bytes(message)
        for idx, message in enumerate(messages)
    }


def _credential_sync_messages(hby, rgy, said, seen=None):
    seen = set() if seen is None else seen
    if said in seen:
        return []

    seen.add(said)
    messages = []
    creder, prefixer, seqner, saider = rgy.reger.cloneCred(said=said)
    for chain_said in _credential_chain_saids(creder):
        messages.extend(_credential_sync_messages(hby, rgy, chain_said, seen=seen))

    for msg in hby.db.clonePreIter(pre=creder.issuer):
        messages.append(bytes(msg))

    if "i" in creder.attrib:
        subj = creder.attrib["i"]
        for msg in hby.db.clonePreIter(pre=subj):
            messages.append(bytes(msg))

    if creder.regi is not None:
        for msg in rgy.reger.clonePreIter(pre=creder.regi):
            messages.append(bytes(msg))

        for msg in rgy.reger.clonePreIter(pre=creder.said):
            messages.append(bytes(msg))

    messages.append(bytes(signing.serialize(creder, prefixer, seqner, saider)))
    return messages


def _credential_sync_schemas(hby, rgy, said, seen=None):
    seen = set() if seen is None else seen
    if said in seen:
        return []

    seen.add(said)
    schemas = []
    creder, _, _, _ = rgy.reger.cloneCred(said=said)
    for chain_said in _credential_chain_saids(creder):
        schemas.extend(_credential_sync_schemas(hby, rgy, chain_said, seen=seen))

    if (schemer := hby.db.schema.get(creder.schema)) is not None:
        schemas.append(dict(schemer.sed))

    return schemas


def _registry_anchor(regk, regd, sn="0"):
    return dict(i=regk, s=sn, d=regd)


def _query_group_anchor_for_tel_message(agent, gid, group_hab, message):
    """Backfill or query the group KEL event that seals a synced TEL message."""

    try:
        serder = SerderKERI(raw=bytes(message))
    except Exception:
        return

    if serder.ked.get("t") not in {"vcp", "vrt", "iss", "bis", "rev", "brv"}:
        return

    seal = dict(i=serder.pre, s=serder.snh, d=serder.said)
    if longrunning.ensure_tel_anchor(
        hby=agent.hby,
        reger=agent.rgy.reger,
        gid=gid,
        pre=serder.pre,
        said=serder.said,
        anchor=seal,
    ):
        return

    agent.witq.query(
        hab=agent.agentHab,
        pre=gid,
        anchor=seal,
        wits=group_hab.kever.wits or None,
    )


def _cache_embedded_schemas(agent, serder, attachments):
    payload = serder.ked.get("a", {})
    schemas = payload.get("schemas", [])
    for sed in schemas:
        schemer = scheming.Schemer(sed=sed)
        agent.verifier.resolver.add(schemer.said, schemer.raw)

    return schemas


class EmptyDictSchema(MarshmallowSchema):
    class Meta:
        additional = ()


@dataclass
class ACDCAttributes:
    dt: Optional[str] = field(
        default=None, metadata={"marshmallow_field": fields.String(allow_none=False)}
    )
    i: Optional[str] = field(
        default=None, metadata={"marshmallow_field": fields.String(allow_none=False)}
    )
    u: Optional[str] = field(
        default=None, metadata={"marshmallow_field": fields.String(allow_none=False)}
    )
    # Override the schema to force additionalProperties=True


acdcCustomTypes = {
    "a": ACDCAttributes,
    "A": Union[str, List[Any]],
}
acdcFieldDomV1 = SerderKERI.Fields[Protocols.acdc][Vrsn_1_0][None]
ACDC_V_1, ACDCSchema_V_1 = dataclassFromFielddom(
    "ACDC_V_1", acdcFieldDomV1, acdcCustomTypes
)
acdcFieldDomV2 = SerderKERI.Fields[Protocols.acdc][Vrsn_2_0][None]
ACDC_V_2, ACDCSchema_V_2 = dataclassFromFielddom(
    "ACDC_V_2", acdcFieldDomV2, acdcCustomTypes
)


@dataclass
class IssEvent:
    v: str
    t: Literal["iss", "bis"]
    d: str
    i: str
    s: str
    ri: str
    dt: str


@dataclass
class Schema:
    id_: str = field(metadata={"data_key": "$id"})
    schema: str = field(metadata={"data_key": "$schema"})
    title: str
    description: str
    type: str
    credentialType: str
    version: str
    properties: Dict[str, Any]
    additionalProperties: bool
    required: List[str]


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
    et: Literal["iss", "rev"]
    ra: Dict[str, Any] = field(
        metadata={
            "marshmallow_field": fields.Nested(
                EmptyDictSchema(), allow_none=False, required=True
            )
        }
    )


@dataclass
class RaFields:
    i: str
    s: str
    d: str


@dataclass
class CredentialStateBisOrBrv(CredentialStateBase):
    et: Literal["bis", "brv"]
    ra: RaFields


@dataclass
class Anchor:
    pre: str
    sn: int
    d: str


AnchoringEvent = Union[
    IXN_V_1,
    IXN_V_2,
    ICP_V_1,
    ICP_V_2,
    ROT_V_1,
    ROT_V_2,
    DIP_V_1,
    DIP_V_2,
    DRT_V_1,
    DRT_V_2,
]


@dataclass
class ClonedCredential:
    sad: Union[
        "ACDC_V_1", "ACDC_V_2"
    ]  # Use string annotation for dynamically generated class
    atc: str
    iss: IssEvent
    issatc: str
    pre: str
    schema: Schema
    chains: List[Dict[str, Any]]
    status: Union[CredentialStateIssOrRev, CredentialStateBisOrBrv]
    anchor: Anchor
    anc: AnchoringEvent  # type: ignore
    ancatc: str


@dataclass
class Registry:
    name: str
    regk: str
    pre: str
    state: Union[CredentialStateIssOrRev, CredentialStateBisOrBrv]


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
        """Registries GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID

        ---
        summary: List credential issuance and revocation registries
        description: List credential issuance and revocation registries
        operationId: listRegistries
        tags:
           - Registries
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: human readable name or prefix of Hab to load credentials for
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
           404:
              description: The requested registry is not a valid reference to an identifier

        """
        agent = req.context.agent

        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        res = []
        for name, registry in agent.rgy.regs.items():
            if (
                registry.regk not in registry.tevers
            ):  # defensive programming for a registry not being fully committed
                continue

            if registry.hab.pre == hab.pre:
                rd = dict(
                    name=registry.name,
                    regk=registry.regk,
                    pre=registry.hab.pre,
                    state=asdict(registry.tever.state()),
                )
                res.append(rd)

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(res).encode("utf-8")

    def on_post(self, req, rep, name):
        """Registries POST endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix of Hab to load credentials for

        ---
        summary: Request to create a credential issuance and revocation registry
        description: Request to create a credential issuance and revocation registry
        operationId: createRegistry
        tags:
           - Registries
        parameters:
        - in: path
          name: name
          schema:
            type: string
          required: true
          description: human readable name or prefix of Hab to load credentials for
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
                      description: True means to not allow seperate backers from identifier's witnesses.
                    baks:
                      type: array
                      items:
                         type: string
                      description: List of qb64 AIDs of witnesses to be used for the new group identifier.
                    estOnly:
                      type: boolean
                      default: false
                      description: True means to not allow interaction events to anchor credential events.
                  required:
                    - name
                    - alias
                    - toad
                    - nonce
                    - baks
        responses:
           202:
              description:  registry inception request has been submitted
              content:
                  application/json:
                    schema:
                      $ref: '#/components/schemas/RegistryOperation'
           404:
              description: The requested registry is not a valid reference to an identifier.
           400:
              description: Registry already in use.

        """
        agent = req.context.agent
        body = req.get_media()

        rname = httping.getRequiredParam(body, "name")
        ked = httping.getRequiredParam(body, "vcp")
        vcp = serdering.SerderKERI(sad=ked)

        ked = httping.getRequiredParam(body, "ixn")
        ixn = serdering.SerderKERI(sad=ked)

        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        if agent.rgy.registryByName(name=rname) is not None:
            raise falcon.HTTPBadRequest(
                description=f"registry name {rname} already in use"
            )

        registry = agent.rgy.makeSignifyRegistry(name=rname, prefix=hab.pre, regser=vcp)

        # The `/multisig/vcp` EXN uses the embed label `anc` for the anchoring
        # KEL event. In this endpoint that concrete event is the submitted `ixn`.
        protocol_embeds = dict(vcp=vcp.ked, anc=ixn.ked)
        replay_multisig_embeds(
            agent,
            hab,
            route="/multisig/vcp",
            embeds=protocol_embeds,
            labels=("anc",),
        )

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        anchor = dict(i=registry.regk, s="0", d=registry.regk)
        # Create registry long running OP that embeds the above received OP or Serder.

        seqner = coring.Seqner(sn=ixn.sn)
        prefixer = coring.Prefixer(qb64=ixn.pre)
        agent.registrar.incept(
            hab,
            registry,
            prefixer=prefixer,
            seqner=seqner,
            saider=coring.Saider(qb64=ixn.said),
        )
        op = agent.monitor.submit(
            registry.regk,
            longrunning.OpTypes.registry,
            metadata=dict(pre=hab.kever.prefixer.qb64, anchor=anchor, depends=op),
        )

        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class RegistrySyncCollectionEnd:
    """Collection endpoint for explicit multisig registry catch-up."""

    @staticmethod
    def on_post(req, rep, name):
        agent = req.context.agent
        body = req.get_media() or {}
        if not isinstance(body, dict):
            raise falcon.HTTPBadRequest(description="body must be a JSON object")

        hab = _resolve_group_identifier(agent, name)
        source = _select_regsync_source(agent, hab, source=body.get("source"))

        opname = _regsync_op_name(hab.pre)
        if (existing := agent.monitor.opr.ops.get(keys=(opname,))) is not None:
            if not agent.monitor.status(existing).done:
                raise falcon.HTTPConflict(
                    description=f"registry sync already pending for {hab.pre}"
                )

        exn, atc = _registry_sync_request_exn(
            hab=agent.agentHab,
            gid=hab.pre,
            mid=hab.mhab.pre,
        )
        agent.hby.psr.parseOne(
            ims=bytearray(exn.raw) + bytearray(atc),
            exc=agent.exc,
        )

        metadata = dict(
            pre=hab.pre,
            source=source,
            phase="catalog",
            phase_start=helping.nowIso8601(),
            request=exn.said,
            targets=[],
            error=None,
        )
        op = agent.monitor.submit(hab.pre, longrunning.OpTypes.regsync, metadata=metadata)
        agent.exchanges.append(
            dict(said=exn.said, pre=agent.agentHab.pre, rec=[source], topic="multisig")
        )

        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class CredentialSyncCollectionEnd:
    """Collection endpoint for explicit multisig credential-history catch-up."""

    @staticmethod
    def on_post(req, rep, name):
        agent = req.context.agent
        body = req.get_media() or {}
        if not isinstance(body, dict):
            raise falcon.HTTPBadRequest(description="body must be a JSON object")

        hab = _resolve_group_identifier(agent, name)
        saids = _validate_sync_saids(body)
        source = _select_regsync_source(agent, hab, source=body.get("source"))

        if not any(registry.hab.pre == hab.pre for registry in agent.rgy.regs.values()):
            raise falcon.HTTPConflict(
                description=f"credential sync for {hab.pre} requires registry sync first"
            )

        opname = _credsync_op_name(hab.pre)
        if (existing := agent.monitor.opr.ops.get(keys=(opname,))) is not None:
            if not agent.monitor.status(existing).done:
                raise falcon.HTTPConflict(
                    description=f"credential sync already pending for {hab.pre}"
                )

        exn, atc = _credential_sync_request_exn(
            hab=agent.agentHab,
            gid=hab.pre,
            saids=saids,
            mid=hab.mhab.pre,
        )
        agent.hby.psr.parseOne(
            ims=bytearray(exn.raw) + bytearray(atc),
            exc=agent.exc,
        )

        metadata = dict(
            pre=hab.pre,
            source=source,
            phase="replay",
            phase_start=helping.nowIso8601(),
            request=exn.said,
            saids=saids,
            synced=[],
            error=None,
        )
        op = agent.monitor.submit(hab.pre, longrunning.OpTypes.credsync, metadata=metadata)
        agent.exchanges.append(
            dict(said=exn.said, pre=agent.agentHab.pre, rec=[source], topic="multisig")
        )

        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class RegistrySyncRequestHandler:
    """Machine-handled multisig registry sync request."""

    resource = "/multisig/registry/sync"

    def __init__(self, agent):
        self.agent = agent

    def handle(self, serder, attachments=None):
        payload = serder.ked.get("a", {})
        gid = payload.get("gid")
        sender = serder.ked.get("i")
        requester = payload.get("mid")
        if gid is None or sender is None:
            logger.error("invalid registry sync request payload on %s", serder.said)
            return

        hab = self.agent.hby.habByPre(gid)
        if hab is None or not isinstance(hab, SignifyGroupHab):
            logger.info("ignoring registry sync request for unknown group %s", gid)
            return

        members = hab.db.signingMembers(pre=gid) or []
        if requester is not None:
            if requester not in members:
                logger.warning(
                    "ignoring registry sync request %s for non-member requester %s on %s",
                    serder.said,
                    requester,
                    gid,
                )
                return
            if not _agent_authorized_for_member(self.agent, requester, sender):
                logger.warning(
                    "ignoring registry sync request %s from unauthorized agent %s for %s",
                    serder.said,
                    sender,
                    requester,
                )
                return
            if requester == hab.mhab.pre and sender == self.agent.agentHab.pre:
                logger.info(
                    "ignoring locally originated registry sync request %s for %s",
                    serder.said,
                    gid,
                )
                return
        elif not any(_agent_authorized_for_member(self.agent, member, sender) for member in members):
            logger.warning(
                "ignoring registry sync request %s from non-member agent %s for %s",
                serder.said,
                sender,
                gid,
            )
            return

        registries = []
        messages = []
        local_regs = sorted(
            self.agent.rgy.regs.values(),
            key=lambda registry: (registry.name, registry.regk),
        )
        for registry in local_regs:
            if registry.hab.pre != gid or registry.regk not in self.agent.rgy.tevers:
                continue
            vcp = SerderKERI(raw=self.agent.rgy.reger.cloneTvtAt(pre=registry.regk, sn=0))
            vcp_message = None
            for msg in self.agent.rgy.reger.clonePreIter(pre=registry.regk, fn=0):
                vcp_message = bytes(msg)
                break

            if vcp_message is None:
                logger.warning(
                    "skipping registry %s during sync for %s because no VCP replay message was available",
                    registry.regk,
                    gid,
                )
                continue

            registries.append(
                dict(
                    name=registry.name,
                    regk=registry.regk,
                    vcp=vcp.ked,
                    anc=_registry_anchor(registry.regk, vcp.said, sn=vcp.snh),
                    sn=registry.tever.sn,
                )
            )
            messages.append(vcp_message)

        exn, atc = _registry_sync_response_exn(
            hab=self.agent.agentHab,
            gid=gid,
            registries=registries,
            dig=serder.said,
            messages=messages,
        )
        self.agent.hby.psr.parseOne(
            ims=bytearray(exn.raw) + bytearray(atc),
            exc=self.agent.exc,
        )
        self.agent.exchanges.append(
            dict(
                said=exn.said,
                pre=self.agent.agentHab.pre,
                rec=[requester if requester is not None else sender],
                topic="multisig",
            )
        )


class RegistrySyncResponseHandler:
    """Machine-handled multisig registry sync response."""

    resource = "/multisig/registry/sync/response"

    def __init__(self, agent):
        self.agent = agent

    def handle(self, serder, attachments=None):
        self.agent.regsyncResps.append(
            dict(serder=serder, attachments=attachments or [])
        )


class RegistrySyncApplyDoer(doing.Doer):
    """Apply sync responses by hydrating local registry records then replaying TEL."""

    def __init__(self, agent, responses, tock=0.0):
        self.agent = agent
        self.responses = responses
        self.tock = tock
        super(RegistrySyncApplyDoer, self).__init__(tock=tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        if not self.responses:
            return False

        msg = self.responses.popleft()
        serder = msg["serder"]
        attachments = msg.get("attachments") or []
        request_said = serder.ked.get("p")
        if not request_said:
            logger.warning("ignoring registry sync response %s without p", serder.said)
            return False

        opname, op = _find_regsync_by_request(self.agent, request_said)
        if op is None:
            logger.info(
                "ignoring stale registry sync response %s for request %s",
                serder.said,
                request_said,
            )
            return False

        metadata = dict(op.metadata)
        source = metadata["source"]
        gid = metadata["pre"]
        payload = serder.ked.get("a", {})
        sender = serder.ked.get("i")
        if sender is None or not _agent_authorized_for_member(self.agent, source, sender):
            _update_regsync_error(
                self.agent,
                opname,
                424,
                f"registry sync response source mismatch, expected agent for {source} got {sender}",
            )
            return False

        if payload.get("gid") != gid:
            _update_regsync_error(
                self.agent,
                opname,
                424,
                f"registry sync response group mismatch, expected {gid} got {payload.get('gid')}",
            )
            return False

        if metadata["phase"] != "catalog":
            logger.info(
                "ignoring registry sync response %s for completed phase %s",
                serder.said,
                metadata["phase"],
            )
            return False

        entries = payload.get("registries")
        if not isinstance(entries, list):
            _update_regsync_error(
                self.agent,
                opname,
                424,
                "registry sync response registries payload must be a list",
            )
            return False

        vcp_messages = _embedded_messages_from_attachments(serder, attachments, "vcpmsg")
        if vcp_messages and len(vcp_messages) != len(entries):
            _update_regsync_error(
                self.agent,
                opname,
                424,
                "registry sync response VCP message count does not match registry entries",
                details=dict(entries=len(entries), messages=len(vcp_messages)),
            )
            return False

        parsed = []
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                _update_regsync_error(
                    self.agent,
                    opname,
                    424,
                    "registry sync response contains a non-object registry entry",
                    details=dict(entry=entry),
                )
                return False

            try:
                name = entry["name"]
                regk = entry["regk"]
                vcp = SerderKERI(sad=entry["vcp"])
                anc = entry["anc"]
                sn = int(entry["sn"])
                coring.Prefixer(qb64=regk)
            except (KeyError, TypeError, ValueError, kering.ValidationError) as ex:
                _update_regsync_error(
                    self.agent,
                    opname,
                    424,
                    f"invalid registry sync response entry: {ex}",
                    details=dict(entry=entry),
                )
                return False

            existing_by_name = self.agent.rgy.registryByName(name)
            if existing_by_name is not None and existing_by_name.regk != regk:
                _update_regsync_error(
                    self.agent,
                    opname,
                    409,
                    f"registry name {name} already maps to {existing_by_name.regk}",
                    details=dict(name=name, regk=regk, existing=existing_by_name.regk),
                )
                return False

            if vcp.ked["t"] != "vcp" or vcp.pre != regk:
                _update_regsync_error(
                    self.agent,
                    opname,
                    424,
                    f"invalid registry inception event for {regk}",
                    details=dict(entry=entry),
                )
                return False

            if tuple(anc) != ("i", "s", "d"):
                _update_regsync_error(
                    self.agent,
                    opname,
                    424,
                    f"invalid registry sync anchor for {regk}",
                    details=dict(entry=entry),
                )
                return False

            parsed.append(
                (name, regk, vcp, anc, sn, vcp_messages[idx] if vcp_messages else None)
            )

        group_hab = self.agent.hby.habByPre(gid)
        if group_hab is None or not isinstance(group_hab, SignifyGroupHab):
            _update_regsync_error(
                self.agent,
                opname,
                424,
                f"registry sync target group {gid} is no longer available locally",
            )
            return False

        targets = []
        # Late joiners may know the current multisig state but still lack the
        # historical group event that anchored a preexisting registry VCP.
        # Replay the group's KEL first so subsequent TEL replay can unescrow
        # anchored registry events instead of stalling in ANC escrow.
        self.agent.witq.query(
            hab=self.agent.agentHab,
            pre=gid,
            wits=group_hab.kever.wits or None,
        )
        for name, regk, vcp, anc, sn, vcp_message in parsed:
            if vcp_message is not None:
                try:
                    self.agent.parser.parseOne(
                        ims=bytearray(vcp_message),
                        tvy=self.agent.rgy.tvy,
                        local=False,
                    )
                except Exception as ex:
                    _update_regsync_error(
                        self.agent,
                        opname,
                        424,
                        f"registry sync import failed for {regk}: {ex}",
                    )
                    return False

            if not longrunning.ensure_registry_anchor(
                hby=self.agent.hby,
                reger=self.agent.rgy.reger,
                gid=gid,
                regk=regk,
                regd=vcp.said,
                anchor=anc,
            ):
                self.agent.witq.query(
                    hab=self.agent.agentHab,
                    pre=gid,
                    anchor=anc,
                    wits=group_hab.kever.wits or None,
                )

            registry = self.agent.rgy.regs.get(regk)
            if registry is None:
                registry = _materialize_signify_registry(
                    self.agent,
                    name=name,
                    prefix=gid,
                    regk=regk,
                )

            if sn > 0:
                self.agent.witq.telquery(
                    hab=self.agent.agentHab,
                    pre=gid,
                    ri=regk,
                    wits=group_hab.kever.wits or None,
                )

            targets.append(
                dict(name=registry.name, regk=regk, regd=vcp.said, anc=anc, sn=sn)
            )

        metadata.update(
            phase="replay",
            phase_start=helping.nowIso8601(),
            targets=targets,
            error=None,
        )
        self.agent.monitor.update(opname, metadata=metadata)
        return False


class CredentialSyncRequestHandler:
    """Machine-handled multisig credential-history sync request."""

    resource = "/multisig/credential/sync"

    def __init__(self, agent):
        self.agent = agent

    def handle(self, serder, attachments=None):
        payload = serder.ked.get("a", {})
        gid = payload.get("gid")
        sender = serder.ked.get("i")
        requester = payload.get("mid")
        saids = payload.get("saids")
        if gid is None or sender is None or requester is None or not isinstance(saids, list):
            logger.error("invalid credential sync request payload on %s", serder.said)
            return

        hab = self.agent.hby.habByPre(gid)
        if hab is None or not isinstance(hab, SignifyGroupHab):
            logger.info("ignoring credential sync request for unknown group %s", gid)
            return

        members = hab.db.signingMembers(pre=gid) or []
        if requester not in members:
            logger.warning(
                "ignoring credential sync request %s for non-member requester %s on %s",
                serder.said,
                requester,
                gid,
            )
            return

        if not _agent_authorized_for_member(self.agent, requester, sender):
            logger.warning(
                "ignoring credential sync request %s from unauthorized agent %s for %s",
                serder.said,
                sender,
                requester,
            )
            return

        if requester == hab.mhab.pre and sender == self.agent.agentHab.pre:
            logger.info(
                "ignoring locally originated credential sync request %s for %s",
                serder.said,
                gid,
            )
            return

        for said in saids:
            error = None
            messages = None
            schemas = None
            try:
                creder, _, _, _ = self.agent.rgy.reger.cloneCred(said=said)
                regk = _current_credential_regk(creder)
                registry = self.agent.rgy.regs.get(regk) if regk is not None else None
                if registry is None or registry.hab.pre != gid:
                    error = dict(
                        code=424,
                        message=(
                            f"credential {said} is not issued from a registry controlled by {gid}"
                        ),
                    )
                else:
                    messages = _credential_sync_messages(
                        self.agent.hby, self.agent.rgy, said
                    )
                    schemas = _credential_sync_schemas(
                        self.agent.hby, self.agent.rgy, said
                    )
            except kering.MissingEntryError:
                error = dict(
                    code=424,
                    message=f"credential {said} is not available on source {gid}",
                )

            exn, atc = _credential_sync_response_exn(
                hab=self.agent.agentHab,
                gid=gid,
                said=said,
                messages=messages,
                schemas=schemas,
                error=error,
                dig=serder.said,
            )
            self.agent.hby.psr.parseOne(
                ims=bytearray(exn.raw) + bytearray(atc),
                exc=self.agent.exc,
            )
            self.agent.exchanges.append(
                dict(
                    said=exn.said,
                    pre=self.agent.agentHab.pre,
                    rec=[requester],
                    topic="multisig",
                )
            )


class CredentialSyncResponseHandler:
    """Machine-handled multisig credential-history sync response."""

    resource = "/multisig/credential/sync/response"

    def __init__(self, agent):
        self.agent = agent

    def handle(self, serder, attachments=None):
        self.agent.credsyncResps.append(
            dict(serder=serder, attachments=attachments or [])
        )


class CredentialSyncApplyDoer(doing.Doer):
    """Apply credential sync responses by parsing imported CESR bundles locally."""

    def __init__(self, agent, responses, tock=0.0):
        self.agent = agent
        self.responses = responses
        self.tock = tock
        super(CredentialSyncApplyDoer, self).__init__(tock=tock)

    def recur(self, tyme=None, tock=0.0, **opts):
        if not self.responses:
            return False

        msg = self.responses.popleft()
        serder = msg["serder"]
        attachments = msg.get("attachments") or []
        request_said = serder.ked.get("p")
        if not request_said:
            logger.warning("ignoring credential sync response %s without p", serder.said)
            return False

        opname, op = _find_credsync_by_request(self.agent, request_said)
        if op is None:
            logger.info(
                "ignoring stale credential sync response %s for request %s",
                serder.said,
                request_said,
            )
            return False

        metadata = dict(op.metadata)
        if metadata.get("error") is not None:
            logger.info(
                "ignoring credential sync response %s for errored op %s",
                serder.said,
                opname,
            )
            return False

        source = metadata["source"]
        gid = metadata["pre"]
        payload = serder.ked.get("a", {})
        sender = serder.ked.get("i")
        if sender is None or not _agent_authorized_for_member(self.agent, source, sender):
            logger.info(
                "ignoring credential sync response %s from unexpected sender %s for source %s",
                serder.said,
                sender,
                source,
            )
            return False

        if payload.get("gid") != gid:
            logger.info(
                "ignoring credential sync response %s with group mismatch %s for %s",
                serder.said,
                payload.get("gid"),
                gid,
            )
            return False

        said = payload.get("said")
        if said not in metadata["saids"]:
            logger.info(
                "ignoring credential sync response %s for unexpected credential %s",
                serder.said,
                said,
            )
            return False

        if isinstance(payload.get("error"), dict):
            err = payload["error"]
            _update_credsync_error(
                self.agent,
                opname,
                err.get("code", 424),
                err.get("message", f"credential sync failed for {said}"),
                details=err.get("details"),
            )
            return False

        if said in metadata["synced"]:
            logger.info(
                "ignoring duplicate credential sync response %s for %s",
                serder.said,
                said,
            )
            return False

        messages = _embedded_messages_from_attachments(serder, attachments, "credmsg")
        bundle = _embedded_stream_from_attachments(serder, attachments, "cred")

        if not messages and bundle is None:
            _update_credsync_error(
                self.agent,
                opname,
                424,
                f"credential sync response for {said} missing credential bundle",
            )
            return False

        group_hab = self.agent.hby.habByPre(gid)
        if group_hab is None or not isinstance(group_hab, SignifyGroupHab):
            _update_credsync_error(
                self.agent,
                opname,
                424,
                f"credential sync target group {gid} is no longer available locally",
            )
            return False

        try:
            _cache_embedded_schemas(self.agent, serder, attachments)

            if bundle is not None:
                self.agent.parser.parse(
                    ims=bytearray(bundle),
                    tvy=self.agent.rgy.tvy,
                    local=False,
                )

            for message in messages:
                _query_group_anchor_for_tel_message(
                    self.agent,
                    gid=gid,
                    group_hab=group_hab,
                    message=message,
                )
                self.agent.parser.parseOne(
                    ims=bytearray(message),
                    tvy=self.agent.rgy.tvy,
                    local=False,
                )

            # Late-join sync imports can otherwise rely on ambient doer timing to
            # drain TEL, verifier, registrar, and dissemination escrows. Process
            # once here so imported credential state becomes usable immediately
            # when the local KEL/TEL data is sufficient.
            longrunning.stabilize_credsync_state(
                registrar=self.agent.registrar,
                credentialer=self.agent.credentialer,
            )
        except Exception as ex:
            _update_credsync_error(
                self.agent,
                opname,
                424,
                f"credential sync import failed for {said}: {ex}",
            )
            return False

        metadata["synced"] = [*metadata["synced"], said]
        self.agent.monitor.update(opname, metadata=metadata)
        return False


class RegistryResourceEnd:
    @staticmethod
    def on_get(req, rep, name, registryName):
        """Registry Resource GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID
            registryName(str): human readable name for registry

        ---
        summary: Get a single credential issuance and revocation registy
        description: Get a single credential issuance and revocation registy
        operationId: getRegistry
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

        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        registry = agent.rgy.registryByName(registryName)
        if registry is None:
            raise falcon.HTTPNotFound(
                description=f"{registryName} is not a valid reference to a credential registry"
            )

        if not registry.hab.pre == hab.pre:
            raise falcon.HTTPNotFound(
                description=f"{registryName} is not a valid registry for AID {name}"
            )

        rd = dict(
            name=registry.name,
            regk=registry.regk,
            pre=registry.hab.pre,
            state=asdict(registry.tever.state()),
        )
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(rd).encode("utf-8")

    @staticmethod
    def on_put(req, rep, name, registryName):
        """Registry Resource PUT endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable name or prefix for AID
            registryName(str): human readable name for registry or its SAID

        ---
        summary: Get a single credential issuance and revocation registry
        description: Get a single credential issuance and revocation registry
        operationId: renameRegistry
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

        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        body = req.get_media()
        if "name" not in body:
            raise falcon.HTTPBadRequest(description="'name' is required in body")

        name = body["name"]
        if agent.rgy.registryByName(name) is not None:
            raise falcon.HTTPBadRequest(
                description=f"{name} is already in use for a registry"
            )

        registry = agent.rgy.registryByName(registryName)
        if registry is None:
            if (
                registryName in agent.rgy.regs
            ):  # Check to see if the registryName parameter is a SAID
                registry = agent.rgy.regs[registryName]
            else:
                regk = registryName
                key = dgKey(regk, regk)
                raw = agent.rgy.reger.getTvt(key=key)
                if raw is None:
                    raise falcon.HTTPNotFound(
                        description=f"{registryName} is not a valid reference to a credential registry"
                    )

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
            state=asdict(registry.tever.state()),
        )
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(rd).encode("utf-8")


class SchemaResourceEnd:
    @staticmethod
    def on_get(req, rep, said):
        """Schema GET endpoint

          Parameters:
              req: falcon.Request HTTP request
              rep: falcon.Response HTTP response
              said: qb64 self-addressing identifier of schema to load

        ---
         summary:  Get schema JSON of specified schema
         description:  Get schema JSON of specified schema
         operationId: getSchema
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
        """Schema GET plural endpoint

          Parameters:
              req: falcon.Request HTTP request
              rep: falcon.Response HTTP response

        ---
         summary:  Get schema JSON of all schema
         description:  Get schema JSON of all schema
         operationId: listSchemas
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
        """Verify credential endpoint (no IPEX)

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Verify a credential without IPEX
        description: Verify a credential without using IPEX (TEL should be updated separately)
        operationId: verifyCredential
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
                        $ref: '#/components/schemas/CredentialOperation'
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
        op = agent.monitor.submit(
            creder.said, longrunning.OpTypes.credential, metadata=dict(ced=creder.sad)
        )
        rep.status = falcon.HTTP_202
        rep.data = op.to_json().encode("utf-8")


class CredentialQueryCollectionEnd:
    """This class provides a collection endpoint for creating credential queries.

    I fully admit that the semantics here are a big stretch.  I would rather have this as a GET against the
    credential collection endpoint, but the nature of the complicated input to this endpoint dictate a BODY
    and certain client libraries (and possibly reverse proxies) don't support a BODY in a GET request.  So
    I'm moving the credential query code to this endpoint class and mapping to `.../credentials/queries` and
    making it a post against that path and calling it "creating a creaential query".  Meh.

    """

    @staticmethod
    def on_post(req, rep):
        """Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary:  List credentials in credential store (wallet)
        description: List issued or received credentials current verified
        operationId: listCredentials
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
        """Initiate a credential issuance

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            name (str): human readable alias or prefix for AID to use as issuer

        ---
        summary: Perform credential issuance
        description: Perform credential issuance
        operationId: issueCredential
        tags:
           - Credentials
        parameters:
          - in: path
            name: name
            description: human readable alias or prefix for AID to use as issuer
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
                            $ref: '#/components/schemas/CredentialOperation'
            400:
                description: Bad request. This could be due to missing or invalid data.

        """
        agent = req.context.agent

        body = req.get_media()
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )
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

        regk = (
            iserder.ked["ri"]
            if "ri" in iserder.ked
            else iserder.ked["ii"]
            if "ii" in iserder.ked
            else None
        )
        if regk is None:
            raise falcon.HTTPBadRequest(
                description="credential issuance request missing registry (ri) or (ii) field"
            )
        if regk not in agent.rgy.tevers:
            raise falcon.HTTPNotFound(
                description=f"issue against invalid registry SAID {regk}"
            )

        replay_multisig_embeds(
            agent,
            hab,
            route="/multisig/iss",
            embeds=dict(acdc=creder.sad, iss=iserder.ked, anc=anc.ked),
            labels=("anc", "acdc"),
        )

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        try:
            agent.credentialer.validate(creder)
            agent.registrar.issue(regk, iserder, anc)
            agent.credentialer.issue(creder=creder, serder=iserder)
            op = agent.monitor.submit(
                creder.said,
                longrunning.OpTypes.credential,
                metadata=dict(ced=creder.sad, depends=op),
            )

        except kering.ConfigurationError as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
            return

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")


class CredentialResourceEnd:
    def __init__(self):
        """ """

    @staticmethod
    def on_get(req, rep, said):
        """Credentials GET endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said (str): SAID of credential to export

        ---
        summary:  Export credential and all supporting cryptographic material
        description: Export credential and all supporting cryptographic material
        operationId: getCredential
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
           404:
             description: The requested credential was not found.
        """
        agent = req.context.agent
        accept = req.get_header("accept")

        if agent.rgy.reger.saved.get(keys=(said,)) is None:
            raise falcon.HTTPNotFound(
                description=f"credential for said {said} not found."
            )

        if accept == "application/json+cesr":
            rep.content_type = "application/json+cesr"
            data = CredentialResourceEnd.outputCred(agent.hby, agent.rgy, said)
        else:
            rep.content_type = "application/json"
            creds = agent.rgy.reger.cloneCreds(
                [coring.Saider(qb64=said)], db=agent.hby.db
            )
            data = json.dumps(creds[0]).encode("utf-8")

        rep.status = falcon.HTTP_200
        rep.data = bytes(data)

    @staticmethod
    def outputCred(hby, rgy, said):
        out = bytearray()
        creder, prefixer, seqner, saider = rgy.reger.cloneCred(said=said)
        for chain_said in _credential_chain_saids(creder):
            out.extend(CredentialResourceEnd.outputCred(hby, rgy, chain_said))

        issr = creder.issuer
        for msg in hby.db.clonePreIter(pre=issr):
            serder = serdering.SerderKERI(raw=msg)
            atc = msg[serder.size :]
            out.extend(serder.raw)
            out.extend(atc)

        if "i" in creder.attrib:
            subj = creder.attrib["i"]
            for msg in hby.db.clonePreIter(pre=subj):
                serder = serdering.SerderKERI(raw=msg)
                atc = msg[serder.size :]
                out.extend(serder.raw)
                out.extend(atc)

        if creder.regi is not None:
            for msg in rgy.reger.clonePreIter(pre=creder.regi):
                serder = serdering.SerderKERI(raw=msg)
                atc = msg[serder.size :]
                out.extend(serder.raw)
                out.extend(atc)

            for msg in rgy.reger.clonePreIter(pre=creder.said):
                serder = serdering.SerderKERI(raw=msg)
                atc = msg[serder.size :]
                out.extend(serder.raw)
                out.extend(atc)

        out.extend(signing.serialize(creder, prefixer, seqner, saider))

        return out

    @staticmethod
    def on_delete(req, rep, said):
        """Credentials DELETE endpoint

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response
            said (str): SAID of credential to delete

        ---
        summary: Delete a credential from the database
        description: Delete a credential from the database and remove any associated indices
        operationId: deleteCredential
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
            raise falcon.HTTPNotFound(
                description=f"credential for said {said} not found."
            )

        agent.seeker.unindex(said)

        saider = coring.Saider(qb64b=said)
        if not isinstance(creder.attrib, str) and "i" in creder.attrib:
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
        """Initiate a credential revocation

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
        operationId: revokeCredential
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
                      oneOf:
                        - $ref: '#/components/schemas/GroupOperation'
                        - $ref: '#/components/schemas/DelegationOperation'
                        - $ref: '#/components/schemas/WitnessOperation'
                        - $ref: '#/components/schemas/DoneOperation'
            400:
                description: Bad request. This could be due to invalid revocation event or other invalid parameters.
            404:
                description: The requested identifier or credential was not found.
        """

        agent = req.context.agent

        body = req.get_media()
        hab = (
            agent.hby.habs[name]
            if name in agent.hby.habs
            else agent.hby.habByName(name)
        )
        if hab is None:
            raise falcon.HTTPNotFound(
                description=f"{name} is not a valid reference to an identifier"
            )

        rserder = serdering.SerderKERI(sad=httping.getRequiredParam(body, "rev"))

        regk = rserder.ked["ri"]
        if regk not in agent.rgy.tevers:
            raise falcon.HTTPNotFound(
                description=f"revocation against invalid registry SAID {regk}"
            )

        try:
            agent.rgy.reger.cloneCreds([coring.Saider(qb64=said)], db=agent.hby.db)
        except Exception as ex:
            raise falcon.HTTPConflict(
                description=(
                    f"credential history for said {said} is not available locally; "
                    f"run credentials().sync({name!r}, saids=[{said!r}]) first"
                )
            ) from ex

        if agent.rgy.tevers[regk].vcSn(said) is None:
            raise falcon.HTTPConflict(
                description=(
                    f"credential history for said {said} is incomplete locally; "
                    f"run credentials().sync({name!r}, saids=[{said!r}]) first"
                )
            )

        if hab.kever.estOnly:
            anc = serdering.SerderKERI(sad=httping.getRequiredParam(body, "rot"))
        else:
            anc = serdering.SerderKERI(sad=httping.getRequiredParam(body, "ixn"))

        replay_multisig_embeds(
            agent,
            hab,
            route="/multisig/rev",
            embeds=dict(rev=rserder.ked, anc=anc.ked),
            labels=("anc",),
        )

        if hab.kever.estOnly:
            op = self.identifierResource.rotate(agent, name, body)
        else:
            op = self.identifierResource.interact(agent, name, body)

        try:
            agent.registrar.revoke(regk, rserder, anc.ked)
        except Exception:
            raise falcon.HTTPBadRequest(description="invalid revocation event.")

        rep.status = falcon.HTTP_200
        rep.data = op.to_json().encode("utf-8")


class CredentialRegistryResourceEnd:
    @staticmethod
    def on_get(req, rep, ri, vci):
        """Get credential registry state

        Parameters:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Get credential registry state
        description: Get credential registry state from any known Tever (does not need be controlled by us)
        operationId: getCredentialState
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
            raise falcon.HTTPNotFound(
                description=f"credential {vci} not found in registry {ri}"
            )

        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(asdict(state)).encode("utf-8")


def signPaths(hab, pather, sigers):
    """Sign the SAD or SAIDs with the keys from the Habitat.

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
    """
    Manages credential registry creation (inception), credential issuance, and credential revocation.
    Handles witness, multisig, and dissemination escrows for registry and credential operations.
    """

    def __init__(self, agentHab, hby, rgy, counselor, witDoer, witPub, verifier):
        """
        Parameters:
            hby (habbing.Habery): Habery in which the Agent lives
            agentHab (habbing.Habitat): Agent
            rgy (Regery): registry for the agent
            counselor (Counselor): counselor for the agent
            witDoer (WitnessReceiptor): retrieves receipts registry and credential events from witnesses
            witPub (WitnessPublisher): publishes registry and credential events to witnesses
            verifier (Verifier): Verifies TEL events
        """
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
            registry.anchorMsg(
                pre=registry.regk, regd=registry.regd, seqner=seqner, saider=saider
            )
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))
            self.rgy.reger.tpwe.add(
                keys=(registry.regk, rseq.qb64),
                val=(hab.kever.prefixer, seqner, saider),
            )

        else:
            # assume SignifyGroupHab - multisig incept, so start the counselor to wait on multisig incept completion
            self.counselor.start(
                ghab=hab, prefixer=prefixer, seqner=seqner, saider=saider
            )
            logger.info(
                "[%s | %s]: Waiting for TEL registry vcp event mulisig anchoring event",
                hab.name,
                hab.pre,
            )
            self.rgy.reger.tmse.add(
                keys=(registry.regk, rseq.qb64, registry.regd),
                val=(prefixer, seqner, saider),
            )

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
            registry.anchorMsg(
                pre=vcid, regd=iserder.said, seqner=seqner, saider=saider
            )

            logger.info(
                "[%s | %s]: Waiting for TEL event witness receipts", hab.name, hab.pre
            )
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))
            self.rgy.reger.tpwe.add(
                keys=(vcid, rseq.qb64), val=(hab.kever.prefixer, seqner, saider)
            )
            return vcid, rseq.sn

        else:  # multisig group hab
            sn = anc.sn
            said = anc.said

            prefixer = coring.Prefixer(qb64=hab.pre)
            seqner = coring.Seqner(sn=sn)
            saider = coring.Saider(qb64=said)

            self.counselor.start(
                prefixer=prefixer, seqner=seqner, saider=saider, ghab=hab
            )
            logger.info(
                "[%s | %s]: Waiting for TEL iss event mulisig anchoring event %s",
                hab.name,
                hab.pre,
                seqner.sn,
            )
            self.rgy.reger.tmse.add(
                keys=(vcid, rseq.qb64, iserder.said), val=(prefixer, seqner, saider)
            )
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
            registry.anchorMsg(
                pre=vcid, regd=rserder.said, seqner=seqner, saider=saider
            )

            logger.info(
                "[%s | %s]: Waiting for TEL event witness receipts", hab.name, hab.pre
            )
            self.witDoer.msgs.append(dict(pre=hab.pre, sn=seqner.sn))

            self.rgy.reger.tpwe.add(
                keys=(vcid, rseq.qb64), val=(hab.kever.prefixer, seqner, saider)
            )
            return vcid, rseq.sn
        else:
            serder = serdering.SerderKERI(sad=anc)
            sn = serder.sn
            said = serder.said

            prefixer = coring.Prefixer(qb64=hab.pre)
            seqner = coring.Seqner(sn=sn)
            saider = coring.Saider(qb64=said)

            self.counselor.start(
                prefixer=prefixer, seqner=seqner, saider=saider, ghab=hab
            )

            logger.info(
                "[%s | %s]: Waiting for TEL rev event mulisig anchoring event %s",
                hab.name,
                hab.pre,
                seqner.sn,
            )
            self.rgy.reger.tmse.add(
                keys=(vcid, rseq.qb64, rserder.said), val=(prefixer, seqner, saider)
            )
            return vcid, rseq.sn

    def complete(self, pre, sn=0):
        """Determine if registry event (inception, issuance, revocation, etc.) is finished validation

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
        for (regk, snq), (
            prefixer,
            seqner,
            saider,
        ) in self.rgy.reger.tpwe.getItemIter():  # partial witness escrow
            kever = self.hby.kevers[prefixer.qb64]
            dgkey = dbing.dgKey(prefixer.qb64b, saider.qb64)

            # Load all the witness receipts we have so far
            wigs = self.hby.db.getWigs(dgkey)
            if kever.wits:
                if len(wigs) == len(
                    kever.wits
                ):  # We have all of them, this event is finished
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

            self.rgy.reger.tede.add(
                keys=(regk, rseq.qb64), val=(prefixer, seqner, saider)
            )

    def processMultisigEscrow(self):
        """
        Process escrow of group multisig events that do not have a full compliment of receipts
        from witnesses yet.  When receipting is complete, remove from escrow and cue up a message
        that the event is complete.

        """
        for (regk, snq, regd), (
            prefixer,
            seqner,
            saider,
        ) in self.rgy.reger.tmse.getItemIter():  # multisig escrow
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
            self.rgy.reger.tede.add(
                keys=(regk, rseq.qb64), val=(prefixer, seqner, saider)
            )

    def processDiseminationEscrow(self):
        for (regk, snq), (
            prefixer,
            seqner,
            saider,
        ) in self.rgy.reger.tede.getItemIter():  # group multisig escrow
            rseq = coring.Seqner(qb64=snq)
            dig = self.rgy.reger.getTel(key=dbing.snKey(pre=regk, sn=rseq.sn))
            if dig is None:
                continue

            self.rgy.reger.tede.rem(keys=(regk, snq))

            tevt = bytearray()
            for msg in self.rgy.reger.clonePreIter(pre=regk, fn=rseq.sn):
                tevt.extend(msg)

            logger.info("Sending TEL events to witnesses")
            # Fire and forget the TEL event to the witnesses.  Consumers will have to query
            # to determine when the Witnesses have received the TEL events.
            self.witPub.msgs.append(dict(pre=prefixer.qb64, msg=tevt))
            self.rgy.reger.ctel.put(keys=(regk, rseq.qb64), val=saider)  # idempotent


class Credentialer:
    """
    Places credentials into the credential missing signature escrow, handles the credential signature
    escrow, and has utility functions to validate a credential against its schema and to know
    if a credential's anchoring event is completely signed.
    """

    def __init__(self, agentHab, hby, rgy, registrar, verifier, notifier):
        """
        Initialize the Credentialer

        Parameters:
            agentHab (Hab): Hab of the agent performing credential operations
            hby (Habery): Habery in which the Agent lives
            rgy (Regery): Container for local registries and their associated Tevers
            registrar (Registrar): Creation and escrowing for registries and credential issuance/revocation
            verifier (Verifier): Verifies and escrows TEL events.
            notifier (Notifier): Handles notifying controllers of significant events
        """
        self.agentHab = agentHab
        self.hby = hby
        self.rgy = rgy
        self.registrar = registrar
        self.verifier = verifier
        self.notifier = notifier

    def validate(self, creder):
        """
        Validates a credential against its schema.

        Args:
            creder (Creder): creder object representing the credential to validate

        Returns:
            bool: True if credential is valid against a known schema
        Raises:
            kering.ConfigurationError: if the credential schema is not found or validation fails
        """
        schema = creder.sad["s"]
        scraw = self.verifier.resolver.resolve(schema)
        if not scraw:
            raise kering.ConfigurationError(
                "Credential schema {} not found.  It must be loaded with data oobi before "
                "issuing credentials".format(schema)
            )

        schemer = scheming.Schemer(raw=scraw)
        try:
            schemer.verify(creder.raw)
        except kering.ValidationError as ex:
            raise kering.ConfigurationError(
                f"Credential schema validation failed for {schema}: {ex}"
            )

        return True

    def issue(self, creder, serder):
        """Issue the credential creder and handle witness propagation and communication

        Parameters:
            creder (Creder): Credential object to issue
            serder (Serder): KEL or TEL anchoring event

        """
        prefixer = coring.Prefixer(qb64=serder.pre)
        seqner = coring.Seqner(sn=serder.sn)

        self.rgy.reger.cmse.put(keys=(creder.said, seqner.qb64), val=creder)

        try:
            self.verifier.processCredential(
                creder=creder,
                prefixer=prefixer,
                seqner=seqner,
                saider=coring.Saider(qb64=serder.said),
            )
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
