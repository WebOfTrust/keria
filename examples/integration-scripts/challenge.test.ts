import { strict as assert } from 'assert';
import signify, { Serder } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';
import { resolveOobi, waitOperation } from './utils/test-util';

const { url, bootUrl } = resolveEnvironment();

test('challenge', async () => {
    await signify.ready();
    const bran1 = signify.randomPasscode();
    const bran2 = signify.randomPasscode();
    const client1 = new signify.SignifyClient(
        url,
        bran1,
        signify.Tier.low,
        bootUrl
    );
    const client2 = new signify.SignifyClient(
        url,
        bran2,
        signify.Tier.low,
        bootUrl
    );
    await client1.boot();
    await client2.boot();
    await client1.connect();
    await client2.connect();
    const state1 = await client1.state();
    const state2 = await client2.state();
    console.log(
        'Client 1 connected. Client AID:',
        state1.controller.state.i,
        'Agent AID: ',
        state1.agent.i
    );
    console.log(
        'Client 2 connected. Client AID:',
        state2.controller.state.i,
        'Agent AID: ',
        state2.agent.i
    );

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
    const { response: aid1 } = await waitOperation<{ i: string }>(
        client1,
        await icpResult1.op()
    );
    await client1
        .identifiers()
        .addEndRole('alice', 'agent', client1!.agent!.pre);
    console.log("Alice's AID:", aid1.i);

    const icpResult2 = await client2.identifiers().create('bob', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    let op2 = await icpResult2.op();
    while (!op2['done']) {
        op2 = await client2.operations().get(op2.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    const aid2 = op2['response'];
    await client2.identifiers().addEndRole('bob', 'agent', client2!.agent!.pre);
    console.log("Bob's AID:", aid2.i);

    // Exchenge OOBIs
    const oobi1 = await client1.oobis().get('alice', 'agent');
    const oobi2 = await client2.oobis().get('bob', 'agent');

    await resolveOobi(client1, oobi2.oobis[0], 'bob');
    console.log("Client 1 resolved Bob's OOBI");
    await resolveOobi(client2, oobi1.oobis[0], 'alice');
    console.log("Client 2 resolved Alice's OOBI");

    // List Client 1 contacts
    let contacts1 = await client1.contacts().list();
    expect(contacts1[0].alias).toEqual('bob');
    expect(contacts1[0].challenges).toHaveLength(0);

    // Bob responds to Alice challenge
    await client2.challenges().respond('bob', aid1.i, challenge1_small.words);
    console.log('Bob responded to Alice challenge with signed words');

    // Alice verifies Bob's response
    const verifyOperation = await waitOperation(
        client1,
        await client1
            .challenges()
            .verify('alice', aid2.i, challenge1_small.words)
    );
    console.log('Alice verified challenge response');

    //Alice mark response as accepted
    const verifyResponse = verifyOperation.response as {
        exn: Record<string, unknown>;
    };
    const exn = new Serder(verifyResponse.exn);

    await client1.challenges().responded('alice', aid2.i, exn.ked.d);
    console.log('Alice marked challenge response as accepted');

    // Check Bob's challenge in conctats
    contacts1 = await client1.contacts().list();
    expect(contacts1[0].challenges[0].authenticated).toEqual(true);
}, 30000);
