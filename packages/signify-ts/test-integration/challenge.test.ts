import { assert, test } from 'vitest';
import { Serder } from 'signify-ts';
import {
    assertOperations,
    getOrCreateClients,
    resolveOobi,
    waitOperation,
} from './utils/test-util.ts';

test('challenge', async () => {
    const [client1, client2] = await getOrCreateClients(2);

    // Generate challenge words
    const challenge1_small = await client1.challenges().generate(128);
    assert.equal(challenge1_small.words.length, 12);
    const challenge1_big = await client1.challenges().generate(256);
    assert.equal(challenge1_big.words.length, 24);

    // Create two identifiers, one for each client
    const icpResult1 = await client1.identifiers().create('alice', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    const { response: aid1 } = await waitOperation(
        client1,
        await icpResult1.op()
    );
    const rpyResult1 = await client1
        .identifiers()
        .addEndRole('alice', 'agent', client1!.agent!.pre);
    await waitOperation(client1, await rpyResult1.op());
    console.log("Alice's AID:", aid1.i);

    const icpResult2 = await client2.identifiers().create('bob', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    const { response: aid2 } = await waitOperation(
        client2,
        await icpResult2.op()
    );
    const rpyResult2 = await client2
        .identifiers()
        .addEndRole('bob', 'agent', client2!.agent!.pre);
    await waitOperation(client2, await rpyResult2.op());

    // Exchenge OOBIs
    const oobi1 = await client1.oobis().get('alice', 'agent');
    const oobi2 = await client2.oobis().get('bob', 'agent');

    await resolveOobi(client1, oobi2.oobis[0], 'bob');
    console.log("Client 1 resolved Bob's OOBI");
    await resolveOobi(client2, oobi1.oobis[0], 'alice');
    console.log("Client 2 resolved Alice's OOBI");

    // List Client 1 contacts
    let contacts1 = await client1.contacts().list();
    let bobContact = contacts1.find((contact) => contact.alias === 'bob');
    assert.equal(bobContact?.alias, 'bob');
    assert(Array.isArray(bobContact?.challenges));
    assert.strictEqual(bobContact.challenges.length, 0);

    // Bob responds to Alice challenge
    await client2.challenges().respond('bob', aid1.i, challenge1_small.words);
    console.log('Bob responded to Alice challenge with signed words');

    // Alice verifies Bob's response
    const verifyOperation = await waitOperation(
        client1,
        await client1.challenges().verify(aid2.i, challenge1_small.words)
    );
    console.log('Alice verified challenge response');

    //Alice mark response as accepted
    const verifyResponse = verifyOperation.response as {
        exn: Record<string, unknown>;
    };
    const exn = new Serder(verifyResponse.exn);

    await client1.challenges().responded(aid2.i, exn.sad.d);
    console.log('Alice marked challenge response as accepted');

    // Check Bob's challenge in conctats
    contacts1 = await client1.contacts().list();
    bobContact = contacts1.find((contact) => contact.alias === 'bob');

    assert(Array.isArray(bobContact?.challenges));
    assert.strictEqual(bobContact?.challenges[0].authenticated, true);

    await assertOperations(client1, client2);
}, 30000);
