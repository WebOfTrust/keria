# -*- encoding: utf-8 -*-
"""
KERIA
tests.app.test_start module

Environment configuration read by the start command.
"""

import pytest

from keria.app import agenting
from keria.app.cli.commands import start


@pytest.fixture()
def launched(monkeypatch):
    """Runs start.launch with no arguments, capturing the server config
    instead of starting an agency."""
    configs = []
    monkeypatch.setattr(agenting, "runAgency", configs.append)
    for name in ("KERIA_ACCEPT_LEGACY", "KERIA_SIGNATURE_AUTHORITIES"):
        monkeypatch.delenv(name, raising=False)

    def launch(**env):
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        start.launch(start.parser.parse_args([]))
        return configs.pop()

    return launch


@pytest.mark.parametrize(
    "value, expected",
    [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        (" TRUE ", True),
        ("Yes", True),
        ("false", False),
        ("0", False),
        ("no", False),
        ("off", False),
        (" False\n", False),
        ("OFF", False),
    ],
)
def test_accept_legacy_values(launched, value, expected):
    assert launched(KERIA_ACCEPT_LEGACY=value).acceptLegacy is expected


def test_accept_legacy_default(launched):
    assert launched().acceptLegacy is True


@pytest.mark.parametrize("value", ["", "ture", "2", "enabled", "y", "none"])
def test_accept_legacy_refuses_anything_else(launched, value):
    """A value that is not recognisably true or false stops KERIA at startup
    and names the variable, rather than silently turning legacy mode off."""
    with pytest.raises(ValueError, match="KERIA_ACCEPT_LEGACY"):
        launched(KERIA_ACCEPT_LEGACY=value)


def test_signature_authorities_stripped(launched):
    """Entries are stripped and empty ones dropped, so a space after a ';'
    or a trailing ';' does not produce an authority no request can match."""
    config = launched(
        KERIA_SIGNATURE_AUTHORITIES=" keria.example.com ; ;127.0.0.1:3901; "
    )
    assert config.signatureAuthorities == ["keria.example.com", "127.0.0.1:3901"]
    assert config.signaturePolicy().authorities == frozenset(
        {"keria.example.com", "127.0.0.1:3901"}
    )


@pytest.mark.parametrize("value", [None, "", " ; ; "])
def test_signature_authorities_none(launched, value):
    env = {} if value is None else dict(KERIA_SIGNATURE_AUTHORITIES=value)
    config = launched(**env)
    assert config.signatureAuthorities == []
    assert config.signaturePolicy().requireAuthority is False
