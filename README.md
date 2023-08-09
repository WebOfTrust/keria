# KERIA
[![GitHub Actions](https://github.com/webOfTrust/keria/actions/workflows/python-app-ci.yml/badge.svg)](https://github.com/WebOfTrust/keria/actions)
[![codecov](https://codecov.io/gh/WebOfTrust/keria/branch/main/graph/badge.svg?token=FR5CB2TPYG)](https://codecov.io/gh/WebOfTrust/keria)
[![Documentation Status](https://readthedocs.org/projects/keria/badge/?version=latest)](https://keria.readthedocs.io/en/latest/?badge=latest)

KERI Agent in the cloud

Split from KERI Core


## Development

### Setup

* Ensure [Python](https://www.python.org/downloads/) `version 3.10.4+` is installed
* Install [Keripy dependency](https://github.com/WebOfTrust/keripy#dependencies) (`libsodium 1.0.18+`)


#### Build from source

* Setup virtual environment:
    ```bash
    python3 -m venv venv
    ```
* Activate virtual environment:
    ```bash
    source venv/bin/activate
    ```
* Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
* Run agent:
    ```bash
    keria start --config-dir scripts --config-file demo-witness-oobis
    ```

#### Build with docker

* Build KERIA docker image:
    ```bash
    make build-keria
    ```


### Running Tests

* Install `pytest`:
    ```bash
      pip install pytest
    ```

* Run the test suites:
    ```bash
      pytest tests/
    ```

