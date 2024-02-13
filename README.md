# KERIA
[![GitHub Actions](https://github.com/webOfTrust/keria/actions/workflows/python-app-ci.yml/badge.svg)](https://github.com/WebOfTrust/keria/actions)
[![codecov](https://codecov.io/gh/WebOfTrust/keria/branch/main/graph/badge.svg?token=FR5CB2TPYG)](https://codecov.io/gh/WebOfTrust/keria)
[![Documentation Status](https://readthedocs.org/projects/keria/badge/?version=latest)](https://keria.readthedocs.io/en/latest/?badge=latest)

KERI Agent in the cloud

Split from KERI Core

## KERIA Service Architecture
Here we detail the components of a single KERIA instance. This architecture protects the host and the holder private keys. All client tasks/calls are signed 'at the edge', not in the hosted KERIA instance. Therefore, KERIA relies on the Signify protocol for all calls. The Architecture provides three endpoints for Signify clients to create their KERIA agents. The Agency (boot) endpoint establishes an agent. The API Handler and Message Router endpoints would be exposed to the internet for creating identifiers, receiving credentials, etc.
![KERIA](https://github.com/WebOfTrust/keria/assets/681493/a64212ef-e343-428d-954f-1aa81222ae63)

### Message Router
The Message Router receives external KERI protocol messages. These are KERI protocol messages for instance coordinating multi-sig, revoking credentials, etc. It routes these messages to the appropriate Agent(s). For instance a multisig message requires asynchronous waiting (for signature responses from other participants) and the message router would route those incoming KERI protocol responses to the appropriate agents.
From Signify client calls, this service endpoint corresponds to the *http port* (default is 3902).
This enpoint allows all KERI clients (not just Signify) to interact in a seamless way.

### The Agency
The Agency receives API requests (/boot requests) to provision agents. It is the central repository for initializing agents. 
The Agency database persists all of the information to track the existing agents, allowing recovery on restart.
From Signify clients calls, this service endpoint corresponds to the *boot port* (default is 3903).
A common entry in the agency is the mapping between a managed AID and the agency that handles that managed AID.

### API Handler
The API Handler receives agent API requests (/agent requests) including for Signify clients to create identifiers, receiving credentials, etc. All API calls are signed by the Signify client headers so that all calls are secure. 
This API interacts with agents and those interactions are stored in the agent databases.
From Signify clients calls, this service endpoint corresponds to the *admin port* (default is 3901).

### Agents
Agents act on behalf of their Signify clients. They don't have the secrets of the client. Instead, they handle all actions for the clients, other than secret/encryption/signing. However, Agents do have their own keys and do sign all of their messages BACK to the Signify client, so the client can verify that all messages received are from their agent.
Agents use KERI HIO to handle all of the different asynchronous actions that are occuring. HIO is an efficient and scalable orchestration/processing mechanism that leverages queues, handlers, coroutines, etc.
All Agent db access is through the associated Agent.

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

