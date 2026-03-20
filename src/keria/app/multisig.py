# -*- encoding: utf-8 -*-
"""
KERIA
keria.app.multisig module

Shared helpers for multisig approval flows.
"""

from keri.app.habbing import SignifyGroupHab
from keri.core import coring


def replay_multisig_embeds(agent, hab, *, route, embeds, labels):
    """Replay stored non-local multisig embedded events before local approval.

    Signify follower approval can happen after the matching multisig EXN was
    already received and stored. In that local-after-remote ordering, KLI
    explicitly replays the remote participant's signed embedded event streams
    before it parses the follower's approval of the same proposal.

    This helper restores that ordering for KERIA approval endpoints. It derives
    the embedded-section SAID from the local approval payload, loads matching
    non-local multisig EXNs from the mux, and replays the selected embedded
    labels plus their pathed attachments through the parser.

    The ``labels`` argument uses EXN embed-label names, not concrete KEL/TEL
    event-type names. For example, the multisig protocol uses the embed label
    ``anc`` for the anchoring KEL event even when the concrete event is an
    interaction event (``ixn``).
    """
    if not isinstance(hab, SignifyGroupHab):
        return 0

    embed_ked = dict(embeds)
    embed_ked["d"] = ""
    _, embed_ked = coring.Saider.saidify(sad=embed_ked, label=coring.Saids.d)

    replays = 0
    for msg in agent.mux.get(esaid=embed_ked["d"]):
        exn = msg["exn"]
        if exn["r"] != route or exn["i"] == hab.mhab.pre:
            continue

        paths = msg["paths"]
        for label in labels:
            if label not in paths:
                continue

            sadder = coring.Sadder(ked=embeds[label])
            attachment = paths[label]
            if isinstance(attachment, str):
                attachment = attachment.encode("utf-8")

            ims = bytearray(sadder.raw)
            ims.extend(attachment)
            agent.hby.psr.parseOne(ims=ims)

        replays += 1

    return replays
