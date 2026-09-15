"""Scheduler-facing yields and ownership, beyond configuration properties."""

from types import SimpleNamespace

import pytest
from hio.base import doing
from hio.help import decking
from keri.app import configing
from keri.core import parsing

from keria.app import agenting
from keria.app.serving import GracefulShutdownDoer


@pytest.mark.parametrize("cadence", [0.0, 0.25])
def test_parser_yields(cadence):
    parser = parsing.Parser()
    doer = agenting.ParserDoer(kvy=None, parser=parser, tock=cadence)
    dog = doer.recur()
    try:
        assert next(dog) == cadence
        parser.ims.extend(
            b"-"
        )  # An incomplete CESR frame must also yield at this cadence.
        assert next(dog) == cadence
    finally:
        dog.close()


def test_shutdown_yields():
    cadence = 0.25
    agency = SimpleNamespace(shouldShutdown=False)
    shutdown = GracefulShutdownDoer(agency=agency, tock=cadence)
    dog = shutdown.recur()
    assert next(dog) == cadence
    shutdown.shutdown_received = True
    with pytest.raises(StopIteration):
        next(dog)
    assert agency.shouldShutdown


def test_witnesser_threads_cadence_through_both_operations():
    class Receiptor:
        def catchup(self, pre, wit, tock=0.0):
            yield tock

        def receipt(self, pre, sn, tock=0.0):
            yield tock

    event = SimpleNamespace(pre="prefix", sn=1, ked={"t": "rot", "ba": ["witness"]})
    doer = agenting.Witnesser(
        receiptor=Receiptor(), witners=decking.Deck([{"serder": event}]), tock=0.25
    )
    dog = doer.recur()
    try:
        assert [next(dog), next(dog), next(dog)] == [0.25, 0.25, 0.25]
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
            assert expiry.signaler is signaler
            assert expiry.tock == 0.125
            signaler.push(attrs={}, topic="test", dt="2000-01-01T00:00:00.000000+00:00")
            doist = doing.Doist(tock=0.03125)
            deeds = doist.enter(doers=[expiry])
            try:
                for _ in range(6):
                    doist.recur(deeds)
                assert not signaler.signals
                signaler.push(attrs={}, topic="live")
                for _ in range(6):
                    doist.recur(deeds)
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
            release = next(d for d in agency.doers if isinstance(d, agenting.Releaser))
            dog = release.recur()
            try:
                assert next(dog) == 30.0
                assert next(dog) == 30.0
            finally:
                dog.close()
        finally:
            for server in servers:
                server.server.close()
            agency.adb.close(clear=True)
