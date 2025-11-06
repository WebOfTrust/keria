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

- Install [Node.js](https://nodejs.org)

- Install dependencies:
    ```bash
    npm install
    ```

Typescript source files needs to be transpiled before running scripts or integration tests

- Generate types:

    To generate TypeScript types from KERIA OpenAPI docs dynamically

    ```
    npm run generate:types
    ```

    We can specify KERIA spec url by this command:

    ```
    SPEC_URL=http://localhost:3902/spec.yaml npm run generate:types
    ```

- Build:

    ```bash
    npm run build
    ```

- ready() must be called before library is useable. Example minimum viable client code.

    ```javascript
    import { randomPasscode, ready, SignifyClient, Tier } from 'signify-ts';

    await ready();

    const bran = randomPasscode();
    const url = 'http://127.0.0.1:3901';
    const boot_url = 'http://127.0.0.1:3903';
    const actualSignifyClient = new SignifyClient(
        url,
        bran,
        Tier.low,
        boot_url
    );

    console.log(actualSignifyClient);
    ```

### Unit testing

To run unit tests

```bash
npm test
```

### Integration testing

The integration tests depends on a local instance of KERIA, vLEI-Server and Witness Demo. These are specified in the [Docker Compose](./docker-compose.yaml) file. To start the dependencies, use docker compose:

```bash
docker compose up --wait
```

If successful, it should print something like this:

```bash
$ docker compose up --wait
[+] Running 4/4
 ✔ Network signify-ts_default           Created                                           0.0s
 ✔ Container signify-ts-vlei-server-1   Healthy                                           5.7s
 ✔ Container signify-ts-keria-1         Healthy                                           6.2s
 ✔ Container signify-ts-witness-demo-1  Healthy                                           6.2s
```

It is possible to change the keria image by using environment variables. For example, to use weboftrust/keria:0.1.3, do:

```bash
export KERIA_IMAGE_TAG=0.1.3
docker compose pull
docker compose up --wait
```

To use another repository, you can do:

```bash
export KERIA_IMAGE=gleif/keria
docker compose pull
docker compose up --wait
```

Use the npm script "test:integration" to run all integration tests in sequence:

```bash
npm run test:integration
```

To execute a specific integration test, you can use:

```bash
npm run test:integration -- test-integration/credentials.test.ts
```

It is also possible to run the tests using local instances of vLEI, Keria, and witness network. Set the environment variable `TEST_ENVIRONMENT` to `local`, e.g:

```
TEST_ENVIRONMENT=local npm run test:integration test-integration/credentials.test.ts
```

This changes the discovery urls to use `localhost` instead of the hostnames inside the docker network.

# Diagrams

Account Creation Workflow

![Account Creation](/diagrams/account-creation-workflow.png)

![Account Creation Webpage](/diagrams/account-creation-webpage-workflow.png)

# Publishing

This package is published on npm: https://www.npmjs.com/package/signify-ts.

If you need to publish a version under your own scope, you can use the [publish script](./publish.sh). This enables you to create development packages. For example:

```bash
NPM_PACKAGE_SCOPE=@myorg DRY_RUN=1 ./publish.sh
npm notice Tarball Details
npm notice name: @myorg/signify-ts
npm notice version: 0.3.0-rc1-dev.8fa9919
npm notice filename: myorg-signify-ts-0.3.0-rc1-dev.8fa9919.tgz
npm notice package size: 81.0 kB
npm notice unpacked size: 370.0 kB
npm notice shasum: 8c160bc99d9ec552e6c478c20922cae3388a8ace
npm notice integrity: sha512-WRuD5PKFN3WBl[...]xVieCIS0UpVeg==
npm notice total files: 96
npm notice
npm notice Publishing to https://registry.npmjs.org/ with tag dev and default access (dry-run)
+ @myorg/signify-ts@0.3.0-rc1-dev.8fa9919
```

Set the `NPM_PUBLISH_TAG` to `latest` to skip the commit hash suffix in the version:

```bash
NPM_PUBLISH_TAG=latest NPM_PACKAGE_SCOPE=@myorg DRY_RUN=1 ./publish.sh
npm notice Tarball Details
npm notice name: @myorg/signify-ts
npm notice version: 0.3.0-rc1
npm notice filename: myorg-signify-ts-0.3.0-rc1.tgz
npm notice package size: 80.9 kB
npm notice unpacked size: 370.0 kB
npm notice shasum: 8c9e4edcf19802e8acaf5996a36061a9c335b1c4
npm notice integrity: sha512-V1y2W3zs4Ccsn[...]vKY3WWgalcuBQ==
npm notice total files: 96
npm notice
npm notice Publishing to https://registry.npmjs.org/ with tag latest and default access (dry-run)
+ @myorg/signify-ts@0.3.0-rc1
```
