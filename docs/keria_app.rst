KERIA App API Documentation
===========================

keria.app.agenting
------------------

.. automodule:: keria.app.agenting
    :members:

Agency and Agent Configuration
==============================

A KERIA Agency can be configured with either environment variables or a configuration file.
The configuration file is a JSON file. Both alternatives are shown here. A subset of the options
available in the config file may alternatively be set with environment variables. When both are
defined the environment variables take precedence over config file properties.

Configuration uses the following precedence strategy:

* ``specific env > coarse env > specific config > coarse config > default``

Environment Variables
---------------------

KERIA may be configured with environment variables as shown below. A complete list of tock-level
configuration options are shown in :ref:`scheduler-tock-config`.

.. code-block:: bash

    # Service Endpoint Location URLs creating Endpoint Role Authorizations and Location Scheme records on startup
    export KERIA_CURLS="https://url1,https://url2"
    # Introduction URLs resolved on startup (OOBIs)
    export KERIA_IURLS="https://url3,https://url4"
    # Data OOBI URLs resolved on startup
    export KERIA_DURLS="https://url5,https://url6"
    # how long before an agent can be idle before shutting down; defaults to 1 day
    export KERIA_RELEASER_TIMEOUT=86400

JSON Configuration File
-----------------------

The JSON configuration is the default configuration source and 100% of the configuration options for
KERIA are located in the config file.

.. Warning::
  When using JSON config with containers make sure to mount the JSON file to the directory specified in the
  ``--config-dir`` option and use the JSON file name specified by the ``--config-dir`` option to the
  ``keria start`` command as shown below.

.. Note::
    Using the absolute path variant for ``--config-file`` ignores the ``--config-dir`` argument.

.. code-block:: bash

    # Relative path version, interpreted relative to directory executing keria binary from.
    # This means the file "keria.json" must exist in the "scripts/keri/cf" folder
    keria start \
        --config-dir scripts \
        --config-file keria

    # Absolute path version
    keria start \
        --config-dir /path/to/config-dir/keria.json \
        --config-file /path/to/config-dir/keria.json

.. Warning::
  The JSON file must have an object with the same name that you sent to the ``keria start`` command via the ``--name`` argument.
  The default is ``"keria"`` which is why the JSON file below shows a sub-object named ``"keria"``.
  Make sure to include the ``"dt"`` date timestamp field or the configuration will not be loaded.

KERIA tocks in `tocks.signify`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configure KERIA Agent tocks in the JSON config file under ``tocks.signify``. KERIpy service settings
remain directly under ``tocks``. Values are HIO Doist scheduler intervals in seconds as a float value.

You can also configure the CURLs, IURLs, and DURLs of the agent.

* ``CURLs`` are **Service Endpoint Location** URLs creating Endpoint Role Authorizations and Location Scheme records on startup.
* ``IURLS`` are **Introduction** URLs resolved on startup (OOBIs).
* ``DURLS`` are **Data OOBI** URLs resolved on startup usually of things like ACDC credential schemas or ACDC credential CESR streams.


KERIA Configuration File Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Note that the following configuration file uses the name ``keria`` for the Agency as it has a
``"keria"`` top level section of the configuration JSON. This corresponds to using the ``keria``
value for ``keria start --name "keria"`` when starting KERIA.

The existing sample lists every KERIpy and KERIA component cadence explicitly.
Coarse aliases are omitted because they are shortcuts for these same settings.

.. literalinclude:: ../scripts/keri/cf/keria.json
   :language: json

.. _scheduler-tock-config:

Scheduler Tock Configuration (HIO Doist scheduler)
==================================================

Except for the release scan described below, KERIA defaults its registered
component cadences, including its KERIpy service settings, to ``0.03125`` seconds: one tick of its 32 Hz root scheduler. Explicit
``0.0`` remains supported and schedules work on the next cycle. File and
environment overrides retain their normal precedence; KERIpy's own defaults
outside KERIA are unchanged.

Delegation escrow processing uses ``tocks.anchorerEscrow`` throughout its
runtime, without a separate half-second delay. Witness resubmission's outbound
drain wait uses ``tocks.witnessReceiptorIdle`` and also defaults to one tick.

The Agent release scan, ``tocks.signify.releaser``, is the housekeeping
exception with a default of ``60.0`` seconds. It scans all open Agents for the default 24-hour inactivity
timeout. Allowing up to one minute of additional cleanup delay avoids a full
scan every tick without delaying active message processing. The release timeout
itself is separate from scheduler cadence and is not shortened.

