# KERIA Notifications

Simple end user interaction with a KERIA server agent through notifications.

Event driven workflows often simplify user experiences especially in complicated, multi-step
workflows. SignifyTS and SignifyPy based client applications may use KERIA notifications to draw
user attention to tasks for the user to complete in these workflows whether single or multi-step.

Notifications can be polled for and, in the future, will be sent via a server sent events (SSE)
stream.

## Overview
Modules leveraging notifications include:
- delegation
- multisig identifier creation
- multisig signing
- credential issuance and presentation, single or multisig
- challenge response and verification
- identifier creation

### Delegated Identifier Inception or Rotation Request Approval Notifications

Both inception and rotation must be approved by the delegator when a delegate wants to either 
set up a new identifier, inception, or rotate keys on an existing identifier. The following steps 
demonstrate when an approval is needed.

1. **Delegate** creates delegated inception (`dip`) or delegated rotation (`drt`) event.
2. **Delegate** sends a delegation approval request exchange message (`exn`) to the delegator.
3. **Delegator** agent receives notification and surfaces it to the user.
4. **Delegator** manually approves the event by anchoring the delegate event seal in a delegator 
   interaction event. 

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

Wallets should derive the seal from the event instead of
hard-coding the inception case.

##### Inception
For delegated inception, `s` is `"0"` and `d` is usually the delegate prefix.

##### Rotation
For delegated rotation, `s` is the rotation sequence number and `d` is the
rotation event SAID. 

### Sender Verification Precondition

The `/delegate/request` EXN is signed by the sender's habitat selected by KERIA's delegation
`Anchorer`. For a Signify managed single-sig AID, that sender is normally the delegatee agent/proxy
AID, because Signify habitats do not sign inside KERIA. For a group delegated AID, the sender is 
the local member habitat.

The delegator must already know (have OOBI resolved) the EXN sender's KEL before its exchanger can
validate the request and create a notification. If the sender is unknown, the inbound EXN will not
produce a `/delegate/request` notification, even though the raw delegated event may still be sent
separately.

We should add at the very least an error message in the logs when receiving an approval request from
an unknown sender, though ideally that would be surfaced to the user in some visible way. Right now
this is a future TODO.