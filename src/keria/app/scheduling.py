"""KERIA scheduler configuration and compatibility with legacy flat keys."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

from keri import kering
from keri.app import tocking
from keri.app.tocking import Tock, TockAlias

logger = logging.getLogger(__name__)

# One cycle of KERIA's 32 Hz root Doist. Zero remains an explicit next-cycle option.
DEFAULT_TOCK = 0.03125

# Apply KERIA's default tock policy without mutating KERIpy's process-global registry.
# Keep its keys, environment variables, aliases, and precedence rules intact.
KERI_TOCKS: dict[str, Tock] = {
    key: Tock(definition.env, DEFAULT_TOCK) for key, definition in tocking.TOCKS.items()
}

# tocks.signify default tock values mapped by config prop name to Tock env key and default
SIG_TOCKS: dict[str, Tock] = {}

# Tock subkeys cascading tock to their target subkeys
SIG_TOCK_ALIASES: dict[str, TockAlias] = {}

# Agent initialization and key-state queries (agenting.py - Initer, Querier)
KERIA_INITER_TOCK_KEY = "KERIA_INITER_TOCK"
KERIA_QUERIER_TOCK_KEY = "KERIA_QUERIER_TOCK"

SIG_TOCKS["initer"] = Tock(KERIA_INITER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["querier"] = Tock(KERIA_QUERIER_TOCK_KEY, DEFAULT_TOCK)

# Escrow and inbound message processing (agenting.py - Escrower, ParserDoer)
KERIA_ESCROWER_TOCK_KEY = "KERIA_ESCROWER_TOCK"
KERIA_PARSER_TOCK_KEY = "KERIA_PARSER_TOCK"

SIG_TOCKS["escrower"] = Tock(KERIA_ESCROWER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["parser"] = Tock(KERIA_PARSER_TOCK_KEY, DEFAULT_TOCK)

# Witness and delegation coordination (agenting.py - Witnesser, Delegator)
KERIA_WITNESSER_TOCK_KEY = "KERIA_WITNESSER_TOCK"
KERIA_DELEGATOR_TOCK_KEY = "KERIA_DELEGATOR_TOCK"

SIG_TOCKS["witnesser"] = Tock(KERIA_WITNESSER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["delegator"] = Tock(KERIA_DELEGATOR_TOCK_KEY, DEFAULT_TOCK)

# Exchange and credential workflows (agenting.py - ExchangeSender, Granter, Admitter)
KERIA_EXCHANGE_SENDER_TOCK_KEY = "KERIA_EXCHANGE_SENDER_TOCK"
KERIA_GRANTER_TOCK_KEY = "KERIA_GRANTER_TOCK"
KERIA_ADMITTER_TOCK_KEY = "KERIA_ADMITTER_TOCK"

SIG_TOCKS["exchangeSender"] = Tock(KERIA_EXCHANGE_SENDER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["granter"] = Tock(KERIA_GRANTER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["admitter"] = Tock(KERIA_ADMITTER_TOCK_KEY, DEFAULT_TOCK)

# Multisig group coordination (agenting.py - GroupRequester)
KERIA_GROUP_REQUESTER_TOCK_KEY = "KERIA_GROUP_REQUESTER_TOCK"

SIG_TOCKS["groupRequester"] = Tock(KERIA_GROUP_REQUESTER_TOCK_KEY, DEFAULT_TOCK)

# Credential and exchange indexing (agenting.py - SeekerDoer, ExchangeCueDoer)
KERIA_SEEKER_TOCK_KEY = "KERIA_SEEKER_TOCK"
KERIA_EXCHANGE_CUE_TOCK_KEY = "KERIA_EXCHANGE_CUE_TOCK"

SIG_TOCKS["seeker"] = Tock(KERIA_SEEKER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["exchangecue"] = Tock(KERIA_EXCHANGE_CUE_TOCK_KEY, DEFAULT_TOCK)

# Witness resubmission queue coordination
KERIA_SUBMITTER_TOCK_KEY = "KERIA_SUBMITTER_TOCK"
SIG_TOCKS["submitter"] = Tock(KERIA_SUBMITTER_TOCK_KEY, DEFAULT_TOCK)

# Coarse Agent alias covering all Agent component tocks above
KERIA_AGENT_TOCK_KEY = "KERIA_AGENT_TOCK"
SIG_TOCK_ALIASES["agent"] = TockAlias(
    env=KERIA_AGENT_TOCK_KEY,
    targets=tuple(SIG_TOCKS),
)


# Server I/O, shutdown, and housekeeping are independent
# of the coarse Agent-work alias above.
KERIA_BOOT_SERVER_TOCK_KEY = "KERIA_BOOT_SERVER_TOCK"
KERIA_ADMIN_SERVER_TOCK_KEY = "KERIA_ADMIN_SERVER_TOCK"
KERIA_HTTP_SERVER_TOCK_KEY = "KERIA_HTTP_SERVER_TOCK"
KERIA_SHUTDOWN_TOCK_KEY = "KERIA_SHUTDOWN_TOCK"
KERIA_SIGNAL_EXPIRY_TOCK_KEY = "KERIA_SIGNAL_EXPIRY_TOCK"
KERIA_RELEASER_TOCK_KEY = "KERIA_RELEASER_TOCK"

SIG_TOCKS["bootServer"] = Tock(KERIA_BOOT_SERVER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["adminServer"] = Tock(KERIA_ADMIN_SERVER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["httpServer"] = Tock(KERIA_HTTP_SERVER_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["shutdown"] = Tock(KERIA_SHUTDOWN_TOCK_KEY, DEFAULT_TOCK)
SIG_TOCKS["signalExpiry"] = Tock(KERIA_SIGNAL_EXPIRY_TOCK_KEY, DEFAULT_TOCK)
# Full scan of open Agents against a 24-hour inactivity timeout.
SIG_TOCKS["releaser"] = Tock(KERIA_RELEASER_TOCK_KEY, 60.0)


@dataclass(frozen=True)
class TockConfiguration:
    """Effective scheduler tock cadences and canonical file values without overrides."""

    # Resolved tocks for Doers/DoDoers/doified functions defined in KERIpy
    # This includes environment variable overrides and defaults defined in this scheduling module.
    keri: dict[str, float]
    # Resolved tocks for KERIA-defined Doers/DoDoers/doified functions
    # This includes environment variable overrides and defaults defined in this scheduling module.
    signify: dict[str, float]
    # This contains the Agent's config from the loaded config file
    configured: dict


def resolveTocks(cfTocks=None, *, environ=None):
    """Resolve one load, warning once if it contains legacy flat KERIA keys.

    Environment values override file values using KERIpy's precedence rules.
    Canonical file values retain explicit settings only, never environment
    overrides or defaults. Callers may persist them when provisioning new Agents;
    resolving an existing file does not rewrite it.
    """
    cfTocks = {} if cfTocks is None else cfTocks
    if not isinstance(cfTocks, Mapping):
        raise kering.ConfigurationError("tocks must be a mapping")
    sigCfTocks = cfTocks.get("signify", {})  # signify tocks read from config file
    if not isinstance(sigCfTocks, Mapping):
        raise kering.ConfigurationError("tocks.signify must be a mapping")

    # The SIG_TOCKS config items are valid at the top level of "tocks" as legacy,
    # backwards compatibility items. They are also valid inside the "tocks.signify" prop.
    legacy = {key: value for key, value in cfTocks.items() if key in SIG_TOCKS}
    if legacy:
        logger.warning(
            "deprecated flat KERIA tocks; move %s under tocks.signify. "
            "Legacy placement will be removed in a future announced release.",
            ", ".join(sorted(legacy)),
        )

    # Validate legacy values before merging can overwrite them.
    tocking.resolveTocks(
        legacy,
        tocks=SIG_TOCKS,
        aliases=SIG_TOCK_ALIASES,
        environ={},
        reserved=list(),
    )
    for key in legacy.keys() & sigCfTocks.keys():
        if legacy[key] != sigCfTocks[key]:
            raise kering.ConfigurationError(
                f"Conflicting values for tocks.{key} and tocks.signify.{key}"
            )

    # pull the legacy and new tocks.signify config into a consolidated config objet
    sigTocks = {**legacy, **sigCfTocks}  # tocks.signify overwrites legacy tocks

    # get the non-signify tocks config
    configured = {key: value for key, value in cfTocks.items() if key not in SIG_TOCKS}
    if legacy or "signify" in cfTocks:  # only add signify tocks if they are present
        configured["signify"] = sigTocks
    keri = tocking.resolveTocks(configured, tocks=KERI_TOCKS, environ=environ)
    signify = tocking.resolveTocks(
        sigTocks,
        tocks=SIG_TOCKS,
        aliases=SIG_TOCK_ALIASES,
        environ=environ,
        reserved=list(),
    )

    return TockConfiguration(
        keri=keri,
        signify=signify,
        configured=configured,
    )


def loadTocks(cf):
    """Read one Configer, resolving values without changing its file."""
    config = cf.get() if cf is not None else {}
    if "tocks" in config and config["tocks"] is None:
        raise kering.ConfigurationError(f"{cf.path}: tocks must be a mapping")
    cfTocks = config.get("tocks", {})
    return resolveTocks(cfTocks)
