"""Scheduler-facing yields and ownership, beyond configuration properties."""

import pytest
from hio.base import doing
from hio.help import decking
from keri.app import configing
from keri.core import coring, eventing, parsing, signing

from keria.app import agenting


@pytest.mark.parametrize("cadence", [0.0, 0.25])
def test_parser_yields(cadence):
    parser = parsing.Parser()
    doer = agenting.ParserDoer(kvy=None, parser=parser, tock=cadence)
    dog = doer.recur()
    try:
        assert next(dog) == cadence  # Step 1: wait for input on an empty stream.
        parser.ims.extend(b"-")  # Supply only the start of a CESR frame.
        assert next(dog) == cadence  # Step 2: wait for the rest of the frame.
    finally:
        dog.close()


def test_witnesser_threads_cadence_through_both_operations():
    key = signing.Signer(raw=b"a" * 32).verfer.qb64
    witness = signing.Signer(raw=b"b" * 32, transferable=False).verfer.qb64
    inception = eventing.incept(keys=[key], ndigs=[coring.Diger(ser=key.encode()).qb64])
    # Adding a witness on rotation requires catch-up before receipt collection.
    event = eventing.rotate(
        pre=inception.pre, keys=[key], dig=inception.said, adds=[witness], toad=1
    )
    calls = []

    class Receiptor:
        def catchup(self, pre, wit, tock=0.0):
            calls.append(("catchup", pre, wit))
            yield tock

        def receipt(self, pre, sn, tock=0.0):
            calls.append(("receipt", pre, sn))
            yield tock

    doer = agenting.Witnesser(
        receiptor=Receiptor(), witners=decking.Deck([{"serder": event}]), tock=0.25
    )
    dog = doer.recur()
    try:
        assert next(dog) == 0.25  # Step 1: dequeue rotation; catch-up yields.
        assert next(dog) == 0.25  # Step 2: catch-up finishes; receipt yields.
        assert next(dog) == 0.25  # Step 3: receipt finishes; outer loop yields.
        # Matching yields alone could pass if a child operation were skipped.
        assert calls == [
            ("catchup", event.pre, witness),
            ("receipt", event.pre, event.sn),
        ]
    finally:
        dog.close()


def test_signaler_is_scheduled_and_expires_signals(helpers):
    with configing.openCF(temp=True) as cf:
        cf.put({"tocks": {"signify": {"signalExpiry": 0.125}}})
        with helpers.openKeria(cf=cf) as (_, agent, _, _):
            signaler = agent.notifier.signaler
            expirers = [d for d in agent.doers if isinstance(d, agenting.SignalExpirer)]
            assert len(expirers) == 1
            expiry = expirers[0]
            # Expiry must service the notifier's live queue, not a separate Signaler.
            assert expiry.signaler is signaler
            assert expiry.tock == 0.125
            signaler.push(attrs={}, topic="test", dt="2000-01-01T00:00:00.000000+00:00")
            doist = doing.Doist(tock=0.03125)
            deeds = doist.enter(
                doers=[expiry]
            )  # Prime expiry; recur has not scanned yet.
            try:
                # Cycles 1-6 visit t=0 through 0.15625; expiry scans at 0 and 0.125.
                for _ in range(6):
                    doist.recur(deeds)  # Advance one 0.03125-second scheduler cycle.
                assert not signaler.signals
                # Add a fresh signal between scans to exercise queue reuse after removal.
                signaler.push(attrs={}, topic="live")
                # Cycles 7-12 visit t=0.1875 through 0.34375; expiry scans at 0.25.
                for _ in range(6):
                    doist.recur(
                        deeds
                    )  # Advance one cycle; the fresh signal must survive.
                assert len(signaler.signals) == 1
                assert signaler.signals[0].topic == "live"
            finally:
                doist.exit(deeds)


def test_agency_service_bindings():
    configured = {
        "bootServer": 0.125,
        "adminServer": 0.25,
        "httpServer": 0.375,
        "shutdown": 0.5,
        "releaser": 30.0,
    }
    with configing.openCF(temp=True) as cf:
        cf.put({"tocks": {"signify": configured}})
        agency = agenting.Agency(name="cadences", bran=None, temp=True, cf=cf)
        config = agenting.KERIAServerConfig(
            bootPort=23903, adminPort=23901, httpPort=23902
        )
        servers = []
        try:
            servers.append(agenting.createBootServerDoer(config, agency))
            app, admin = agenting.createAdminServerDoer(config, agency)
            servers.append(admin)
            servers.append(agenting.createHttpServerDoer(config, agency, app))
            assert [server.tock for server in servers] == [0.125, 0.25, 0.375]
            doist = agenting.agencyDoist([agency, *servers])
            shutdown = doist.doers[-1]
            assert shutdown.tock == 0.5
            dog = shutdown.recur()
            try:
                assert not agency.shouldShutdown
                # Step 1: no shutdown request; yield the configured polling cadence.
                assert next(dog) == configured["shutdown"]
                shutdown.shutdown_received = True
                with pytest.raises(StopIteration):
                    next(dog)  # Step 2: forward the request to Agency and finish.
                assert agency.shouldShutdown
            finally:
                dog.close()
            release = next(d for d in agency.doers if isinstance(d, agenting.Releaser))
            dog = release.recur()
            try:
                assert next(dog) == 30.0  # Step 1: scan the empty cache, then yield.
                assert next(dog) == 30.0  # Step 2: repeat the scan at the same cadence.
            finally:
                dog.close()
        finally:
            for server in servers:
                server.server.close()
            agency.adb.close(clear=True)
