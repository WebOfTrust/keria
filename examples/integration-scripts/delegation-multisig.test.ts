import { strict as assert } from 'assert';
import signify from 'signify-ts';
import {
    assertNotifications,
    assertOperations,
    markAndRemoveNotification,
    resolveOobi,
    waitForNotifications,
    waitOperation,
    warnNotifications,
} from './utils/test-util';
import { getOrCreateClient, getOrCreateIdentifier } from './utils/test-setup';
import {
    acceptMultisigIncept,
    startMultisigIncept,
} from './utils/multisig-utils';

test('delegation-multisig', async () => {
    await signify.ready();
    // Boot three clients
    const [client0, client1, client2] = await Promise.all([
        getOrCreateClient(),
        getOrCreateClient(),
        getOrCreateClient(),
    ]);

    // Create four identifiers, one for each client
    const [aid0, aid1, aid2] = await Promise.all([
        createAID(client0, 'delegator'),
        createAID(client1, 'member1'),
        createAID(client2, 'member2'),
    ]);

    // Exchange OOBIs
    console.log('Resolving OOBIs');
    const oobi0 = await client0.oobis().get('delegator', 'agent');
    const oobi1 = await client1.oobis().get('member1', 'agent');
    const oobi2 = await client2.oobis().get('member2', 'agent');

    await Promise.all([
        resolveOobi(client1, oobi0.oobis[0], 'delegator'),
        resolveOobi(client1, oobi2.oobis[0], 'member2'),
        resolveOobi(client2, oobi0.oobis[0], 'delegator'),
        resolveOobi(client2, oobi1.oobis[0], 'member1'),
    ]);

    console.log('Member1 and Member2 resolved 2 OOBIs');

    // First member start the creation of a multisig identifier
    const op1 = await startMultisigIncept(client1, {
        groupName: 'multisig',
        localMemberName: aid1.name,
        participants: [aid1.prefix, aid2.prefix],
        isith: 2,
        nsith: 2,
        toad: 2,
        delpre: aid0.prefix,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    console.log('Member1 initiated multisig, waiting for others to join...');

    // Second member check notifications and join the multisig
    const [notification] = await waitForNotifications(client2, '/multisig/icp');
    await markAndRemoveNotification(client2, notification);
    assert(notification.a.d);
    const op2 = await acceptMultisigIncept(client2, {
        localMemberName: aid2.name,
        groupName: 'multisig',
        msgSaid: notification.a.d,
    });

    console.log('Member2 joined multisig, waiting for delegator...');

    const delegatePrefix = op1.name.split('.')[1];
    assert.equal(op2.name.split('.')[1], delegatePrefix);
    console.log("Delegate's prefix:", delegatePrefix);
    console.log('Delegate waiting for approval...');

    // Client 0 approves delegation
    const anchor = {
        i: delegatePrefix,
        s: '0',
        d: delegatePrefix,
    };
    const ixnResult = await client0.identifiers().interact('delegator', anchor);
    await waitOperation(client0, await ixnResult.op());
    console.log('Delegator approved delegation');

    const op3 = await client1.keyStates().query(aid0.prefix, '1');
    const op4 = await client2.keyStates().query(aid0.prefix, '1');

    // Check for completion
    await Promise.all([
        waitOperation(client1, op1),
        waitOperation(client2, op2),
        waitOperation(client1, op3),
        waitOperation(client2, op4),
    ]);
    console.log('Delegated multisig created!');

    const aid_delegate = await client1.identifiers().get('multisig');
    assert.equal(aid_delegate.prefix, delegatePrefix);

    await assertOperations(client0, client1, client2);
    await assertNotifications(client0, client1, client2);
}, 30000);

async function createAID(client: signify.SignifyClient, name: string) {
    await getOrCreateIdentifier(client, name);
    const aid = await client.identifiers().get(name);
    console.log(name, 'AID:', aid.prefix);
    return aid;
}
