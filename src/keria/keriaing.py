# -*- encoding: utf-8 -*-
"""KERIA-specific exceptions shared across database and application layers."""


class KeriaError(Exception):
    """Base class for KERIA exceptions, following KERIpy's KeriError pattern."""


class MissingSchemaError(KeriaError, ValueError):
    """Indexing can resume when the referenced schema becomes available."""


class UnsupportedQueryError(KeriaError, ValueError):
    """The requested query has no supported ordering/equality semantics."""


class IndexNotReadyError(KeriaError, RuntimeError):
    """Credential search cannot claim completeness during repair or failure."""
