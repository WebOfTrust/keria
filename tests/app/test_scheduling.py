"""Configuration policy tests using KERIpy's published resolver."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from keri import kering
from keri.app import configing

from keria.app import scheduling


def test_defaults_and_environment_coverage():
    """Verify KERIA's one-tick defaults, slower cleanup exception, and a working
    environment override for every KERIA tock setting.
    """
    defaults = scheduling.resolveTocks(environ={})
    assert len(defaults.signify) == 19
    assert defaults.signify["releaser"] == 60.0
    assert {v for k, v in defaults.signify.items() if k != "releaser"} == {0.03125}
    assert set(defaults.keri.values()) == {0.03125}
    # Generate unique tock values per SIG_TOCKS entry to expose environment variables accidentally bound to the wrong key.
    expected = {key: (index + 1) / 10 for index, key in enumerate(scheduling.SIG_TOCKS)}
    environ = {
        scheduling.SIG_TOCKS[key].env: str(value) for key, value in expected.items()
    }
    assert scheduling.resolveTocks(environ=environ).signify == expected


@pytest.mark.parametrize("name", ["scripts/keria.json", "scripts/keri/cf/keria.json"])
def test_sample_configs_match_tock_defaults(name):
    """Keep both sample configs complete and aligned with all registered tock defaults."""
    root = Path(__file__).resolve().parents[2]
    defaults = scheduling.resolveTocks(environ={})
    configured = json.loads((root / name).read_text())["tocks"]
    assert configured == {**defaults.keri, "signify": defaults.signify}


def test_keria_resolver_preserves_core_overrides():
    """KERIA's resolver preserves KERIpy alias and environment overrides when
    applying its own core defaults; these settings stay outside tocks.signify.
    """
    resolved = scheduling.resolveTocks(
        {"vdrEscrow": 0.25}, environ={"KERI_CREDENTIALER_ESCROW_TOCK": "0.0"}
    )
    assert resolved.keri["registrarEscrow"] == 0.25
    assert resolved.keri["credentialerEscrow"] == 0.0


@pytest.mark.parametrize(
    "environ, expected_escrower, expected_initer",
    [
        ({}, 0.2, 0.1),
        ({"KERIA_AGENT_TOCK": "0.3"}, 0.3, 0.3),
        ({"KERIA_AGENT_TOCK": "0.3", "KERIA_ESCROWER_TOCK": "0.4"}, 0.4, 0.3),
    ],
)
def test_specific_and_coarse_precedence(environ, expected_escrower, expected_initer):
    """Specific file values beat group file values; group environment values beat
    file values, and specific environment values take highest precedence.
    """
    resolved = scheduling.resolveTocks(
        {"signify": {"agent": 0.1, "escrower": 0.2}}, environ=environ
    )
    assert resolved.signify["escrower"] == expected_escrower
    # An untargeted worker still follows the group value at the winning layer.
    assert resolved.signify["initer"] == expected_initer


def test_legacy_normalization_is_lossless_and_warns_per_load(caplog, monkeypatch):
    """Normalize matching legacy/canonical settings without mutating the input or
    persisting environment overrides; warn on each legacy load, not canonical loads.
    """
    # Capture directly, without also forwarding the same record to pytest's root handler.
    monkeypatch.setattr(scheduling.logger, "propagate", False)
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
        # Legacy KERIA keys must be removed before passing the core map to Habery.
        assert not resolved.keri.keys() & scheduling.SIG_TOCKS.keys()  # should be empty
        assert resolved.configured == {"receiptor": 0.25, "signify": {"escrower": 1.0}}
        warning = caplog.text
        assert warning.count("deprecated flat KERIA tocks") == 1
        assert "escrower under tocks.signify" in warning
        # A different config load must receive its own warning; no process-global latch.
        scheduling.resolveTocks(raw, environ={})
        assert len(caplog.records) == 2
        caplog.clear()
        # Reload the normalized form: no legacy placement remains to warn about.
        scheduling.resolveTocks(resolved.configured, environ={})
        assert not caplog.records
    finally:
        scheduling.logger.removeHandler(caplog.handler)


def test_conflicting_duplicates_fail_even_with_environment_override():
    """Reject contradictory legacy and canonical values even when an environment
    override would otherwise hide the ambiguous file configuration.
    """
    with pytest.raises(kering.ConfigurationError, match="Conflicting.*escrower"):
        scheduling.resolveTocks(
            {"escrower": 1.0, "signify": {"escrower": 0.5}},
            environ={"KERIA_ESCROWER_TOCK": "0.25"},
        )


@pytest.mark.parametrize(
    "raw, environ, error",
    [
        # True == 1.0: merging must not hide the invalid legacy boolean.
        pytest.param(
            {"escrower": True, "signify": {"escrower": 1.0}},
            {"KERIA_ESCROWER_TOCK": "0.5"},
            "escrower",
            id="legacy-boolean",
        ),
        pytest.param(
            {"signify": {"escrower": -1}},
            {"KERIA_ESCROWER_TOCK": "0.5"},
            "escrower",
            id="negative",
        ),
        pytest.param([], {}, "tocks must be a mapping", id="root-list"),
        pytest.param(
            {"signify": []}, {}, r"tocks\.signify must be a mapping", id="signify-list"
        ),
        pytest.param(
            {"signify": None},
            {},
            r"tocks\.signify must be a mapping",
            id="signify-null",
        ),
        pytest.param(
            {"escrowre": 1.0},
            {},
            r"Unknown tock configuration key\(s\): escrowre",
            id="unknown-core-key",
        ),
        pytest.param(
            {"signify": {"escrowre": 1.0}},
            {},
            r"Unknown tock configuration key\(s\): escrowre",
            id="unknown-signify-key",
        ),
        pytest.param(
            {},
            {"KERIA_AGENT_TOCK": "bad"},
            "KERIA_AGENT_TOCK",
            id="invalid-environment",
        ),
    ],
)
def test_invalid_tock_configuration(raw, environ, error):
    """Reject malformed sections, unknown keys, and invalid file/environment values;
    valid overrides must not conceal invalid file values. Errors identify the setting.
    """
    with pytest.raises(kering.ConfigurationError, match=error):
        scheduling.resolveTocks(raw, environ=environ)


def test_explicit_null_file_block_is_invalid():
    """Treat an explicit null tocks block as invalid, not as omitted configuration."""
    with configing.openCF(temp=True) as cf:
        cf.put({"tocks": None})
        with pytest.raises(kering.ConfigurationError, match="tocks must be a mapping"):
            scheduling.loadTocks(cf)


def test_missing_tocks_block_uses_defaults():
    """Accept absent configuration without inventing explicit settings or rewriting
    an existing file that contains no tocks block.
    """
    assert scheduling.loadTocks(None).configured == {}
    with configing.openCF(temp=True) as cf:
        original = {"dt": "2026-09-16T00:00:00.000000+00:00"}
        cf.put(original)
        assert scheduling.loadTocks(cf).configured == {}
        assert cf.get() == original


def test_agent_alias_excludes_server_and_housekeeping_cadences():
    """The Agent group override includes submission work but must not retime
    HTTP servers, shutdown polling, signal expiry, or inactive-Agent cleanup.
    """
    values = scheduling.resolveTocks(environ={"KERIA_AGENT_TOCK": "0.0"}).signify
    assert values["submitter"] == 0.0
    assert values["releaser"] == 60.0
    for key in ("bootServer", "adminServer", "httpServer", "shutdown", "signalExpiry"):
        assert values[key] == scheduling.DEFAULT_TOCK
