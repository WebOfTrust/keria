# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.oobier module

"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from functools import partial
from typing import List
from urllib.parse import urljoin

from keri import kering
from keri.app import habbing
from keri.core.signing import Salter
from keri.db.basing import OobiRecord
from keri.help import helping
from marshmallow import fields

from ..core import longrunning
from ..utils.openapi import namedtupleToEnum


Role = namedtupleToEnum(kering.Roles, "Role")


@dataclass
class OOBI:
    """OOBI URLs generated for an endpoint role."""

    role: Role  # type: ignore
    oobis: List[str] = field(
        default_factory=list,
        metadata={"marshmallow_field": fields.List(fields.String(), required=True)},
    )


def endpointUrl(hab, eid):
    """Select one location URL for an endpoint, preferring HTTP over HTTPS.

    Parameters:
        hab (Hab): Habitat whose location records are queried.
        eid (str): Endpoint identifier whose location is requested.

    Returns:
        str | None: The HTTP URL, the HTTPS fallback, or None when neither exists.
    """
    for scheme in (kering.Schemes.http, kering.Schemes.https):
        urls = hab.fetchUrls(eid=eid, scheme=scheme)
        if scheme in urls:
            return urls[scheme]

    return None


def _endpointIds(endpointGroup):
    """Expose the distinct endpoint IDs contained in one endpoint-role group.

    Parameters:
        endpointGroup (Mict): Mapping from endpoint IDs to nested scheme maps.

    Returns:
        dict[str, None]: Ordered endpoint IDs, such as
            ``{"EID1": None, "EID2": None}``.
    """
    return dict.fromkeys(endpointGroup.keys())


def _endpointSchemeUrls(endpointGroup, eid, scheme):
    """Flatten one ``endpointGroup[eid][scheme]`` branch into URL strings.

    Parameters:
        endpointGroup (Mict): Mapping from endpoint IDs to nested scheme maps.
        eid (str): Endpoint identifier selecting one branch of the group.
        scheme (str): Location scheme to select, such as ``http`` or ``https``.

    Yields:
        str: Each matching URL, such as ``"http://agent.example"``.
    """
    for schemeUrls in endpointGroup.getall(eid):
        yield from schemeUrls.getall(scheme)


def _endpointGroupUrls(endpointGroup, scheme):
    """Attach endpoint IDs to every URL flattened from one role group.

    Parameters:
        endpointGroup (Mict): Mapping from endpoint IDs to nested scheme maps.
        scheme (str): Location scheme to select from every endpoint branch.

    Yields:
        tuple[str, str]: An ``(eid, url)`` pair, such as
            ``("EID1", "http://agent.example")``.
    """
    for eid in _endpointIds(endpointGroup):
        for url in _endpointSchemeUrls(endpointGroup, eid, scheme):
            yield eid, url


def _schemeRoleEndpointUrls(hab, role, scheme):
    """Flatten all endpoint groups authorized for one role and scheme.

    Parameters:
        hab (Hab): Habitat whose authorized endpoint roles are queried.
        role (str): Authorized endpoint role, such as ``agent`` or ``mailbox``.
        scheme (str): Location scheme to select, such as ``http`` or ``https``.

    Yields:
        tuple[str, str]: Each authorized ``(eid, url)`` pair for the scheme.
    """
    roleUrls = hab.fetchRoleUrls(cid=hab.pre, role=role, scheme=scheme)
    if role not in roleUrls:
        return

    for endpointGroup in roleUrls.getall(role):
        yield from _endpointGroupUrls(endpointGroup, scheme)


def roleEndpointUrls(hab, role):
    """Materialize authorized role endpoints with HTTP pairs before HTTPS pairs.

    Parameters:
        hab (Hab): Habitat whose authorized endpoint roles are queried.
        role (str): Authorized endpoint role, such as ``agent`` or ``mailbox``.

    Returns:
        list[tuple[str, str]]: Flattened ``(eid, url)`` pairs, for example
            ``[("EID1", "http://one"), ("EID1", "https://two")]``.
    """
    urls = []
    for scheme in (kering.Schemes.http, kering.Schemes.https):
        urls.extend(_schemeRoleEndpointUrls(hab, role, scheme))

    return urls


def oobiUrl(base_url, aid, role, eid=None):
    """Build an OOBI URL for an identifier, role, and optional endpoint ID."""
    path = f"/oobi/{aid}/{role}"
    if eid is not None:
        path = f"{path}/{eid}"

    return urljoin(base_url, path)


def agentOobiUrl(hab, base_url, eid, include_eid=False):
    """Build an agent OOBI using the single-signature or group URL policy."""
    endpoint_id = eid
    if isinstance(hab, habbing.SignifyGroupHab) and not include_eid:
        endpoint_id = None

    return oobiUrl(base_url, hab.pre, kering.Roles.agent, endpoint_id)


def uniqueOobis(oobis: Iterable[str]):
    """Return OOBIs without duplicates while preserving first-seen order."""
    return list(dict.fromkeys(oobis))


