# TypeScript implementation of Signify

Project Name: signify-ts

[![TypeScript](https://badges.frapsoft.com/typescript/code/typescript.png?v=101)](https://github.com/ellerbrock/typescript-badges/)
[![Tests](https://github.com/WebOfTrust/signify-ts/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/WebOfTrust/signify-ts/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/WebOfTrust/signify-ts/branch/main/graph/badge.svg?token=K3GK7MCYVW)](https://codecov.io/gh/WebOfTrust/signify-ts)
[![Documentation](https://img.shields.io/badge/documentation-grey?)](https://weboftrust.github.io/signify-ts/)

## Signify - KERI Signing at the Edge

Of the five functions in a KERI agent,

1. Key generation
2. Encrypted key storage
3. Event generation
4. Event signing
5. Event Validation

Signify-TS splits off two, key generation and event signing into a TypeScript library to provide "signing at the edge".
It accomplishes this by using [libsodium](https://doc.libsodium.org/) to generate ed25519 key pairs for signing and x25519 key pairs for encrypting the
private keys, next public keys and salts used to generate the private keys. The encrypted private key and salts are then stored on a
remote cloud agent that never has access to the decryption keys. New key pair sets (current and next) will be generated
for inception and rotation events with only the public keys and blake3 hash of the next keys made available to the agent.

The communication protocol between a Signify client and [KERI](https://github.com/WebOfTrust/keri) agent will encode all cryptographic primitives as CESR base64
encoded strings for the initial implementation. Support for binary CESR can be added in the future.

### Environment Setup

The code is built using Typescript and running code locally requires a Mac or Linux OS.

-   Install [Node.js](https://nodejs.org)

-   Install dependencies:
    ```bash
    npm install
    ```

Typescript source files needs to be transpiled before running scripts or integration tests

-   Build:
    ```bash
    npm run build
    ```

### Unit testing

To run unit tests

```bash
npm test
```

### Integration testing

The integration tests depends on a local instance of KERIA, vLEI-Server and Witness Demo. These are specified in the [Docker Compose](./docker-compose.yaml) file. To start the dependencies, use docker compose:

```bash
docker compose up deps
```

If successful, it should print someting like this:

```bash
$ docker compose up deps
[+] Running 5/4
 ✔ Network signify-ts_default           Created                                           0.0s
 ✔ Container signify-ts-vlei-server-1   Created                                           0.1s
 ✔ Container signify-ts-keria-1         Created                                           0.1s
 ✔ Container signify-ts-witness-demo-1  Created                                           0.1s
 ✔ Container signify-ts-deps-1          Created                                           0.0s
Attaching to signify-ts-deps-1
signify-ts-deps-1  | Dependencies running
signify-ts-deps-1 exited with code 0
```

It is possible to change the keria image by using environment variables. For example, to use weboftrust/keria:0.1.3, do:

```bash
export KERIA_IMAGE_TAG=0.1.3
docker compose pull
docker compose up deps
```

To use another repository, you can do:

```bash
export KERIA_IMAGE=gleif/keria
docker compose pull
docker compose up deps
```

**Important!** The integration tests runs on the build output in `dist/` directory. Make sure to run build before running the integration tests.

```bash
npm run build
```

Use the npm script "test:integration" to run all integration tests in sequence:

```bash
npm run test:integration
```

Or, use execute `jest` directly to run a specific integration test, for example:

```bash
npx jest examples/integration-scripts/credentials.test.ts
```

It is also possible to run the tests using local instances of vLEI, Keria, and witness network. Set the environment variable `TEST_ENVIRONMENT` to `local`, e.g:

```
TEST_ENVIRONMENT=local npx jest examples/integration-scripts/credentials.test.ts
```

This changes the discovery urls to use `localhost` instead of the hostnames inside the docker network.

# Diagrams

Account Creation Workflow

![Account Creation](/diagrams/account-creation-workflow.png)

![Account Creation Webpage](/diagrams/account-creation-webpage-workflow.png)
