# -*- encoding: utf-8 -*-
"""Tests for managed-identifier OOBI generation and resolution submission."""

from types import SimpleNamespace
from unittest import mock

import pytest
from hio.help import hicting
from keri import core, kering
from keri.app import habbing
from keri.db import basing

from keria.app import aiding, oobier
from keria.core import longrunning


HTTP_ENDPOINT_URL = "http://preferred"
HTTPS_ENDPOINT_URL = "https://available"


@pytest.fixture
def endpointUrlResponses():
    """Provide successive ``Hab.fetchUrls`` results for memorable endpoint cases.

    Each result is KERIpy's ``Mict[scheme, url]`` shape. Its prefix lookup means
    an HTTPS-only record may appear during both the HTTP and HTTPS lookup steps.
    """
    bothSchemes = hicting.Mict(
        [
            (kering.Schemes.http, HTTP_ENDPOINT_URL),
            (kering.Schemes.https, HTTPS_ENDPOINT_URL),
        ]
    )
    httpsFromHttpPrefix = hicting.Mict([(kering.Schemes.https, HTTPS_ENDPOINT_URL)])
    httpsFromHttpsLookup = hicting.Mict([(kering.Schemes.https, HTTPS_ENDPOINT_URL)])

    return {
        "httpPreferred": [bothSchemes],
        "httpsFallback": [httpsFromHttpPrefix, httpsFromHttpsLookup],
        "noLocation": [hicting.Mict(), hicting.Mict()],
    }


def _add_identifier_route(app):
    app.add_route("/identifiers", aiding.IdentifierCollectionEnd())


def _authorize_endpoint(agent, cid, role, eid, url, scheme=kering.Schemes.http):
    agent.hby.db.ends.pin(
        keys=(cid, role, eid), val=basing.EndpointRecord(allowed=True)
    )
    agent.hby.db.locs.pin(keys=(eid, scheme), val=basing.LocationRecord(url=url))


def _role_urls(role, eid, scheme, *urls):
    locations = hicting.Mict((scheme, url) for url in urls)
    endpoints = hicting.Mict([(eid, locations)])
    return hicting.Mict([(role, endpoints)])


@pytest.mark.parametrize(
    "eid, expected",
    [
        (None, "https://example.com/oobi/EAID/controller"),
        ("EEND", "https://example.com/oobi/EAID/agent/EEND"),
    ],
)
def test_oobi_url(eid, expected):
    assert (
        oobier.oobiUrl(
            "https://example.com/base",
            "EAID",
            "controller" if eid is None else "agent",
            eid,
        )
        == expected
    )


def test_agent_oobi_url_and_unique_oobis():
    hab = SimpleNamespace(pre="EAID")
    assert (
        oobier.agentOobiUrl(hab, "http://example.com", "EEND")
        == "http://example.com/oobi/EAID/agent/EEND"
    )
    assert oobier.uniqueOobis(["one", "two", "one"]) == ["one", "two"]


@pytest.mark.parametrize(
    "case, expected",
    [
        ("httpPreferred", HTTP_ENDPOINT_URL),
        ("httpsFallback", HTTPS_ENDPOINT_URL),
        ("noLocation", None),
    ],
)
def test_endpoint_url_prefers_http_and_falls_back_to_https(
    case, expected, endpointUrlResponses
):
    hab = mock.Mock()
    hab.fetchUrls.side_effect = endpointUrlResponses[case]

    assert oobier.endpointUrl(hab, "EEND") == expected


def test_role_endpoint_urls_includes_http_and_https():
    hab = mock.Mock(pre="EAID")
    hab.fetchRoleUrls.side_effect = [
        _role_urls("agent", "EEND", "http", "http://one", "http://two"),
        _role_urls("agent", "EEND", "https", "https://three"),
    ]

    assert oobier.roleEndpointUrls(hab, "agent") == [
        ("EEND", "http://one"),
        ("EEND", "http://two"),
        ("EEND", "https://three"),
    ]
    assert hab.fetchRoleUrls.call_args_list == [
        mock.call(cid="EAID", role="agent", scheme="http"),
        mock.call(cid="EAID", role="agent", scheme="https"),
    ]