class Oobier:
    """Generate managed-identifier OOBIs and submit OOBI resolution requests."""

    def __init__(self, hby, monitor):
        """Initialize OOBI services for one KERIA Agent.

        Parameters:
            hby (Habery): The Agent Habery containing its managed identifiers and
                OOBI resolution escrows.
            monitor (Monitor): The Agent operation monitor used to track
                asynchronous OOBI resolution.
        """
        self.hby = hby
        self.monitor = monitor

    def get(self, name: str, role: str, include_eid: bool = False) -> OOBI:
        """Generate OOBIs for one managed identifier and endpoint role.

        Parameters:
            name (str): Managed identifier alias or AID prefix.
            role (str): OOBI role to generate: witness, controller, agent, or
                mailbox.
            include_eid (bool): Include endpoint IDs in multisig agent OOBIs when
                True.

        Returns:
            OOBI: The requested role and its generated OOBI URLs.

        Raises:
            MissingEntryError: The identifier or a required endpoint is missing.
            ValidationError: The name or role is invalid.
        """
        hab = self._findHab(name)
        generators = {
            kering.Roles.witness: self._witnessOobis,
            kering.Roles.controller: self._controllerOobis,
            kering.Roles.agent: partial(self._agentOobis, include_eid=include_eid),
            kering.Roles.mailbox: self._mailboxOobis,
        }

        if role not in generators:
            raise kering.ValidationError(f"unsupport role type {role} for oobi request")

        return OOBI(role=role, oobis=generators[role](hab))

    def resolve(self, body: Mapping[str, object]) -> longrunning.Operation:
        """Queue an OOBI URL and create an operation that tracks its resolution.

        Parameters:
            body (Mapping[str, object]): Resolution request containing a required
                ``url`` and optional ``oobialias``; ``rpy`` is reserved for future
                support.

        Returns:
            Operation: The pending or completed OOBI resolution operation.

        Raises:
            ValidationError: The body contains neither ``url`` nor ``rpy``.
            NotImplementedError: The body requests unsupported ``rpy`` resolution.
        """
        if not isinstance(body, Mapping):
            raise kering.ValidationError(
                "invalid OOBI request body, either 'rpy' or 'url' is required"
            )

        if "url" in body:
            url = body["url"]
            self._queueResolution(url=url, alias=body.get("oobialias"))
            return self._submitOp(url)

        if "rpy" in body:
            raise NotImplementedError("'rpy' support not implemented yet")

        raise kering.ValidationError(
            "invalid OOBI request body, either 'rpy' or 'url' is required"
        )

    def _findHab(self, name):
        """Find a managed identifier habitat by prefix or alias.

        Parameters:
            name (str): Managed identifier alias or AID prefix.

        Returns:
            Hab: The matching habitat from the Agent Habery.

        Raises:
            ValidationError: The name is empty.
            MissingEntryError: No managed identifier matches the name.
        """
        if not name:
            raise kering.ValidationError("name is required")

        hab = self.hby.habs[name] if name in self.hby.habs else self.hby.habByName(name)
        if hab is None:
            raise kering.MissingEntryError(f"invalid alias or prefix {name}")

        return hab

    @staticmethod
    def _witnessOobis(hab):
        """Generate endpoint-qualified OOBIs for every current witness.

        Parameters:
            hab (Hab): Managed identifier habitat whose witnesses are queried.

        Returns:
            list[str]: Witness OOBI URLs in witness-list order.

        Raises:
            MissingEntryError: A configured witness has no HTTP or HTTPS location.
        """
        oobis = []
        for witness in hab.kever.wits:
            url = endpointUrl(hab, witness)
            if url is None:
                raise kering.MissingEntryError(
                    f"unable to query witness {witness}, no http endpoint"
                )

            oobis.append(oobiUrl(url, hab.pre, kering.Roles.witness, witness))

        return oobis

    @staticmethod
    def _controllerOobis(hab):
        """Generate the controller OOBI for a managed identifier.

        Parameters:
            hab (Hab): Managed identifier habitat whose controller URL is queried.

        Returns:
            list[str]: A single controller OOBI URL.

        Raises:
            MissingEntryError: The controller has no HTTP or HTTPS location.
        """
        url = endpointUrl(hab, hab.pre)
        if url is None:
            raise kering.MissingEntryError(
                f"unable to query controller {hab.pre}, no http endpoint"
            )

        return [oobiUrl(url, hab.pre, kering.Roles.controller)]

    @staticmethod
    def _agentOobis(hab, include_eid=False):
        """Generate agent OOBIs using the single-signature or multisig URL policy.

        Parameters:
            hab (Hab): Managed identifier habitat whose agent endpoints are queried.
            include_eid (bool): Include endpoint IDs in multisig agent OOBIs when
                True.

        Returns:
            list[str]: Deduplicated agent OOBI URLs in endpoint discovery order.
        """
        oobis = (
            agentOobiUrl(hab, url, eid, include_eid=include_eid)
            for eid, url in roleEndpointUrls(hab, kering.Roles.agent)
        )
        return uniqueOobis(oobis)

    @staticmethod
    def _mailboxOobis(hab):
        """Generate endpoint-qualified mailbox OOBIs for authorized endpoints.

        Parameters:
            hab (Hab): Managed identifier habitat whose mailbox endpoints are
                queried.

        Returns:
            list[str]: Mailbox OOBI URLs in endpoint discovery order.
        """
        return [
            oobiUrl(url, hab.pre, kering.Roles.mailbox, eid)
            for eid, url in roleEndpointUrls(hab, kering.Roles.mailbox)
        ]

    def _queueResolution(self, url, alias):
        """Persist an OOBI URL request for asynchronous KERIpy resolution.

        Parameters:
            url (str): OOBI URL to place in the Agent Habery's resolution escrow.
            alias (str | None): Optional contact alias to assign after resolution.

        Returns:
            None.
        """
        record = OobiRecord(date=helping.nowIso8601(), oobialias=alias)
        self.hby.db.oobis.pin(keys=(url,), val=record)

    def _submitOp(self, url):
        """Create a monitor operation for an already-queued OOBI URL.

        Parameters:
            url (str): Queued OOBI URL tracked by the operation.

        Returns:
            Operation: The pending or completed OOBI resolution operation.
        """
        oid = Salter().qb64
        return self.monitor.submit(
            oid, longrunning.OpTypes.oobi, metadata=dict(oobi=url)
        )
