"""Configuration policy tests using KERIpy's published resolver."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from keri import kering
from keri.app import configing, tocking

from keria.app import scheduling


def test_defaults_and_environment_coverage():
    defaults = scheduling.resolveTocks(environ={})
    assert len(defaults.signify) == 19
    assert defaults.signify["releaser"] == 60.0
    assert {v for k, v in defaults.signify.items() if k != "releaser"} == {0.03125}
    assert set(defaults.keri.values()) == {0.03125}
    expected = {key: (index + 1) / 10 for index, key in enumerate(scheduling.SIG_TOCKS)}
    environ = {
        scheduling.SIG_TOCKS[key].env: str(value) for key, value in expected.items()
    }
    assert scheduling.resolveTocks(environ=environ).signify == expected


def test_sample_configs_cover_defaults_without_persisting_them():
    root = Path(__file__).resolve().parents[2]
    defaults = scheduling.resolveTocks(environ={})
    for name in ("scripts/keria.json", "scripts/keri/cf/keria.json"):
        configured = json.loads((root / name).read_text())["tocks"]
        assert configured == {**defaults.keri, "signify": defaults.signify}
    assert defaults.configured == {}


def test_core_alias_and_environment_override_keria_defaults():
    resolved = scheduling.resolveTocks(
        {"vdrEscrow": 0.25}, environ={"KERI_CREDENTIALER_ESCROW_TOCK": "0.0"}
    )
    assert resolved.keri["registrarEscrow"] == 0.25
    assert resolved.keri["credentialerEscrow"] == 0.0
    assert resolved.configured == {"vdrEscrow": 0.25}


@pytest.mark.parametrize(
    "environ, expected",
    [
        ({}, 0.2),
        ({"KERIA_AGENT_TOCK": "0.3"}, 0.3),
        ({"KERIA_AGENT_TOCK": "0.3", "KERIA_ESCROWER_TOCK": "0.4"}, 0.4),
    ],
)
def test_specific_and_coarse_precedence(environ, expected):
    resolved = scheduling.resolveTocks(
        {"signify": {"agent": 0.1, "escrower": 0.2}}, environ=environ
    )
    assert resolved.signify["escrower"] == expected
    assert resolved.signify["initer"] == float(environ.get("KERIA_AGENT_TOCK", 0.1))


def test_legacy_normalization_is_lossless_and_warns_per_load(caplog):
    scheduling.logger.addHandler(caplog.handler)
    try:
        raw = {"receiptor": 0.25, "escrower": 1.0, "signify": {"escrower": 1.0}}
        original = deepcopy(raw)
        resolved = scheduling.resolveTocks(
            raw,
            environ={"KERIA_ESCROWER_TOCK": "0.5", "KERI_RECEIPTOR_TOCK": "0.125"},
        )
        assert raw == original
        assert resolved.signify["escrower"] == 0.5
        assert resolved.keri["receiptor"] == 0.125
        assert not resolved.keri.keys() & scheduling.SIG_TOCKS.keys()
        assert resolved.configured == {"receiptor": 0.25, "signify": {"escrower": 1.0}}
        warning = caplog.text
        assert warning.count("deprecated flat KERIA tocks") == 1
        assert "escrower under tocks.signify" in warning
        # A different config load must receive its own warning; no process-global latch.
        scheduling.resolveTocks(raw, environ={})
        assert len(caplog.records) == 2
        caplog.clear()
        scheduling.resolveTocks(resolved.configured, environ={})
        assert not caplog.records
    finally:
        scheduling.logger.removeHandler(caplog.handler)


def test_conflicting_duplicates_fail_even_with_environment_override():
    with pytest.raises(kering.ConfigurationError, match="Conflicting.*escrower"):
        scheduling.resolveTocks(
            {"escrower": 1.0, "signify": {"escrower": 0.5}},
            environ={"KERIA_ESCROWER_TOCK": "0.25"},
        )


@pytest.mark.parametrize(
    "raw",
    [
        # True == 1.0: merging would hide the invalid legacy boolean.
        {"escrower": True, "signify": {"escrower": 1.0}},
        {"signify": {"escrower": -1}},
    ],
)
def test_invalid_values_are_not_masked(raw):
    with pytest.raises(kering.ConfigurationError, match="escrower"):
        scheduling.resolveTocks(raw, environ={"KERIA_ESCROWER_TOCK": "0.5"})


@pytest.mark.parametrize(
    "raw, error",
    [
        ([], "tocks must be a mapping"),
        ({"signify": []}, r"tocks\.signify must be a mapping"),
        ({"signify": None}, r"tocks\.signify must be a mapping"),
        ({"escrowre": 1.0}, r"Unknown tock configuration key\(s\): escrowre"),
        (
            {"signify": {"escrowre": 1.0}},
            r"Unknown tock configuration key\(s\): escrowre",
        ),
    ],
)
def test_invalid_shape_and_unknown_keys(raw, error):
    with pytest.raises(kering.ConfigurationError, match=error):
        scheduling.resolveTocks(raw, environ={})


def test_invalid_environment():
    with pytest.raises(kering.ConfigurationError, match="KERIA_AGENT_TOCK"):
        scheduling.resolveTocks(environ={"KERIA_AGENT_TOCK": "bad"})


def test_explicit_null_file_block_is_invalid():
    with configing.openCF(temp=True) as cf:
        cf.put({"tocks": None})
        with pytest.raises(kering.ConfigurationError, match="tocks must be a mapping"):
            scheduling.loadTocks(cf)


def test_missing_tocks_block_uses_defaults():
    assert scheduling.loadTocks(None).configured == {}
    with configing.openCF(temp=True) as cf:
        original = {"dt": "2026-09-16T00:00:00.000000+00:00"}
        cf.put(original)
        assert scheduling.loadTocks(cf).configured == {}
        assert cf.get() == original


def test_agent_alias_excludes_server_and_housekeeping_cadences():
    values = scheduling.resolveTocks(environ={"KERIA_AGENT_TOCK": "0.0"}).signify
    assert values["submitter"] == 0.0
    assert values["releaser"] == 60.0
    for key in ("bootServer", "adminServer", "httpServer", "shutdown", "signalExpiry"):
        assert values[key] == scheduling.DEFAULT_TOCK
