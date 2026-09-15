"""KERIA scheduler configuration and compatibility with legacy flat keys."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from keri import kering
from keri.app import tocking as keritocking

logger = logging.getLogger(__name__)

TOCKS = {
    "initer": keritocking.Tock("KERIA_INITER_TOCK"),
    "querier": keritocking.Tock("KERIA_QUERIER_TOCK"),
    "escrower": keritocking.Tock("KERIA_ESCROWER_TOCK"),
    "parser": keritocking.Tock("KERIA_PARSER_TOCK"),
    "witnesser": keritocking.Tock("KERIA_WITNESSER_TOCK"),
    "delegator": keritocking.Tock("KERIA_DELEGATOR_TOCK"),
    "exchangeSender": keritocking.Tock("KERIA_EXCHANGE_SENDER_TOCK"),
    "granter": keritocking.Tock("KERIA_GRANTER_TOCK"),
    "admitter": keritocking.Tock("KERIA_ADMITTER_TOCK"),
    "groupRequester": keritocking.Tock("KERIA_GROUP_REQUESTER_TOCK"),
    "seeker": keritocking.Tock("KERIA_SEEKER_TOCK"),
    "exchangecue": keritocking.Tock("KERIA_EXCHANGE_CUE_TOCK"),
}

TOCK_ALIASES = {
    "agent": keritocking.TockAlias("KERIA_AGENT_TOCK", tuple(TOCKS)),
}


@dataclass(frozen=True)
class TockConfiguration:
    """Effective immutable cadences and canonical file values without overrides."""

    keri: Mapping
    signify: Mapping
    configured: dict


def _signify(values, *, environ, path="tocks.signify"):
    try:
        return keritocking.resolveTocks(
            values, tocks=TOCKS, aliases=TOCK_ALIASES, environ=environ, reserved=()
        )
    except kering.ConfigurationError as ex:
        raise kering.ConfigurationError(f"{path}: {ex}") from ex


def resolveTocks(cfTocks=None, *, environ=None, source="configuration"):
    """Resolve one load, warning once if it contains legacy flat KERIA keys.

    Environment values override file values using KERIpy's precedence rules.
    Canonical file values retain explicit settings only, never environment
    overrides or defaults. Callers may persist them when provisioning new Agents;
    resolving an existing file does not rewrite it.
    """
    raw = {} if cfTocks is None else cfTocks
    try:
        if not isinstance(raw, Mapping):
            raise kering.ConfigurationError("tocks must be a mapping")
        nested = raw.get("signify", {})
        if not isinstance(nested, Mapping):
            raise kering.ConfigurationError("tocks.signify must be a mapping")

        legacy = {key: value for key, value in raw.items() if key in TOCKS}
        # Validate both forms before merging, even if an override would mask them.
        _signify(legacy, environ={}, path="legacy tocks")
        _signify(nested, environ={})
        for key in legacy.keys() & nested.keys():
            if legacy[key] != nested[key]:
                raise kering.ConfigurationError(
                    f"Conflicting values for tocks.{key} and tocks.signify.{key}"
                )

        signify = {**legacy, **nested}
        configured = {key: value for key, value in raw.items() if key not in TOCKS}
        if legacy or "signify" in raw:
            configured["signify"] = signify
        keri = keritocking.resolveTocks(configured, environ=environ)
        resolved = _signify(signify, environ=environ)
    except kering.ConfigurationError as ex:
        raise kering.ConfigurationError(f"{source}: {ex}") from ex

    if legacy:
        logger.warning(
            "%s: deprecated flat KERIA tocks; move %s under tocks.signify. "
            "Legacy placement will be removed in a future announced release.",
            source,
            ", ".join(sorted(legacy)),
        )
    return TockConfiguration(
        keri=MappingProxyType(keri),
        signify=MappingProxyType(resolved),
        configured=configured,
    )


def loadTocks(cf):
    """Read one Configer, resolving values without changing its file."""
    config = cf.get() if cf is not None else {}
    if "tocks" in config and config["tocks"] is None:
        raise kering.ConfigurationError(f"{cf.path}: tocks must be a mapping")
    return resolveTocks(config.get("tocks", {}), source=cf.path if cf else "defaults")
