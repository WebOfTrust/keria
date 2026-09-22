"""Scheduler-facing yields and ownership, beyond configuration properties."""

import pytest
from contextlib import closing
from hio.base import doing
from hio.help import decking
from keri.app import configing
from keri.core import coring, eventing, parsing, signing

from keria.app import agenting
from keria.app.serving import GracefulShutdownDoer


@pytest.mark.parametrize(
    "cadence",
    [
        pytest.param(0.0, id="next-cycle"),
        pytest.param(0.25, id="positive-delay"),
    ],
)
def test_parser_yields(cadence):
    """ParserDoer must yield its configured cadence while waiting for either an
    initial frame or missing bytes, including an explicit zero cadence.
    """
    parser = parsing.Parser()
    doer = agenting.ParserDoer(kvy=None, parser=parser, tock=cadence)
    dog = doer.recur()
    with closing(dog):
        assert next(dog) == cadence  # Step 1: wait for input on an empty stream.
        parser.ims.extend(b"-")  # Supply only the start of a CESR frame.
        assert next(dog) == cadence  # Step 2: wait for the rest of the frame.


def test_witnesser_threads_tock_through_receiptor_child_ops():
    """
    Proves that the Witnesser passes its parent tock to its child tasks/Doers.

    A rotation adding a witness must pass Witnesser's tock through catch-up
    and receipt collection, then use that tock for its own outer-loop yield.
    """
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
    with closing(dog):
        assert next(dog) == 0.25  # Step 1: dequeue rotation; catch-up yields.
        assert next(dog) == 0.25  # Step 2: catch-up finishes; receipt yields.
        assert next(dog) == 0.25  # Step 3: receipt finishes; outer loop yields.
        # Matching yields alone could pass if a child operation were skipped.
        assert calls == [
            ("catchup", event.pre, witness),
            ("receipt", event.pre, event.sn),
        ]


def test_signaler_is_scheduled_and_expires_signals(helpers):
    """The Agent must schedule expiry for its notifier's actual signal queue at
    the configured cadence, removing expired signals while retaining fresh ones.
    """
    with configing.openCF(temp=True) as cf:
        cf.put({"tocks": {"signify": {"signalExpiry": 0.125}}})
        with helpers.openKeria(cf=cf) as (_, agent, _, _):
            signaler = agent.notifier.signaler
            expirer = agent.expirer
            assert expirer in agent.doers  # The Agent must schedule its expiry worker.
            # Expiry must service the notifier's live queue, not a separate Signaler.
            assert expirer.signaler is signaler
            assert expirer.tock == 0.125
            signaler.push(attrs={}, topic="test", dt="2000-01-01T00:00:00.000000+00:00")
            doist = doing.Doist(tock=0.03125)
            # Prime expiry; recur has not scanned yet.
            deeds = doist.enter(doers=[expirer])
            try:
                # Cycles 1-6 visit t=0 through 0.15625; expiry scans at 0 and 0.125.
                for _ in range(6):
                    doist.recur(deeds)  # Advance one 0.03125-second scheduler cycle.
                assert not signaler.signals
                # Add a fresh, non-expiring signal between scans to exercise queue reuse after removal.
                signaler.push(attrs={}, topic="live")
                # Cycles 7-12 visit t=0.1875 through 0.34375; expiry scans at 0.25.
                for _ in range(6):
                    doist.recur(deeds)  # Advance one cycle; retain the fresh signal.
                assert len(signaler.signals) == 1
                assert signaler.signals[0].topic == "live"
            finally:
                doist.exit(deeds)


def test_agency_service_bindings():
    """Bind distinct config values to all three HTTP servers, shutdown, and cleanup;
    verify shutdown and cleanup generators actually yield their assigned cadences.
    """
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
            boot_server = agenting.createBootServerDoer(config, agency)
            servers.append(boot_server)
            app, admin_server = agenting.createAdminServerDoer(config, agency)
            servers.append(admin_server)
            public_server = agenting.createHttpServerDoer(config, agency, app)
            servers.append(public_server)
            assert boot_server.tock == 0.125
            assert admin_server.tock == 0.25
            assert public_server.tock == 0.375
            doist = agenting.agencyDoist([agency, *servers])
            shutdown = next(
                d for d in doist.doers if isinstance(d, GracefulShutdownDoer)
            )
            assert shutdown.tock == 0.5
            shutdown_dog = shutdown.recur()
            with closing(shutdown_dog):
                # Before a request: poll at the configured cadence; keep Agency running.
                assert next(shutdown_dog) == configured["shutdown"]  # First poll.
                assert not agency.shouldShutdown

                # Simulate the flag set by a signal handler; no OS signal is sent.
                shutdown.shutdown_received = True

                # Next poll: request Agency shutdown and complete the generator.
                with pytest.raises(StopIteration):
                    next(shutdown_dog)
                assert agency.shouldShutdown
            releaser = agency.releaser
            releaser_dog = releaser.recur()
            with closing(releaser_dog):
                assert (
                    next(releaser_dog) == 30.0
                )  # Step 1: scan the empty cache, then yield.
                assert (
                    next(releaser_dog) == 30.0
                )  # Step 2: repeat the scan at the same cadence.
        finally:
            for server in servers:
                server.server.close()
            agency.adb.close(clear=True)