def test_oobier_generates_single_signature_roles(helpers):
    with helpers.openKeria() as (_, agent, app, client):
        _add_identifier_route(app)
        salt = b"0123456789abcdef"
        created = helpers.createAid(client, "pal", salt)
        aid = created["response"]["i"]
        hab = agent.hby.habs[aid]

        assert agent.oobier.get("pal", "agent").oobis == []
        assert agent.oobier.get(aid, "agent").oobis == []
        assert agent.oobier.get("pal", "witness").oobis == []

        with pytest.raises(kering.MissingEntryError):
            agent.oobier.get("pal", "controller")

        _authorize_endpoint(
            agent,
            cid=aid,
            role=kering.Roles.agent,
            eid=agent.agentHab.pre,
            url="http://agent.example",
        )
        _authorize_endpoint(
            agent,
            cid=aid,
            role=kering.Roles.mailbox,
            eid=agent.agentHab.pre,
            url="http://agent.example",
        )
        agent.hby.db.locs.pin(
            keys=(agent.agentHab.pre, kering.Schemes.https),
            val=basing.LocationRecord(url="https://agent.example"),
        )
        agent.hby.db.locs.pin(
            keys=(hab.pre, kering.Schemes.http),
            val=basing.LocationRecord(url="http://controller.example"),
        )

        agent_oobis = [
            f"http://agent.example/oobi/{aid}/agent/{agent.agentHab.pre}",
            f"https://agent.example/oobi/{aid}/agent/{agent.agentHab.pre}",
        ]
        mailbox_oobis = [
            f"http://agent.example/oobi/{aid}/mailbox/{agent.agentHab.pre}",
            f"https://agent.example/oobi/{aid}/mailbox/{agent.agentHab.pre}",
        ]
        assert agent.oobier.get("pal", "agent").oobis == agent_oobis
        assert agent.oobier.get("pal", "agent", include_eid=True).oobis == agent_oobis
        assert agent.oobier.get("pal", "mailbox").oobis == mailbox_oobis
        assert agent.oobier.get("pal", "controller").oobis == [
            f"http://controller.example/oobi/{aid}/controller"
        ]

        with pytest.raises(kering.MissingEntryError):
            agent.oobier.get("missing", "agent")
        with pytest.raises(kering.ValidationError):
            agent.oobier.get("pal", "banana")


def test_oobier_reports_missing_witness_endpoint(helpers):
    with helpers.openKeria() as (_, agent, app, client):
        _add_identifier_route(app)
        witness = "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha"
        agent.hby.db.locs.pin(
            keys=(witness, kering.Schemes.http),
            val=basing.LocationRecord(url="http://witness.example"),
        )
        helpers.createAid(client, "pal", b"0123456789abcdef", wits=[witness], toad="1")
        aid = agent.hby.habByName("pal").pre
        agent.hby.db.locs.rem(keys=(witness, kering.Schemes.http))

        with pytest.raises(kering.MissingEntryError):
            agent.oobier.get("pal", "witness")

        agent.hby.db.locs.pin(
            keys=(witness, kering.Schemes.https),
            val=basing.LocationRecord(url="https://witness.example"),
        )
        assert agent.oobier.get("pal", "witness").oobis == [
            f"https://witness.example/oobi/{aid}/witness/{witness}"
        ]


def test_oobier_applies_multisig_agent_policy(helpers):
    with (
        helpers.openKeria() as (_, agent, app, client),
        helpers.openKeria(salter=core.Salter(raw=b"0123456789abcM01")) as (
            _,
            _,
            other_app,
            other_client,
        ),
    ):
        _add_identifier_route(app)
        _add_identifier_route(other_app)
        group = helpers.createMultisigAid(
            [client, other_client],
            "multisig",
            [
                ("multisig0", b"abcdef0123456789"),
                ("multisig1", b"fedcba9876543210"),
            ],
        )[0]
        group_aid = group["prefix"]
        group_hab = agent.hby.habs[group_aid]
        assert isinstance(group_hab, habbing.SignifyGroupHab)

        other = "EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        for eid in (agent.agentHab.pre, other):
            _authorize_endpoint(
                agent,
                cid=group_aid,
                role=kering.Roles.agent,
                eid=eid,
                url="http://agent.example",
            )

        assert agent.oobier.get("multisig", "agent").oobis == [
            f"http://agent.example/oobi/{group_aid}/agent"
        ]
        assert set(agent.oobier.get("multisig", "agent", include_eid=True).oobis) == {
            f"http://agent.example/oobi/{group_aid}/agent/{agent.agentHab.pre}",
            f"http://agent.example/oobi/{group_aid}/agent/{other}",
        }


def test_oobier_submits_url_resolution(helpers):
    with helpers.openKeria() as (_, agent, _, _):
        url = "http://example.com/oobi/EAID/controller"
        operation = agent.oobier.resolve({"url": url, "oobialias": "example"})

        record = agent.hby.db.oobis.get(keys=(url,))
        assert record is not None
        assert record.oobialias == "example"
        assert operation.name.startswith(f"{longrunning.OpTypes.oobi}.")
        assert operation.metadata == {"oobi": url}

        second = "http://example.com/oobi/ESECOND/controller"
        agent.oobier.resolve({"url": second})
        assert agent.hby.db.oobis.get(keys=(second,)).oobialias is None


@pytest.mark.parametrize("body", [None, {}, {"other": "value"}])
def test_oobier_rejects_invalid_resolution(body, helpers):
    with helpers.openKeria() as (_, agent, _, _):
        with pytest.raises(kering.ValidationError):
            agent.oobier.resolve(body)


def test_oobier_url_precedes_unimplemented_rpy(helpers):
    with helpers.openKeria() as (_, agent, _, _):
        url = "http://example.com/oobi/EAID/controller"
        operation = agent.oobier.resolve({"url": url, "rpy": {}})
        assert operation.metadata == {"oobi": url}

        with pytest.raises(NotImplementedError):
            agent.oobier.resolve({"rpy": {}})
