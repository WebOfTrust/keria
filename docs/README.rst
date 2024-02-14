KERIA
=====

|GitHub Actions| |codecov|

KERI Agent in the cloud

Split from KERI Core

Development
-----------

Setup
~~~~~

-  Ensure `Python <https://www.python.org/downloads/>`__
   ``version 3.12.1+`` is installed
-  Install `Keripy
   dependency <https://github.com/WebOfTrust/keripy#dependencies>`__
   (``libsodium 1.0.18+``)

Build from source
^^^^^^^^^^^^^^^^^

-  Setup virtual environment: ``bash     python3 -m venv venv``
-  Activate virtual environment: ``bash     source venv/bin/activate``
-  Install dependencies: ``bash     pip install -r requirements.txt``
-  Run agent:
   ``bash     keria start --config-dir scripts --config-file demo-witness-oobis``

Build with docker
^^^^^^^^^^^^^^^^^

-  Build KERIA docker image: ``bash     make build-keria``

Running Tests
~~~~~~~~~~~~~

-  Install ``pytest``: ``bash       pip install pytest``

-  Run the test suites: ``bash       pytest tests/``

.. |GitHub Actions| image:: https://github.com/webOfTrust/keria/actions/workflows/python-app-ci.yml/badge.svg
   :target: https://github.com/WebOfTrust/keria/actions
.. |codecov| image:: https://codecov.io/gh/WebOfTrust/keria/branch/main/graph/badge.svg?token=FR5CB2TPYG
   :target: https://codecov.io/gh/WebOfTrust/keria
