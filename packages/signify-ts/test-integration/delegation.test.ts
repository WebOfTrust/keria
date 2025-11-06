import { assert, test } from 'vitest';
import {
    assertOperations,
    getOrCreateClients,
    getOrCreateContact,
    resolveOobi,
    waitOperation,
} from './utils/test-util.ts';
import { retry } from './utils/retry.ts';
import { step } from './utils/test-step.ts';

test('delegation', async () => {
    const [client1, client2] = await getOrCreateClients(2);

    // Client 1 create delegator AID
    const icpResult1 = await client1.identifiers().create('delegator', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    await waitOperation(client1, await icpResult1.op());
    const ator = await client1.identifiers().get('delegator');
    const rpyResult1 = await client1
        .identifiers()
        .addEndRole('delegator', 'agent', client1!.agent!.pre);
    await waitOperation(client1, await rpyResult1.op());
    console.log("Delegator's AID:", ator.prefix);

    // Client 2 resolves delegator OOBI
    console.log('Client 2 resolving delegator OOBI');
    const oobi1 = await client1.oobis().get('delegator', 'agent');
    await resolveOobi(client2, oobi1.oobis[0], 'delegator');
    console.log('OOBI resolved');

    // Client 2 creates delegate AID
    const icpResult2 = await client2
        .identifiers()
        .create('delegate', { delpre: ator.prefix });
    const op2 = await icpResult2.op();
    const delegatePrefix = op2.name.split('.')[1];
    console.log("Delegate's prefix:", delegatePrefix);
    console.log('Delegate waiting for approval...');

    // Client 1 approves delegation
    const anchor = {
        i: delegatePrefix,
        s: '0',
        d: delegatePrefix,
    };

    await step('delegator approves delegation', async () => {
        const result = await retry(async () => {
            const apprDelRes = await client1
                .delegations()
                .approve('delegator', anchor);
            await waitOperation(client1, await apprDelRes.op());
            console.log('Delegator approve delegation submitted');
            return apprDelRes;
        });
        assert.equal(
            JSON.stringify(result.serder.sad.a[0]),
            JSON.stringify(anchor)
        );
    });

    const op3 = await client2.keyStates().query(ator.prefix, '1');
    await waitOperation(client2, op3);

    // Client 2 check approval
    await waitOperation(client2, op2);
    const aid2 = await client2.identifiers().get('delegate');
    assert.equal(aid2.prefix, delegatePrefix);
    console.log('Delegation approved for aid:', aid2.prefix);

    await assertOperations(client1, client2);
    const rpyResult2 = await client2
        .identifiers()
        .addEndRole('delegate', 'agent', client2!.agent!.pre);
    await waitOperation(client2, await rpyResult2.op());
    const oobis = await client2.oobis().get('delegate');

    const contactId = await getOrCreateContact(
        client1,
        'delegate',
        oobis.oobis[0].split('/agent/')[0]
    );

    assert.equal(contactId, aid2.prefix);
}, 600000);
