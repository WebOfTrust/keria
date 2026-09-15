"""Configuration policy tests using KERIpy's published resolver."""

from copy import deepcopy

import pytest
from keri import kering
from keri.app import configing

from keria.app import tocking


def test_defaults_and_environment_coverage():
    defaults = tocking.resolveTocks(environ={})
    assert len(defaults.signify) == 12
    assert all(value == 0.0 for value in defaults.signify.values())
    expected = {key: (index + 1) / 10 for index, key in enumerate(tocking.TOCKS)}
    environ = {tocking.TOCKS[key].env: str(value) for key, value in expected.items()}
    assert tocking.resolveTocks(environ=environ).signify == expected
    with pytest.raises(TypeError):
        defaults.signify["escrower"] = 2.0
    with pytest.raises(TypeError):
        defaults.keri["receiptor"] = 2.0


@pytest.mark.parametrize(
    "environ, expected",
    [
        ({}, 0.2),
        ({"KERIA_AGENT_TOCK": "0.3"}, 0.3),
        ({"KERIA_AGENT_TOCK": "0.3", "KERIA_ESCROWER_TOCK": "0.4"}, 0.4),
    ],
)
def test_specific_and_coarse_precedence(environ, expected):
    resolved = tocking.resolveTocks(
        {"signify": {"agent": 0.1, "escrower": 0.2}}, environ=environ
    )
    assert resolved.signify["escrower"] == expected
    assert resolved.signify["initer"] == float(environ.get("KERIA_AGENT_TOCK", 0.1))


def test_legacy_normalization_is_lossless_and_warns_per_load(caplog):
    tocking.logger.addHandler(caplog.handler)
    try:
        raw = {"receiptor": 0.25, "escrower": 1.0, "signify": {"escrower": 1.0}}
        original = deepcopy(raw)
        resolved = tocking.resolveTocks(
            raw,
            environ={"KERIA_ESCROWER_TOCK": "0.5", "KERI_RECEIPTOR_TOCK": "0.125"},
            source="agent.json",
        )
        assert raw == original
        assert resolved.signify["escrower"] == 0.5
        assert resolved.keri["receiptor"] == 0.125
        assert resolved.configured == {"receiptor": 0.25, "signify": {"escrower": 1.0}}
        warning = caplog.text
        assert warning.count("deprecated flat KERIA tocks") == 1
        assert "agent.json" in warning
        assert "escrower under tocks.signify" in warning
        # A different config load must receive its own warning; no process-global latch.
        tocking.resolveTocks(raw, environ={}, source="other.json")
        assert len(caplog.records) == 2
        caplog.clear()
        tocking.resolveTocks(resolved.configured, environ={})
        assert not caplog.records
    finally:
        tocking.logger.removeHandler(caplog.handler)


def test_conflicting_duplicates_fail_even_with_environment_override():
    with pytest.raises(kering.ConfigurationError, match="Conflicting.*escrower"):
        tocking.resolveTocks(
            {"escrower": 1.0, "signify": {"escrower": 0.5}},
            environ={"KERIA_ESCROWER_TOCK": "0.25"},
        )


@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("value", [True, None, "0.25", -1, float("nan"), float("inf")])
def test_invalid_values_are_not_masked(nested, value):
    raw = {"escrower": value}
    if nested:
        raw = {"signify": raw}
    with pytest.raises(kering.ConfigurationError, match="escrower"):
        tocking.resolveTocks(raw, environ={"KERIA_ESCROWER_TOCK": "0.5"})


@pytest.mark.parametrize(
    "raw",
    [
        [],
        {"signify": []},
        {"signify": None},
        {"escrowre": 1.0},
        {"signify": {"escrowre": 1.0}},
    ],
)
def test_invalid_shape_and_unknown_keys(raw):
    with pytest.raises(kering.ConfigurationError, match="agent.json"):
        tocking.resolveTocks(raw, environ={}, source="agent.json")


@pytest.mark.parametrize("value", ["", "NaN", "inf", "-1", "bad"])
def test_invalid_environment(value):
    with pytest.raises(kering.ConfigurationError, match="KERIA_AGENT_TOCK"):
        tocking.resolveTocks(environ={"KERIA_AGENT_TOCK": value})


def test_explicit_null_file_block_is_invalid():
    with configing.openCF(temp=True) as cf:
        cf.put({"tocks": None})
        with pytest.raises(kering.ConfigurationError, match="tocks must be a mapping"):
            tocking.loadTocks(cf)
