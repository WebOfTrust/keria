// This scrip also work if you start keria with no config file with witness urls
import { strict as assert } from 'assert';
import signify from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';

const WITNESS_AID = 'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha';
const { url, bootUrl, witnessUrls } = resolveEnvironment();

test('test witness', async () => {
    await signify.ready();
    // Boot client
    const bran1 = signify.randomPasscode();
    const client1 = new signify.SignifyClient(
        url,
        bran1,
        signify.Tier.low,
        bootUrl
    );
    await client1.boot();
    await client1.connect();
    const state1 = await client1.state();
    console.log(
        'Client connected. Client AID:',
        state1.controller.state.i,
        'Agent AID: ',
        state1.agent.i
    );

    // Client 1 resolves witness OOBI
    let op1 = await client1
        .oobis()
        .resolve(witnessUrls[0] + `/oobi/${WITNESS_AID}`, 'wit');
    while (!op1['done']) {
        op1 = await client1.operations().get(op1.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    console.log('Witness OOBI resolved');

    // Client 1 creates AID with 1 witness
    let icpResult1 = await client1.identifiers().create('aid1', {
        toad: 1,
        wits: [WITNESS_AID],
    });
    op1 = await icpResult1.op();
    while (!op1['done']) {
        op1 = await client1.operations().get(op1.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    let aid1 = await client1.identifiers().get('aid1');
    console.log('AID:', aid1.prefix);
    assert.equal(aid1.state.b.length, 1);
    assert.equal(aid1.state.b[0], WITNESS_AID);

    icpResult1 = await client1.identifiers().rotate('aid1');
    op1 = await icpResult1.op();
    while (!op1['done']) {
        op1 = await client1.operations().get(op1.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    aid1 = await client1.identifiers().get('aid1');
    assert.equal(aid1.state.b.length, 1);
    assert.equal(aid1.state.b[0], WITNESS_AID);

    // Remove witness
    icpResult1 = await client1
        .identifiers()
        .rotate('aid1', { cuts: [WITNESS_AID] });

    op1 = await icpResult1.op();
    while (!op1['done']) {
        op1 = await client1.operations().get(op1.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    aid1 = await client1.identifiers().get('aid1');
    assert.equal(aid1.state.b.length, 0);

    // Add witness again

    icpResult1 = await client1
        .identifiers()
        .rotate('aid1', { adds: [WITNESS_AID] });

    op1 = await icpResult1.op();
    while (!op1['done']) {
        op1 = await client1.operations().get(op1.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    aid1 = await client1.identifiers().get('aid1');
    assert.equal(aid1.state.b.length, 1);
    assert.equal(aid1.state.b.length, 1);
    assert.equal(aid1.state.b[0], WITNESS_AID);
});
