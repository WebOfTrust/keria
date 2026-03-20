# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.multisig module

Focused tests for replaying stored multisig embedded event streams.
"""

from types import SimpleNamespace

from keri.core import coring, eventing as core_eventing, serdering
from keri.core.signing import Salter
from keri.kering import TraitCodex
from keri.vc import proving
from keri.vdr import eventing as veventing

from keria.app import aiding, multisig


def _replay_streams(monkeypatch, *, route, embeds, labels, paths):
    """Simulate follower B replaying a proposal that leader A sent earlier.

    This helper is the shared fixture for the route-specific replay tests
    below. It intentionally models the exact local-after-remote ordering that
    the KLI uses in JoinDoer:

    1. participant A already sent `/multisig/*` and that EXN is stored in mux
       storage,
    2. participant B later approves the same proposal locally,
    3. KERIA must replay A's stored embedded event stream before it can finish
       B's approval.

    Identity mapping used throughout this helper:

    - `StoredRemoteProposalMux` is participant A's already-stored proposal.
    - `fake_agent` is participant B's KERIA agent at approval time.
    - `hab.mhab.pre` is participant B's member AID, which is why the replay
      helper skips EXNs authored by that same prefix.

    The returned `parsed_message_streams` list is therefore the exact stream
    KERIA replays for participant B from participant A's stored EXN.
    """

    class FakeSignifyGroupHab:
        pass

    monkeypatch.setattr(multisig, "SignifyGroupHab", FakeSignifyGroupHab)

    embed_ked = dict(embeds)
    embed_ked["d"] = ""
    _, embed_ked = coring.Saider.saidify(sad=embed_ked, label=coring.Saids.d)
    proposal_esaid = embed_ked["d"]

    parsed_message_streams = []

    # Simple parser mock for testing
    class RecordingParser:
        def parseOne(self, ims):
            parsed_message_streams.append(bytes(ims))

    # Multiplexor mock  for simple testing
    class StoredRemoteProposalMux:
        def get(self, esaid):
            assert esaid == proposal_esaid
            return [
                dict(
                    # Participant A's previously received multisig EXN. The
                    # route and attachments here are the canonical remote
                    # proposal participant B must replay before B continues
                    # with local approval.
                    exn={"r": route, "i": "remote-member-a-pre"},
                    paths=paths,
                )
            ]

    # This fake agent is participant B's KERIA process when B later approves
    # the same proposal through a local HTTP route such as `/registries` or
    # `/credentials`.
    fake_agent = SimpleNamespace(
        mux=StoredRemoteProposalMux(),
        hby=SimpleNamespace(psr=RecordingParser()),
    )
    hab = FakeSignifyGroupHab()
    hab.mhab = SimpleNamespace(pre="local-member-b-pre")

    replays = multisig.replay_multisig_embeds(
        fake_agent,
        hab,
        route=route,
        embeds=embeds,
        labels=labels,
    )

    return replays, parsed_message_streams


def test_replay_multisig_embeds_replays_stored_remote_vcp_anc_stream(
    helpers, monkeypatch
):
    """Follower B must replay leader A's stored `anc` stream for `/multisig/vcp`.

    The concrete fixture objects are:

    - `regser` and `anc`: the proposal participant B is about to approve.
    - `paths["anc"]`: participant A's previously stored signature attachments.
    - `_replay_streams(...)`: participant B's KERIA view at approval time.

    The assertion proves that B replays A's exact anchoring event stream,
    meaning the raw `ixn` bytes plus A's attachment group.
    """
    with helpers.openKeria() as (_, __, app, client):
        app.add_route("/identifiers", aiding.IdentifierCollectionEnd())

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "test", salt)
        aid = op["response"]
        follower_member_b_pre = aid["i"]

        regser = veventing.incept(
            follower_member_b_pre,
            baks=[],
            toad="0",
            nonce=Salter().qb64,
            cnfg=[TraitCodex.NoBackers],
            code=coring.MtrDex.Blake3_256,
        )
        anchor = dict(i=regser.ked["i"], s=regser.ked["s"], d=regser.said)
        anc, _ = helpers.interact(
            pre=follower_member_b_pre,
            bran=salt,
            pidx=0,
            ridx=0,
            dig=aid["d"],
            sn="1",
            data=[anchor],
        )

        replays, parsed_streams = _replay_streams(
            monkeypatch,
            route="/multisig/vcp",
            embeds=dict(vcp=regser.ked, anc=anc.ked),
            labels=("anc",),
            paths={"anc": "FAKE-REMOTE-ANC-ATC"},
        )

        expected = bytearray(serdering.SerderKERI(sad=anc.ked).raw)
        expected.extend(b"FAKE-REMOTE-ANC-ATC")

        assert replays == 1
        assert parsed_streams == [bytes(expected)]


def test_replay_multisig_embeds_replays_stored_remote_rpy_stream(helpers, monkeypatch):
    """Follower B must replay leader A's stored `rpy` stream for `/multisig/rpy`.

    The locally built `rserder` stands in for the exact reply participant B is
    about to endorse. The stored `paths["rpy"]` attachment group represents the
    signature material that already came from participant A's earlier EXN.
    """
    with helpers.openKeria() as (_, agent, app, client):
        app.add_route("/identifiers", aiding.IdentifierCollectionEnd())

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "user1", salt)
        aid = op["response"]
        rserder = helpers.endrole(aid["i"], agent.agentHab.pre)

        replays, parsed_streams = _replay_streams(
            monkeypatch,
            route="/multisig/rpy",
            embeds=dict(rpy=rserder.ked),
            labels=("rpy",),
            paths={"rpy": "FAKE-REMOTE-RPY-ATC"},
        )

        expected = bytearray(serdering.SerderKERI(sad=rserder.ked).raw)
        expected.extend(b"FAKE-REMOTE-RPY-ATC")

        assert replays == 1
        assert parsed_streams == [bytes(expected)]


def test_replay_multisig_embeds_replays_stored_remote_issue_streams(
    helpers, monkeypatch
):
    """Follower B must replay A's `anc` and `acdc` streams for `/multisig/iss`.

    This is the most subtle replay case:

    - `anc` is the anchoring KEL event that both participants must mirror.
    - `acdc` is the credential payload stream participant A already attached.
    - participant B replays both before B's local issuance approval continues.
    """
    with helpers.openKeria() as (_, __, app, client):
        app.add_route("/identifiers", aiding.IdentifierCollectionEnd())

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "issuer", salt)
        aid = op["response"]
        follower_member_b_pre = aid["i"]

        regser = veventing.incept(
            follower_member_b_pre,
            baks=[],
            toad="0",
            nonce=Salter().qb64,
            cnfg=[TraitCodex.NoBackers],
            code=coring.MtrDex.Blake3_256,
        )
        creder = proving.credential(
            issuer=follower_member_b_pre,
            schema="EFgnk_c08WmZGgv9_mpldibRuqFMTQN-rAgtD-TCOwbs",
            recipient=follower_member_b_pre,
            data=dict(
                LEI="254900DA0GOGCFVWB618", dt="2021-01-01T00:00:00.000000+00:00"
            ),
            source={},
            status=regser.pre,
        )
        iserder = veventing.issue(
            vcdig=creder.said,
            regk=regser.pre,
            dt="2021-01-01T00:00:00.000000+00:00",
        )
        anchor = dict(i=iserder.ked["i"], s=iserder.ked["s"], d=iserder.said)
        anc, _ = helpers.interact(
            pre=follower_member_b_pre,
            bran=salt,
            pidx=0,
            ridx=0,
            dig=aid["d"],
            sn="1",
            data=[anchor],
        )

        replays, parsed_streams = _replay_streams(
            monkeypatch,
            route="/multisig/iss",
            embeds=dict(acdc=creder.sad, iss=iserder.ked, anc=anc.ked),
            labels=("anc", "acdc"),
            paths={
                "anc": "FAKE-REMOTE-ANC-ATC",
                "acdc": "FAKE-REMOTE-ACDC-ATC",
            },
        )

        expected_anc = bytearray(serdering.SerderKERI(sad=anc.ked).raw)
        expected_anc.extend(b"FAKE-REMOTE-ANC-ATC")
        expected_acdc = bytearray(serdering.SerderACDC(sad=creder.sad).raw)
        expected_acdc.extend(b"FAKE-REMOTE-ACDC-ATC")

        assert replays == 1
        assert parsed_streams == [bytes(expected_anc), bytes(expected_acdc)]


def test_replay_multisig_embeds_replays_stored_remote_rev_anc_stream(
    helpers, monkeypatch
):
    """Follower B must replay A's stored anchoring event for `/multisig/rev`.

    Revocation only needs the previously stored `anc` stream replayed before
    participant B processes the local revocation approval.
    """
    with helpers.openKeria() as (_, __, app, client):
        app.add_route("/identifiers", aiding.IdentifierCollectionEnd())

        salt = b"0123456789abcdef"
        op = helpers.createAid(client, "issuer", salt)
        aid = op["response"]
        follower_member_b_pre = aid["i"]

        regser = veventing.incept(
            follower_member_b_pre,
            baks=[],
            toad="0",
            nonce=Salter().qb64,
            cnfg=[TraitCodex.NoBackers],
            code=coring.MtrDex.Blake3_256,
        )
        issue_serder = veventing.issue(
            vcdig=regser.said,
            regk=regser.pre,
            dt="2021-01-01T00:00:00.000000+00:00",
        )
        rserder = veventing.revoke(
            vcdig=regser.said,
            regk=regser.pre,
            dig=issue_serder.said,
            dt="2021-01-01T00:00:00.000000+00:00",
        )
        anchor = dict(i=rserder.ked["i"], s=rserder.ked["s"], d=rserder.said)
        anc = core_eventing.interact(
            pre=follower_member_b_pre, dig=aid["d"], sn=1, data=[anchor]
        )

        replays, parsed_streams = _replay_streams(
            monkeypatch,
            route="/multisig/rev",
            embeds=dict(rev=rserder.ked, anc=anc.ked),
            labels=("anc",),
            paths={"anc": "FAKE-REMOTE-ANC-ATC"},
        )

        expected = bytearray(serdering.SerderKERI(sad=anc.ked).raw)
        expected.extend(b"FAKE-REMOTE-ANC-ATC")

        assert replays == 1
        assert parsed_streams == [bytes(expected)]
