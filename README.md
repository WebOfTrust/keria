# TypeScript implementation of Signify

Project Name: signify-ts

[![TypeScript](https://badges.frapsoft.com/typescript/code/typescript.png?v=101)](https://github.com/ellerbrock/typescript-badges/)

## Signify - KERI Signing at the Edge

Of the five functions in a KERI agent, 

1. Key generation
2. Encrypted key storage
3. Event generation
4. Event signing
5. Event Validation

Signify-TS splits off two, key generation and event signing into a TypeScript library to provide "signing at the edge".
It accomplishes this by using libsodium to generate ed25510 key pairs for signing and x25519 key pairs for encrypting the
private keys, next public keys and salts used to generate the private keys.  The encrypted private key and salts are then stored on a
remote cloud agent the never has access to the decryption keys.  New key pair sets (current and next) will be generated 
for inception and rotation events with only the public keys and blake3 hash of next keys made available to the agent.

The communication protocol between a Signify client and KERI agent will encode all cryptographic primitives as CESR base64
encoded strings for the initial implementation.  Support for binary CESR can be added in the future.


### Environment Setup

The code is built using Typescript and running code locally requires a Mac or Linux OS.

-   Install [Node.js](https://nodejs.org)    


-   Install dependencies:
    ```bash
    npm install
    ```


Account Creation Workflow


sequenceDiagram
    actor u as User
    participant s as Signify
    participant c as Cloud Agent
    u ->> s: Create Account
    s ->> s: Generate Pub/Pri Keys
    s ->>+ c: Request ICP Event Creation with Keys
    note over s,c: This call can not be secured
    note right of c: Creates ICP Event
    c ->>- s: Return ICP event
    s ->>+ c: Create Account with Signed ICP Event
    note over s,c: Call Signed by new Keys
    note right of c: Parses and Saves ICP
    note right of c: Create Account with new AID
    c ->>- s: Return New Account KeyState
    s ->>+ c: Save Key Information
    c ->>- s: Key Information Saved
    s ->> u: Return New Account Information


sequenceDiagram
    actor u as User
    participant a as Web Page App
    participant s as Signify
    participant c as Cloud Agent
    u ->> a: Create Account
    a ->>+ s: Generate Pub/Pri Keys
    s ->>- a: Return new Pub/Pri Keypair
    a ->>+ c: Request ICP Event Creation with Keys
    note over s,c: This call can not be secured
    note right of c: Creates ICP Event
    c ->>- a: Return ICP event
    a ->>+ s: Sign ICP Event
    s ->>- a: Return Signed Event
    a ->>+ c: Create Account with Signed ICP Event
    note over s,c: Call Signed by new Keys
    note right of c: Parses and Saves ICP
    note right of c: Create Account with new AID
    c ->>- a: Return New Account KeyState
    a ->>+ s: Save Key Information
    s ->>+ c: Save Key Information
    c ->>- s: Key Information Saved
    a ->> u: Return New Account Information