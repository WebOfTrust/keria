import { assert, test } from 'vitest';
import signify from 'signify-ts';
import {
    assertOperations,
    getOrCreateClient,
    waitOperation,
} from './utils/test-util.ts';

test('randy', async () => {
    const client1 = await getOrCreateClient();

    let icpResult = await client1
        .identifiers()
        .create('aid1', { algo: signify.Algos.randy });
    let op = await waitOperation(client1, await icpResult.op());
    assert.equal(op['done'], true);
    let aid = op['response'];
    const icp = new signify.Serder(aid);
    assert.equal(icp.verfers.length, 1);
    assert.equal(icp.digers.length, 1);
    assert.equal(icp.sad['kt'], '1');
    assert.equal(icp.sad['nt'], '1');

    let aids = await client1.identifiers().list();
    assert.equal(aids.aids.length, 1);
    aid = aids.aids[0];
    assert.equal(aid.name, 'aid1');
    assert.equal(aid.prefix, icp.pre);

    icpResult = await client1.identifiers().interact('aid1', [icp.pre]);
    op = await waitOperation(client1, await icpResult.op());
    let ked = op['response'];
    const ixn = new signify.Serder(ked);
    assert.equal(ixn.sad['s'], '1');
    assert.deepEqual([...ixn.sad['a']], [icp.pre]);

    aids = await client1.identifiers().list();
    assert.equal(aids.aids.length, 1);
    aid = aids.aids[0];

    const events = client1.keyEvents();
    let log = await events.get(aid['prefix']);
    assert.equal(log.length, 2);

    icpResult = await client1.identifiers().rotate('aid1');
    op = await waitOperation(client1, await icpResult.op());
    ked = op['response'];
    const rot = new signify.Serder(ked);
    assert.equal(rot.sad['s'], '2');
    assert.equal(rot.verfers.length, 1);
    assert.equal(rot.digers.length, 1);
    assert.notEqual(rot.verfers[0].qb64, icp.verfers[0].qb64);
    assert.notEqual(rot.digers[0].qb64, icp.digers[0].qb64);
    const dig = new signify.Diger(
        { code: signify.MtrDex.Blake3_256 },
        rot.verfers[0].qb64b
    );
    assert.equal(dig.qb64, icp.digers[0].qb64);
    log = await events.get(aid['prefix']);
    assert.equal(log.length, 3);

    await assertOperations(client1);
}, 30000);
