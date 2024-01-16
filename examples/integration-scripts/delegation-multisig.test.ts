import { strict as assert } from 'assert';
import signify from 'signify-ts';
import {
    resolveOobi,
    waitForNotifications,
    waitOperation,
} from './utils/test-util';
import { getOrCreateClient } from './utils/test-setup';

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
    const rstates = [aid1['state'], aid2['state']];
    const states = rstates;
    const icpResult1 = await client1.identifiers().create('multisig', {
        algo: signify.Algos.group,
        mhab: aid1,
        isith: 2,
        nsith: 2,
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
        states: states,
        rstates: rstates,
        delpre: aid0.prefix,
    });
    const op1 = await icpResult1.op();
    let serder = icpResult1.serder;

    let sigs = icpResult1.sigs;
    let sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    let ims = signify.d(signify.messagize(serder, sigers));
    let atc = ims.substring(serder.size);
    let embeds = {
        icp: [serder, atc],
    };

    let smids = states.map((state) => state['i']);
    let recp = [aid2['state']].map((state) => state['i']);

    await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/icp',
            { gid: serder.pre, smids: smids, rmids: smids },
            embeds,
            recp
        );
    console.log('Member1 initiated multisig, waiting for others to join...');

    // Second member check notifications and join the multisig
    const notifications = await waitForNotifications(client2, '/multisig/icp');
    await Promise.all(
        notifications.map((note) => client2.notifications().mark(note.i))
    );
    const msgSaid = notifications[notifications.length - 1].a.d;
    assert(msgSaid !== undefined);
    console.log('Member2 received exchange message to join multisig');

    const res = await client2.groups().getRequest(msgSaid);
    const exn = res[0].exn;
    const icp = exn.e.icp;

    const icpResult2 = await client2.identifiers().create('multisig', {
        algo: signify.Algos.group,
        mhab: aid2,
        isith: icp.kt,
        nsith: icp.nt,
        toad: parseInt(icp.bt),
        wits: icp.b,
        states: states,
        rstates: rstates,
        delpre: aid0.prefix,
    });
    const op2 = await icpResult2.op();
    serder = icpResult2.serder;
    sigs = icpResult2.sigs;
    sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    embeds = {
        icp: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1['state']].map((state) => state['i']);

    await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/icp',
            { gid: serder.pre, smids: smids, rmids: smids },
            embeds,
            recp
        );
    console.log('Member2 joined multisig, waiting for others...');

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
    await client0.identifiers().interact('delegator', anchor);
    console.log('Delegator approved delegation');

    // Check for completion
    await Promise.all([
        waitOperation(client1, op1),
        waitOperation(client2, op2),
    ]);
    console.log('Delegated multisig created!');

    const aid_delegate = await client1.identifiers().get('multisig');
    assert.equal(aid_delegate.prefix, delegatePrefix);
}, 30000);

async function createAID(client: signify.SignifyClient, name: string) {
    const icpResult1 = await client.identifiers().create(name, {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    await waitOperation(client, await icpResult1.op());
    const aid = await client.identifiers().get(name);
    await client.identifiers().addEndRole(name, 'agent', client!.agent!.pre);
    console.log(name, 'AID:', aid.prefix);
    return aid;
}
