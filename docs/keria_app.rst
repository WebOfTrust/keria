KERIA App API
=============

keria.app.agenting
------------------

.. automodule:: keria.app.agenting
    :members:

Agency and Agent Configuration
===================

A KERIA Agency can be configured with either environment variables or a configuration file.
The configuration file is a JSON file. Both alternatives are shown here.

Environment Variables
---------------------

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

To use the JSON configuration file option make sure to mount the JSON file to the directory you specify with the
`--config-dir` option and name the JSON file the name specified by the `--config-dir` option to the `keria start` command like so.

With the absolute path version the `--config-dir` argument does not have an affect since the
`--config-file` argument specifies the absolute path to the JSON file.

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

The JSON file must have an object with the same name that you sent to the `keria start` command via the `--name` argument.
The default is "keria" which is why the JSON file below shows a sub-object named "keria".
Make sure to include the "dt" date timestamp field or the configuration will not be loaded.

Configure KERIA Agent tocks under ``tocks.signify``. KERIpy service settings
remain directly under ``tocks``. Values are scheduler intervals in seconds.

You can also configure the CURLs, IURLs, and DURLs of the agent.
CURLs are Service Endpoint Location URLs creating Endpoint Role Authorizations and Location Scheme records on startup.
IURLS are Introduction URLs resolved on startup (OOBIs).
DURLS are Data OOBI URLs resolved on startup usually of things like ACDC credential schemas or ACDC credential CESR streams.

.. code-block:: json

    {
      "dt": "2025-01-13T16:08:30.123456+00:00",
      "keria": {
        "dt": "2025-01-13T16:08:30.123457+00:00",
        "curls": ["http://127.0.0.1:3902/"]
      },
      "iurls": [
        "http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller?name=Wan&tag=witness",
        "http://127.0.0.1:5643/oobi/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM/controller?name=Wil&tag=witness",
        "http://127.0.0.1:5644/oobi/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX/controller?name=Wes&tag=witness"
      ],
      "tocks": {
        "signify": {
          "initer": 0.0,
          "escrower": 1.0
        }
      }
    }

Scheduler configuration
~~~~~~~~~~~~~~~~~~~~~~~

Each of the following settings has a code default of ``0.0``. The shipped
examples retain their explicit ``escrower: 1.0`` value. A zero interval means
eligible on the next scheduler cycle, not an independently running busy loop.

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

The coarse ``tocks.signify.agent`` setting, or ``KERIA_AGENT_TOCK``, applies to
all twelve settings. Resolution uses the same rule as KERIpy:

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
when another setting would override them. Errors identify the configuration
file and affected namespace.

The existing names remain supported directly under ``tocks`` for backward
compatibility. For example, ``{"tocks": {"escrower": 1.0}}`` is accepted but
logs one deprecation warning per configuration load. Move it to
``{"tocks": {"signify": {"escrower": 1.0}}}``. Identical old/new duplicates
are accepted; conflicting duplicates fail instead of silently choosing a value.
Legacy placement will remain available through a migration period; removal
will be announced in a future release.

The Agency resolves its template at construction. Newly provisioned Agents
receive a canonical copy of the configured tocks, without persisting environment
overrides or defaults. Existing Agents reopen their own persisted config files,
including legacy files; those files are not automatically rewritten. Restart
the Agency to load template changes for subsequently provisioned Agents.
Updating the Agency template does not change existing Agents. Edit an existing
Agent's config and restart to apply file changes; environment overrides provide
process-wide tuning when services are reconstructed. There is no live reload.

These settings configure the existing doer constructors. Parser yields and
nested witness operations do not yet consistently retain the owning doer's
cadence; scheduling fixes and coverage of additional services follow separately.

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