.. list-table:: KERIA settings under tocks.signify
   :header-rows: 1

   * - File key
     - Environment override
   * - ``initer``
     - ``KERIA_INITER_TOCK``
   * - ``querier``
     - ``KERIA_QUERIER_TOCK``
   * - ``escrower``
     - ``KERIA_ESCROWER_TOCK``
   * - ``parser``
     - ``KERIA_PARSER_TOCK``
   * - ``witnesser``
     - ``KERIA_WITNESSER_TOCK``
   * - ``delegator``
     - ``KERIA_DELEGATOR_TOCK``
   * - ``exchangeSender``
     - ``KERIA_EXCHANGE_SENDER_TOCK``
   * - ``granter``
     - ``KERIA_GRANTER_TOCK``
   * - ``admitter``
     - ``KERIA_ADMITTER_TOCK``
   * - ``groupRequester``
     - ``KERIA_GROUP_REQUESTER_TOCK``
   * - ``seeker``
     - ``KERIA_SEEKER_TOCK``
   * - ``exchangecue``
     - ``KERIA_EXCHANGE_CUE_TOCK``
   * - ``submitter``
     - ``KERIA_SUBMITTER_TOCK``
   * - ``bootServer``
     - ``KERIA_BOOT_SERVER_TOCK``
   * - ``adminServer``
     - ``KERIA_ADMIN_SERVER_TOCK``
   * - ``httpServer``
     - ``KERIA_HTTP_SERVER_TOCK``
   * - ``shutdown``
     - ``KERIA_SHUTDOWN_TOCK``
   * - ``signalExpiry``
     - ``KERIA_SIGNAL_EXPIRY_TOCK``
   * - ``releaser``
     - ``KERIA_RELEASER_TOCK``

Parser waits and witness receipt/catch-up waits use their configured component
cadences. The Agent owns a ``SignalExpirer`` for its Signaler; ``signalExpiry`` controls
its scan cadence, not the ten-minute signal lifetime. Each scan uses a snapshot
and does not yield during iteration, so notification pushes between scheduler
cycles cannot invalidate a live deque iterator.

Agency/Agent containers follow the root scheduler cadence. Habery lifecycle
work and delegation containers inherit their owning container's cadence;
delegation's escrow loop retains its independent ``anchorerEscrow`` setting.
Transient grant workers, query workers, and delivery wrappers use their
parent's cadence. KERIpy's internal Poster, Clienter, and transport scheduling
is outside these KERIA settings. One-off CLI commands have no dedicated keys.

The server, shutdown, and release settings bind at Agency startup. Agent-owned
settings, including ``submitter`` and ``signalExpiry``, bind at creation or
reopen using that Agent's configuration lifecycle.


Configuration Precedence Strategy
---------------------------------

Resolution uses the same rule as KERIpy:

``specific env > coarse env > specific config > coarse config > default``

For example, ``KERIA_AGENT_TOCK=0.5`` overrides a file's
``tocks.signify.escrower=1.0``, while ``KERIA_ESCROWER_TOCK=0.25`` overrides
both. These KERIA environment variables do not alter KERIpy's independent
``KERI_*_TOCK`` settings. KERIA's Registrar and Credentialer are processed by
its central ``escrower``; KERIpy's separate registrar/credentialer escrow
settings do not schedule those KERIA objects.

All file values must be finite, nonnegative JSON numbers; booleans, strings,
nulls, unknown keys, and malformed blocks are errors. Environment values must
parse as finite, nonnegative numbers. Invalid supplied values are rejected even
when another setting would override them. Errors identify the invalid setting or configuration structure.

Coarse grained settings
-----------------------

The coarse grained ``tocks.signify.agent`` setting, or ``KERIA_AGENT_TOCK``, applies to
the original twelve Agent-work settings plus ``submitter``. It excludes
``bootServer``, ``adminServer``, ``httpServer``, ``shutdown``, ``signalExpiry``,
and ``releaser`` so a work-loop override does not alter server or housekeeping
cadences.

Backwards compatibility with legacy flat tocks
----------------------------------------------

The existing names remain supported directly under ``tocks`` for backward
compatibility. For example, ``{"tocks": {"escrower": 1.0}}`` is accepted but
logs one deprecation warning per configuration load. Move it to
``{"tocks": {"signify": {"escrower": 1.0}}}``. Identical old/new duplicates
are accepted; conflicting duplicates fail instead of silently choosing a value.
Legacy placement will remain available through a migration period; removal
will be announced in a future release.

The Agency resolves its configuration at load time and this is used as a template for any
Agent provisioned by that Agency. Newly provisioned Agents receive a copy of the configured tocks
from the Agency's JSON config file and do not persist environment overrides or defaults.

.. Warning::
  Existing Agents reopen their own persisted config files, including legacy files; those files are not automatically rewritten.
  Updating the Agency JSON config file does not change existing Agent JSON config files.
  Restart the Agency to load config changes for subsequently provisioned Agents.
  Edit an existing Agent's individual config and restart to apply changes; environment overrides provide
  process-wide tuning when services are reconstructed. There is no live reload.

These settings configure the existing Doer constructors.

keria.app.aiding
----------------

.. automodule:: keria.app.aiding
    :members:

keria.app.credentialing
-----------------------

.. automodule:: keria.app.credentialing
    :members:

keria.app.indirecting
---------------------

.. automodule:: keria.app.indirecting
    :members:

keria.app.notifying
-------------------

.. automodule:: keria.app.notifying
    :members:

keria.app.presenting
--------------------

.. automodule:: keria.app.presenting
    :members:

keria.app.specing
-----------------

.. automodule:: keria.app.specing
    :members: