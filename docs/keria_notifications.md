# KERIA Notifications

Simple end user interaction with a KERIA server agent through notifications.

Notifications allow good UX for event driven workflows in complicated, multi-step activities 
such as multi-signature identity management or credential issuance and presentation. 
SignifyTS and SignifyPy-based client applications may use the KERIA notifications API to draw
user attention to tasks for the user to complete in these workflows whether single or multi-step.

Notifications can be polled for and, in the future, will be sent via a server sent events (SSE)
stream.

## Overview

Notifications are durable in that they are stored in an Agent's database in the KERIA server. An
edge controller may read the notification database to list notifications, mark notifications as read,
or delete notifications.

### Modules Using Notifications

Modules leveraging notifications include:
- multisig identifier operations
  - creation
  - rotation
  - signing (interaction)
- identifier delegation, single sig or multisig
- credential issuance and presentation (IPEX), single sig or multisig
- challenge response and verification
- out-of-band identifier (OOBI) resolution

### Example notification

A notification payload looks like this:

```jsonc
{
    "i": "0AC-ghYFcCJBa045nPFTW1hh",
    "dt": "2026-06-26T21:12:11.266531+00:00",
    "r": false,
    "a": {
      "r": "/multisig/icp",
      "d": "EKm4OYRrUwo9nwik406n34ckWViDl6pLCeyGf75zpIyi"
    }
  }
```

This is a notification for a multisig inception event.

### Example Exchange Message for Notification

The operations in the modules listed above use KERI Exchange ("exn" / "EXN") messages to drive 
notifications in KERIA and are categorized by their route, the "r" field in an exchange message. 
When the exchange message processor, the Exchanger component from KERIpy, processes an exchange
message then it delegates message processing to an exchange message handler based on the route
field, the "r" attribute. This means the route is effectively a category field or secondary type
field for an exchange message.

Some exchange messages generate notifications and some do not.

### Route types

Here's the breakdown for each of the exn route types:

- `/multisig/*`: Multisig coordination exn messages. 
  - Handled by `Multiplexor` - creates a notification for receivers, not senders. 
  - Event types: 
    - icp: route `/multisig/icp` - multisig inception 
    - rot: route `/multisig/rot` - multisig key rotation
    - ixn: route `/multisig/ixn` - multisig interaction (signing)
    - vcp: route `/multisig/vcp` - multisig registry creation
    - iss: route `/multisig/iss` - multisig credential issuance
    - rev: route `/multisig/rev` - multisig credential revocation
    - exn: route `/multisig/exn` - multisig exchange message
    - rpy: route `/multisig/rpy` - multisig reply message (like location scheme, endpoint role authorization)
- `/ipex/*`: 
  - Handled by `IpexHandler` - creates a notification for each sender and receivers.
  - Event types: 
    - apply: route `/ipex/apply` - Request a credential disclosure  
    - offer: route `/ipex/offer` - Offer a specific credential disclosure by schema, either fully expanded, partially compact, or fully compact.
    - agree: route `/ipex/agree` - Agree to a specific credential disclosure
    - grant: route `/ipex/grant` - Grant the agreed upon credential disclosure
    - admit: route `/ipex/admit` - Admit the disclosed credential
    - spurn: route `/ipex/spurn` - Reject either an apply, offer, or agree event.
- `/challenge/response`: 
  - Handled by `ChallengeHandler` - does not create a notification, does not need one.
  - Sends add a signal to Signaler.
- `/delegate/request`: 
  - Handled by `DelegateRequestHandler` - creates a notification for the delegator only.
  - Only one event type, the delegation request.
- `/oobis`: 
  - Handled by `OobiRequestHandler`, though is not currently registered. No notification needed for OOBI resolution.

### Route attribute for exchange message routing

The "r" attribute of an exchange message corresponds to the same field in the notification
attribute "a" section, meaning the "notification.a.r" property is a route field. The route field of
a notification and its corresponding exchange message will match.

### Typical Exchange Message Example - `/multisig/icp`

A typical exchange message looks like the following `/multisig/icp` message containing similar
fields:

```jsonc
{
  "v": "KERI10JSON0003af_",                              // version
  "t":      "exn",                                       // type - always exn for Exchange message
  "d":  "EL0z30RTfX7Hj6V7tbcwQsbadXzykG5YBLsWYzZOiZEt",  // digest (SAID) of message
  "i":  "EA93JVUXysuNV4ZgjnHrrgG0FGVU8717IoG6oWg_J3fW",  // sender (AID identifier of sender)
  "rp": "",                                              // recipient AID of receiver - (optional)
  "p":  "",                                              // previous event SAID - (optional)
  "dt": "2026-06-26T21:40:36.189723+00:00",              // ISO 8061 date & timestamp string
  "r": "/multisig/icp",                                  // route 
  "q": {},                                               // modifiers - (optional) like query string of URI 
  "a": {                                                 // attributes - message payload 
    "gid": "EMstJkrXzZ9TEfWRX3tzKZy-wVPyvSwa22TREIeJLo5g",
    "smids": ["..."],
    "rmids": ["..."]
  },               
  "e": {                                                 // embeds - (optional) embedded data
    "icp": { "v": "KERI10JSON000189_", "t": "icp", "...": "..." },
    "d": "ENT1TlQmyHygC487HUex-88hoTUM9ORggV-tUsYT1Xw5"
  } 
}
```

## Multisig Identifier Operations

Each multisig operation, like those listed in [route types](#route-types), require participation by
a threshold satisfying number of multisig group members. An exchange message for the given route type
is sent to each multisig group member and creates a notification for each multisig message recipient.

The author, or initiator, of a multisig event does not get a notification because the KERIpy 
Multiplexor implementation suppresses self-notification, which makes sense because the initiator
is assumed to know about the event it submits, thus a self-notification is not needed.


## Delegated Identifier Inception or Rotation Request Approval Notifications

Both inception and rotation must be approved by the delegator when a delegate wants to either 
set up a new identifier, inception, or rotate keys on an existing identifier. this means each
inception or rotation event must trigger a notification for the delegator to see the approval
request. The approval request is sent from the delegate as an exchange message to the delegator.
The delegator's KERIA agent then sees that exchange message and generates a notification from it.

In Signify this is exposed as `delegations().approve(...)`, which posts to 
`/identifiers/{name}/delegation`.

#### Inception or Rotation Approval Request EXN

KERIA sends a peer-to-peer EXN on route `/delegate/request` containing the delegator AID and embeds
the delegated event as `e.evt`. On receipt, KERIA converts the verified EXN into a notification with
these attributes:

```json
{
  "src": "verified EXN sender AID",
  "r": "/delegate/request",
  "delpre": "local delegator qb64 AID",
  "ked": "embedded delegated event",
  "aids": ["optional multisig participant AIDs"]
}
```

Wallets can derive the seal to review and approve from the embedded event:

```json
{
  "i": "delegate event prefix",
  "s": "delegate event sequence number",
  "d": "delegate event SAID"
}
```

Wallets should derive the seal from the event instead of hard-coding the inception case.

##### Inception
For delegated inception, `s` is `"0"` and `d` is always the delegate prefix.

##### Rotation
For delegated rotation, `s` is the rotation sequence number and `d` is always the rotation event
SAID. 

### KERA Agent Signs Delegation Requests - delegation communication proxy

The `/delegate/request` exchange message is used as a signed request for delegation approval of 
either inception or rotation. KERI uses signed requests for everything, which means a delegation
request must be signed. This implies that a pre-existing AID, whose KEL is known by the delegator,
signs the delegated inception (`dip`) event because a delegatee cannot sign its own delegated 
inception event since the `dip` is not valid until the delegator approves it.

A delegation communication proxy is used as this pre-existing AID. In KERIA the Agent Hab AID that
the edge Signify client delegates to is used as this delegation communication proxy. This allows the
 `/delegate/request` EXN message to be signed by a valid KERI AID, the sender's Agent habitat (Hab)
AID, selected by KERIA's delegation `Anchorer`.

#### Single Sig Delegates

For a Signify managed single-sig AID, that sender is the delegatee's Agent AID, which 
acts as a delegation communication proxy because edge Signify identities rely on their KERIA Agent
to sign delegation requests. 

#### Multi Sig Delegates

For a group delegated AID, the sender is 
the Agent Hab for the local single sig member of the group AID. This Agent Hab for the single sig
member acts as the delegation communication proxy.

### Delegator must know delegation communication proxy

The delegator must already know (have OOBI resolved) the EXN sender's KEL before its Exchanger can
validate the request and create a notification. This means the delegator must have OOBI resolved 
the Agent OOBI for the Signify AID. If the sender is unknown, the inbound EXN will not produce a
`/delegate/request` notification and will stay in escrow until it expires even though the
raw delegated event may still be sent
separately.
