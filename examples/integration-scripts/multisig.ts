import { strict as assert } from 'assert';
import signify, { Serder } from 'signify-ts';
import { SignifyClient } from '../../dist';

const url = 'http://127.0.0.1:3901';
const boot_url = 'http://127.0.0.1:3903';

await run();

async function run() {
    await signify.ready();
    // Boot Four clients
    const client1 = await bootClient();
    const client2 = await bootClient();
    const client3 = await bootClient();
    const client4 = await bootClient();

    // Create four identifiers, one for each client
    let aid1 = await createAID(client1, 'member1');
    let aid2 = await createAID(client2, 'member2');
    let aid3 = await createAID(client3, 'member3');
    let aid4 = await createAID(client4, 'holder');

    // Exchange OOBIs
    let schemaSAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
    let schemaOobi = 'http://127.0.0.1:7723/oobi/' + schemaSAID;
    console.log('Resolving OOBIs');
    let oobi1 = await client1.oobis().get('member1', 'agent');
    let oobi2 = await client2.oobis().get('member2', 'agent');
    let oobi3 = await client3.oobis().get('member3', 'agent');
    let oobi4 = await client4.oobis().get('holder', 'agent');

    let op1 = await client1.oobis().resolve(oobi2.oobis[0], 'member2');
    op1 = await waitForOp(client1, op1);
    op1 = await client1.oobis().resolve(oobi3.oobis[0], 'member3');
    op1 = await waitForOp(client1, op1);
    op1 = await client1.oobis().resolve(schemaOobi, 'schema');
    op1 = await waitForOp(client1, op1);
    op1 = await client1.oobis().resolve(oobi4.oobis[0], 'holder');
    op1 = await waitForOp(client1, op1);
    console.log('Member1 resolved 4 OOBIs');

    let op2 = await client2.oobis().resolve(oobi1.oobis[0], 'member1');
    op2 = await waitForOp(client2, op2);
    op2 = await client2.oobis().resolve(oobi3.oobis[0], 'member3');
    op2 = await waitForOp(client2, op2);
    op2 = await client2.oobis().resolve(schemaOobi, 'schema');
    op2 = await waitForOp(client2, op2);
    op2 = await client2.oobis().resolve(oobi4.oobis[0], 'holder');
    op2 = await waitForOp(client2, op2);
    console.log('Member2 resolved 4 OOBIs');

    let op3 = await client3.oobis().resolve(oobi1.oobis[0], 'member1');
    op3 = await waitForOp(client3, op3);
    op3 = await client3.oobis().resolve(oobi2.oobis[0], 'member2');
    op3 = await waitForOp(client3, op3);
    op3 = await client3.oobis().resolve(schemaOobi, 'schema');
    op3 = await waitForOp(client3, op3);
    op3 = await client3.oobis().resolve(oobi4.oobis[0], 'holder');
    op3 = await waitForOp(client3, op3);
    console.log('Member3 resolved 4 OOBIs');

    let op4 = await client4.oobis().resolve(oobi1.oobis[0], 'member1');
    op4 = await waitForOp(client4, op4);
    op4 = await client4.oobis().resolve(oobi2.oobis[0], 'member2');
    op4 = await waitForOp(client4, op4);
    op4 = await client4.oobis().resolve(oobi3.oobis[0], 'member3');
    op4 = await waitForOp(client4, op4);

    op4 = await client4.oobis().resolve(schemaOobi, 'schema');
    op4 = await waitForOp(client4, op4);

    console.log('Holder resolved 4 OOBIs');

    // First member challenge the other members with a random list of words
    // List of words should be passed to the other members out of band
    // The other members should do the same challenge/response flow, not shown here for brevity
    const words = (await client1.challenges().generate(128)).words;
    console.log('Member1 generated challenge words:', words);

    await client2.challenges().respond('member2', aid1.prefix, words);
    console.log('Member2 responded challenge with signed words');

    await client3.challenges().respond('member3', aid1.prefix, words);
    console.log('Member3 responded challenge with signed words');

    op1 = await client1.challenges().verify('member1', aid2.prefix, words);
    op1 = await waitForOp(client1, op1);
    console.log('Member1 verified challenge response from member2');
    let exnwords = new Serder(op1.response.exn);
    op1 = await client1
        .challenges()
        .responded('member1', aid2.prefix, exnwords.ked.d);
    console.log('Member1 marked challenge response as accepted');

    op1 = await client1.challenges().verify('member1', aid3.prefix, words);
    op1 = await waitForOp(client1, op1);
    console.log('Member1 verified challenge response from member3');
    exnwords = new Serder(op1.response.exn);
    op1 = await client1
        .challenges()
        .responded('member1', aid3.prefix, exnwords.ked.d);
    console.log('Member1 marked challenge response as accepted');

    // First member start the creation of a multisig identifier
    let rstates = [aid1['state'], aid2['state'], aid3['state']];
    let states = rstates;
    let icpResult1 = await client1.identifiers().create('multisig', {
        algo: signify.Algos.group,
        mhab: aid1,
        isith: 3,
        nsith: 3,
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
        states: states,
        rstates: rstates,
    });
    op1 = await icpResult1.op();
    let serder = icpResult1.serder;

    let sigs = icpResult1.sigs;
    let sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    let ims = signify.d(signify.messagize(serder, sigers));
    let atc = ims.substring(serder.size);
    let embeds = {
        icp: [serder, atc],
    };

    let smids = states.map((state) => state['i']);
    let recp = [aid2['state'], aid3['state']].map((state) => state['i']);

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

    let msgSaid = await waitForMessage(client2, '/multisig/icp');
    console.log('Member2 received exchange message to join multisig');

    let res = await client2.groups().getRequest(msgSaid);
    let exn = res[0].exn;
    let icp = exn.e.icp;

    let icpResult2 = await client2.identifiers().create('multisig', {
        algo: signify.Algos.group,
        mhab: aid2,
        isith: icp.kt,
        nsith: icp.nt,
        toad: parseInt(icp.bt),
        wits: icp.b,
        states: states,
        rstates: rstates,
    });
    op2 = await icpResult2.op();
    serder = icpResult2.serder;
    sigs = icpResult2.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    embeds = {
        icp: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1['state'], aid3['state']].map((state) => state['i']);

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

    // Third member check notifications and join the multisig
    msgSaid = await waitForMessage(client3, '/multisig/icp');
    console.log('Member3 received exchange message to join multisig');

    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;
    icp = exn.e.icp;
    let icpResult3 = await client3.identifiers().create('multisig', {
        algo: signify.Algos.group,
        mhab: aid3,
        isith: icp.kt,
        nsith: icp.nt,
        toad: parseInt(icp.bt),
        wits: icp.b,
        states: states,
        rstates: rstates,
    });
    op3 = await icpResult3.op();
    serder = icpResult3.serder;
    sigs = icpResult3.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    embeds = {
        icp: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1['state'], aid2['state']].map((state) => state['i']);

    await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/icp',
            { gid: serder.pre, smids: smids, rmids: smids },
            embeds,
            recp
        );
    console.log('Member3 joined, multisig waiting for others...');

    // Check for completion
    op1 = await waitForOp(client1, op1);
    op2 = await waitForOp(client2, op2);
    op3 = await waitForOp(client3, op3);
    console.log('Multisig created!');
    const identifiers1 = await client1.identifiers().list();
    assert.equal(identifiers1.aids.length, 2);
    assert.equal(identifiers1.aids[0].name, 'member1');
    assert.equal(identifiers1.aids[1].name, 'multisig');

    const identifiers2 = await client2.identifiers().list();
    assert.equal(identifiers2.aids.length, 2);
    assert.equal(identifiers2.aids[0].name, 'member2');
    assert.equal(identifiers2.aids[1].name, 'multisig');

    const identifiers3 = await client3.identifiers().list();
    assert.equal(identifiers3.aids.length, 2);
    assert.equal(identifiers3.aids[0].name, 'member3');
    assert.equal(identifiers3.aids[1].name, 'multisig');

    console.log(
        'Client 1 managed AIDs:\n',
        identifiers1.aids[0].name,
        `[${identifiers1.aids[0].prefix}]\n`,
        identifiers1.aids[1].name,
        `[${identifiers1.aids[1].prefix}]`
    );
    console.log(
        'Client 2 managed AIDs:\n',
        identifiers2.aids[0].name,
        `[${identifiers2.aids[0].prefix}]\n`,
        identifiers2.aids[1].name,
        `[${identifiers2.aids[1].prefix}]`
    );
    console.log(
        'Client 3 managed AIDs:\n',
        identifiers3.aids[0].name,
        `[${identifiers3.aids[0].prefix}]\n`,
        identifiers3.aids[1].name,
        `[${identifiers3.aids[1].prefix}]`
    );

    let multisig = identifiers3.aids[1].prefix;

    // Multisig end role
    // for brevity, this script authorize only the agent of member 1
    // a full implementation should repeat the process to authorize all agents

    let members = await client1.identifiers().members('multisig');
    let hab = await client1.identifiers().get('multisig');
    let aid = hab['prefix'];
    let signing = members['signing'];
    let eid1 = Object.keys(signing[0].ends.agent)[0]; //agent of member 1
    // other agent eids can be obtained with
    // let eid2 = Object.keys(signing[1].ends.agent)[0];
    // let eid3 = Object.keys(signing[2].ends.agent)[0];
    console.log(`Starting multisig end role authorization for agent ${eid1}`);

    // initial stamp for the event that will be passed in the exn message
    // to the other members
    let stamp = new Date().toISOString().replace('Z', '000+00:00');

    let endRoleRes = await client1
        .identifiers()
        .addEndRole('multisig', 'agent', eid1, stamp);
    op1 = await endRoleRes.op();
    let rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;
    let mstate = hab['state'];
    let seal = [
        'SealEvent',
        { i: hab['prefix'], s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    let roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    let roleembeds: any = {
        rpy: [rpy, atc],
    };
    recp = [aid2['state'], aid3['state']].map((state) => state['i']);
    res = await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/rpy',
            { gid: aid },
            roleembeds,
            recp
        );
    console.log(
        `Member1 authorized agent role to ${eid1}, waiting for others to authorize...`
    );

    //Member2 check for notifications and join the authorization
    msgSaid = await waitForMessage(client2, '/multisig/rpy');
    console.log('Member2 received exchange message to join the end role authorization');
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;
    // stamp, eid and role are provided in the exn message
    let rpystamp = exn.e.rpy.dt;
    let rpyrole = exn.e.rpy.a.role;
    let rpyeid = exn.e.rpy.a.eid;
    endRoleRes = await client2
        .identifiers()
        .addEndRole('multisig', rpyrole, rpyeid, rpystamp);
    op2 = await endRoleRes.op();
    rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;

    hab = await client2.identifiers().get('multisig');
    mstate = hab['state'];
    seal = [
        'SealEvent',
        { i: hab['prefix'], s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    roleembeds = {
        rpy: [rpy, atc],
    };
    recp = [aid1['state'], aid3['state']].map((state) => state['i']);
    res = await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/rpy',
            { gid: aid },
            roleembeds,
            recp
        );
    console.log(
        `Member2 authorized agent role to ${eid1}, waiting for others to authorize...`
    );

    //Member3 check for notifications and join the authorization
    msgSaid = await waitForMessage(client3, '/multisig/rpy');
    console.log('Member3 received exchange message to join the end role authorization');
    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;
    rpystamp = exn.e.rpy.dt;
    rpyrole = exn.e.rpy.a.role;
    rpyeid = exn.e.rpy.a.eid;
    endRoleRes = await client3
        .identifiers()
        .addEndRole('multisig', rpyrole, rpyeid, rpystamp);

    op3 = await endRoleRes.op();
    rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;
    hab = await client3.identifiers().get('multisig');
    mstate = hab['state'];
    seal = [
        'SealEvent',
        { i: hab['prefix'], s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    roleembeds = {
        rpy: [rpy, atc],
    };
    recp = [aid1['state'], aid2['state']].map((state) => state['i']);
    res = await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/rpy',
            { gid: aid },
            roleembeds,
            recp
        );
    console.log(
        `Member3 authorized agent role to ${eid1}, waiting for others to authorize...`
    );

    // Check for completion
    op1 = await waitForOp(client1, op1);
    op2 = await waitForOp(client2, op2);
    op3 = await waitForOp(client3, op3);
    console.log(`End role authorization for agent ${eid1}completed!`);

    // Holder resolve multisig OOBI
    let oobimultisig = await client1.oobis().get('multisig', 'agent');
    op4 = await client4.oobis().resolve(oobimultisig.oobis[0], 'multisig');
    op4 = await waitForOp(client4, op4);
    console.log(`Holder resolved multisig OOBI`);

    // MultiSig Interaction

    // Member1 initiates an interaction event
    let data = {
        i: 'EBgew7O4yp8SBle0FU-wwN3GtnaroI0BQfBGAj33QiIG',
        s: '0',
        d: 'EBgew7O4yp8SBle0FU-wwN3GtnaroI0BQfBGAj33QiIG'
      };
    let eventResponse1 = await client1.identifiers().interact('multisig', data);
    op1 = await eventResponse1.op();
    serder = eventResponse1.serder;
    sigs = eventResponse1.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    let xembeds = {
        ixn: [serder, atc],
    };

    smids = states.map((state) => state['i']);
    recp = [aid2['state'], aid3['state']].map((state) => state['i']);

    await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/ixn',
            { gid: serder.pre, smids: smids, rmids: smids },
            xembeds,
            recp
        );
    console.log(
        'Member1 initiates interaction event, waiting for others to join...'
    );

    // Member2 check for notifications and join the interaction event
    msgSaid = await waitForMessage(client2, '/multisig/ixn');
    console.log('Member2 received exchange message to join the interaction event');
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;
    let ixn = exn.e.ixn;
    data = ixn.a;

    icpResult2 = await client2.identifiers().interact('multisig', data);
    op2 = await icpResult2.op();
    serder = icpResult2.serder;
    sigs = icpResult2.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    xembeds = {
        ixn: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1['state'], aid3['state']].map((state) => state['i']);

    await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/ixn',
            { gid: serder.pre, smids: smids, rmids: smids },
            xembeds,
            recp
        );
    console.log('Member2 joins interaction event, waiting for others...');

    // Member3 check for notifications and join the interaction event
    msgSaid = await waitForMessage(client3, '/multisig/ixn');
    console.log('Member3 received exchange message to join the interaction event');
    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;
    ixn = exn.e.ixn;
    data = ixn.a;

    icpResult3 = await client3.identifiers().interact('multisig', data);
    op3 = await icpResult3.op();
    serder = icpResult3.serder;
    sigs = icpResult3.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    xembeds = {
        ixn: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1['state'], aid2['state']].map((state) => state['i']);

    await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/ixn',
            { gid: serder.pre, smids: smids, rmids: smids },
            xembeds,
            recp
        );
    console.log('Member3 joins interaction event, waiting for others...');

    // Check for completion
    op1 = await waitForOp(client1, op1);
    op2 = await waitForOp(client2, op2);
    op3 = await waitForOp(client3, op3);
    console.log('Multisig interaction completed!');

    // Members agree out of band to rotate keys
    console.log('Members agree out of band to rotate keys');
    icpResult1 = await client1.identifiers().rotate('member1');
    op1 = await icpResult1.op();
    op1 = await waitForOp(client1, op1);
    aid1 = await client1.identifiers().get('member1');

    console.log('Member1 rotated keys');
    icpResult2 = await client2.identifiers().rotate('member2');
    op2 = await icpResult2.op();
    op2 = await waitForOp(client2, op2);
    aid2 = await client2.identifiers().get('member2');
    console.log('Member2 rotated keys');
    icpResult3 = await client3.identifiers().rotate('member3');
    op3 = await icpResult3.op();
    op3 = await waitForOp(client3, op3);
    aid3 = await client3.identifiers().get('member3');
    console.log('Member3 rotated keys');

    // Update new key states
    op1 = await client1.keyStates().query(aid2.prefix, 1);
    op1 = await waitForOp(client1, op1);
    let aid2State = op1['response'];
    op1 = await client1.keyStates().query(aid3.prefix, 1);
    op1 = await waitForOp(client1, op1);
    let aid3State = op1['response'];

    op2 = await client2.keyStates().query(aid3.prefix, 1);
    op2 = await waitForOp(client2, op2);
    op2 = await client2.keyStates().query(aid1.prefix, 1);
    op2 = await waitForOp(client2, op2);
    let aid1State = op2['response'];

    op3 = await client3.keyStates().query(aid1.prefix, 1);
    op3 = await waitForOp(client3, op3);
    op3 = await client3.keyStates().query(aid2.prefix, 1);
    op3 = await waitForOp(client3, op3);

    op4 = await client4.keyStates().query(aid1.prefix, 1);
    op4 = await waitForOp(client4, op4);
    op4 = await client4.keyStates().query(aid2.prefix, 1);
    op4 = await waitForOp(client4, op4);
    op4 = await client4.keyStates().query(aid3.prefix, 1);
    op4 = await waitForOp(client4, op4);
    
    rstates = [aid1State, aid2State, aid3State];
    states = rstates;

    // Multisig Rotation

    // Member1 initiates a rotation event
    eventResponse1 = await client1
        .identifiers()
        .rotate('multisig', { states: states, rstates: rstates });
    op1 = await eventResponse1.op();
    serder = eventResponse1.serder;
    sigs = eventResponse1.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    let rembeds = {
        rot: [serder, atc],
    };

    smids = states.map((state) => state['i']);
    recp = [aid2State, aid3State].map((state) => state['i']);

    await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/rot',
            { gid: serder.pre, smids: smids, rmids: smids },
            rembeds,
            recp
        );
    console.log(
        'Member1 initiates rotation event, waiting for others to join...'
    );

    // Member2 check for notifications and join the rotation event
    msgSaid = await waitForMessage(client2, '/multisig/rot');
    console.log('Member2 received exchange message to join the rotation event');

    await new Promise((resolve) => setTimeout(resolve, 5000));
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;

    icpResult2 = await client2
        .identifiers()
        .rotate('multisig', { states: states, rstates: rstates });
    op2 = await icpResult2.op();
    serder = icpResult2.serder;
    sigs = icpResult2.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    rembeds = {
        rot: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1State, aid3State].map((state) => state['i']);

    await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/ixn',
            { gid: serder.pre, smids: smids, rmids: smids },
            rembeds,
            recp
        );
    console.log('Member2 joins rotation event, waiting for others...');

    // Member3 check for notifications and join the rotation event
    msgSaid = await waitForMessage(client3, '/multisig/rot');
    console.log('Member3 received exchange message to join the rotation event');
    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;

    icpResult3 = await client3
        .identifiers()
        .rotate('multisig', { states: states, rstates: rstates });
    op3 = await icpResult3.op();
    serder = icpResult3.serder;
    sigs = icpResult3.sigs;
    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(serder, sigers));
    atc = ims.substring(serder.size);
    rembeds = {
        rot: [serder, atc],
    };

    smids = exn.a.smids;
    recp = [aid1State, aid2State].map((state) => state['i']);

    await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/ixn',
            { gid: serder.pre, smids: smids, rmids: smids },
            rembeds,
            recp
        );
    console.log('Member3 joins rotation event, waiting for others...');

    // Check for completion
    op1 = await waitForOp(client1, op1);
    op2 = await waitForOp(client2, op2);
    op3 = await waitForOp(client3, op3);
    console.log('Multisig rotation completed!');

    hab = await client1.identifiers().get('multisig');
    aid = hab['prefix'];
    
    // Multisig Registry creation
    aid1 = await client1.identifiers().get('member1');
    aid2 = await client2.identifiers().get('member2');
    aid3 = await client3.identifiers().get('member3');

    console.log('Starting multisig registry creation');

    let vcpRes1 = await client1.registries().create({
        name: 'multisig',
        registryName: 'vLEI Registry',
        nonce: 'AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s',
    });
    op1 = await vcpRes1.op();
    serder = vcpRes1.regser;
    let regk = serder.pre;
    let anc = vcpRes1.serder;
    sigs = vcpRes1.sigs;

    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(anc, sigers));
    atc = ims.substring(anc.size);
    let regbeds = {
        vcp: [serder, ''],
        anc: [anc, atc],
    };

    recp = [aid2['state'], aid3['state']].map((state) => state['i']);
    res = await client1
        .exchanges()
        .send(
            'member1',
            'registry',
            aid1,
            '/multisig/vcp',
            { gid: multisig, usage: 'Issue vLEIs' },
            regbeds,
            recp
        );

    console.log('Member1 initiated registry, waiting for others to join...');

    // Member2 check for notifications and join the create registry event
    msgSaid = await waitForMessage(client2, '/multisig/vcp');
    console.log('Member2 received exchange message to join the create registry event');
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;

    let vcpRes2 = await client2.registries().create({
        name: 'multisig',
        registryName: 'vLEI Registry',
        nonce: 'AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s',
    });
    op2 = await vcpRes2.op();
    serder = vcpRes2.regser;
    let regk2 = serder.pre;
    anc = vcpRes2.serder;
    sigs = vcpRes2.sigs;

    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(anc, sigers));
    atc = ims.substring(anc.size);
    regbeds = {
        vcp: [serder, ''],
        anc: [anc, atc],
    };

    recp = [aid1['state'], aid3['state']].map((state) => state['i']);
    await client2
        .exchanges()
        .send(
            'member2',
            'registry',
            aid2,
            '/multisig/vcp',
            { gid: multisig, usage: 'Issue vLEIs' },
            regbeds,
            recp
        );
    console.log('Member2 joins registry event, waiting for others...');

    // Member3 check for notifications and join the create registry event
    msgSaid = await waitForMessage(client3, '/multisig/vcp');
    console.log('Member3 received exchange message to join the create registry event');

    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;

    let vcpRes3 = await client3.registries().create({
        name: 'multisig',
        registryName: 'vLEI Registry',
        nonce: 'AHSNDV3ABI6U8OIgKaj3aky91ZpNL54I5_7-qwtC6q2s',
    });
    op3 = await vcpRes3.op();
    serder = vcpRes3.regser;
    let regk3 = serder.pre;
    anc = vcpRes3.serder;
    sigs = vcpRes3.sigs;

    sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    ims = signify.d(signify.messagize(anc, sigers));
    atc = ims.substring(anc.size);
    regbeds = {
        vcp: [serder, ''],
        anc: [anc, atc],
    };

    recp = [aid1['state'], aid2['state']].map((state) => state['i']);
    await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/vcp',
            { gid: multisig, usage: 'Issue vLEIs' },
            regbeds,
            recp
        );

    // Done
    op1 = await waitForOp(client1, op1);
    op2 = await waitForOp(client2, op2);
    op3 = await waitForOp(client3, op3);
    console.log('Multisig create registry completed!');

    //Create Credential
    console.log('Starting multisig credential creation');

    const vcdata = {
        LEI: '5493001KJTIIGC8Y1R17',
    };
    let holder = aid4.prefix

    let TIME = new Date().toISOString().replace('Z', '000+00:00');;
    let credRes = await client1
        .credentials()
        .issue(
            'multisig',
            regk,
            schemaSAID,
            holder,
            vcdata,
            undefined,
            undefined,
            TIME
        );
    op1 = await credRes.op();

    let acdc = new signify.Serder(credRes.acdc);
    let iss = credRes.iserder;
    let ianc = credRes.anc;
    let isigs = credRes.sigs;
    let acdcSaider = credRes.acdcSaider;
    let issExnSaider = credRes.issExnSaider;

    sigers = isigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    ims = signify.d(signify.messagize(ianc, sigers));
    let atc1 = ims.substring(ianc.size);

    let vcembeds = {
        acdc: [acdc, ''],
        iss: [iss, ''],
        anc: [ianc, atc1],
    };
    recp = [aid2['state'], aid3['state']].map((state) => state['i']);
    await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/iss',
            { gid: aid },
            vcembeds,
            recp
        );

    console.log('Member1 initiated credential creation, waiting for others to join...');

    // Member2 check for notifications and join the credential create  event
    msgSaid = await waitForMessage(client2, '/multisig/iss');
    console.log('Member2 received exchange message to join the credential create event');
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;

    let credRes2 = await client2
        .credentials()
        .issue(
            'multisig',
            regk2,
            schemaSAID,
            holder,
            vcdata,
            undefined,
            undefined,
            exn.e.acdc.a.dt
        );

    op2 = await credRes2.op();

    acdc = new signify.Serder(credRes2.acdc);
    iss = credRes2.iserder;
    ianc = credRes2.anc;
    isigs = credRes2.sigs;

    sigers = isigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    ims = signify.d(signify.messagize(ianc, sigers));
    let atc2 = ims.substring(ianc.size);

    vcembeds = {
        acdc: [acdc, ''],
        iss: [iss, ''],
        anc: [ianc, atc2],
    };

    recp = [aid1['state'], aid3['state']].map((state) => state['i']);
    await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/iss',
            { gid: aid },
            vcembeds,
            recp
        );
    console.log('Member2 joins credential create event, waiting for others...');

    // Member3 check for notifications and join the create registry event
    msgSaid = await waitForMessage(client3, '/multisig/iss');
    console.log('Member3 received exchange message to join the credential create event');
    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;

    let credRes3 = await client3
        .credentials()
        .issue(
            'multisig',
            regk3,
            schemaSAID,
            holder,
            vcdata,
            undefined,
            undefined,
            exn.e.acdc.a.dt
        );

    op3 = await credRes3.op();
    acdc = new signify.Serder(credRes3.acdc);
    iss = credRes3.iserder;
    ianc = credRes3.anc;
    isigs = credRes3.sigs;

    sigers = isigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    ims = signify.d(signify.messagize(ianc, sigers));
    let atc3 = ims.substring(ianc.size);

    vcembeds = {
        acdc: [acdc, ''],
        iss: [iss, ''],
        anc: [ianc, atc3],
    };

    recp = [aid1['state'], aid2['state']].map((state) => state['i']);
    await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/iss',
            { gid: aid },
            vcembeds,
            recp
        );
    console.log('Member3 joins credential create event, waiting for others...');

    // Check completion
    op1 = await waitForOp(client1, op1);
    op2 = await waitForOp(client2, op2);
    op3 = await waitForOp(client3, op3);
    console.log('Multisig create credential completed!');

    let m = await client1.identifiers().get('multisig');

    // Update states
    op1 = await client1.keyStates().query(m.prefix, 4);
    op1 = await waitForOp(client1, op1);
    op2 = await client2.keyStates().query(m.prefix, 4);
    op2 = await waitForOp(client2, op2);
    op3 = await client3.keyStates().query(m.prefix, 4);
    op3 = await waitForOp(client3, op3);
    op4 = await client4.keyStates().query(m.prefix, 4);
    op4 = await waitForOp(client4, op4);

    // IPEX grant message
    console.log('Starting grant message');
    stamp = new Date().toISOString().replace('Z', '000+00:00');

    let [grant, gsigs, end] = await client1
        .ipex()
        .grant('multisig', holder, '', acdc, acdcSaider, iss, issExnSaider, ianc, atc1, undefined, stamp);

    await client1
        .exchanges()
        .sendFromEvents(
            'multisig',
            'credential',
            grant,
            gsigs,
            end,
            [holder]
        );

    mstate = m['state'];
    seal = [
        'SealEvent',
        { i: m['prefix'], s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    sigers = gsigs.map((sig: any) => new signify.Siger({ qb64: sig }));

    let gims = signify.d(
        signify.messagize(grant, sigers, seal)
    );
    atc = gims.substring(grant.size);
    atc += end;
    let gembeds: any = {
        exn: [grant, atc],
    };
    recp = [aid2['state'], aid3['state']].map((state) => state['i']);
    await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/exn',
            { gid: m['prefix'] },
            gembeds,
            recp
        );
    
    console.log('Member1 initiated grant message, waiting for others to join...');

    msgSaid = await waitForMessage(client2, '/multisig/exn');
    console.log('Member2 received exchange message to join the grant message');
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;

    let [grant2, gsigs2, end2] = await client2
        .ipex()
        .grant('multisig', holder, '', acdc, acdcSaider, iss, issExnSaider, ianc, atc2, undefined, stamp);
    
    await client2
        .exchanges()
        .sendFromEvents(
            'multisig',
            'credential',
            grant2,
            gsigs2,
            end2,
            [holder]
        );
    
    sigers = gsigs2.map((sig: any) => new signify.Siger({ qb64: sig }));

    gims = signify.d(
        signify.messagize(grant2, sigers, seal)
    );
    atc = gims.substring(grant2.size);
    atc += end2;

    gembeds = {
        exn: [grant2, atc],
    };
    recp = [aid1['state'], aid3['state']].map((state) => state['i']);
    await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/exn',
            { gid: m['prefix'] },
            gembeds,
            recp
        );

    console.log('Member2 joined grant message, waiting for others to join...');

    msgSaid = await waitForMessage(client3, '/multisig/exn');
    console.log('Member3 received exchange message to join the grant message');
    res = await client3.groups().getRequest(msgSaid);
    exn = res[0].exn;

    let [grant3, gsigs3, end3] = await client3
        .ipex()
        .grant('multisig', holder, '', acdc, acdcSaider, iss, issExnSaider, ianc, atc3, undefined, stamp);
    
    await client3
        .exchanges()
        .sendFromEvents(
            'multisig',
            'credential',
            grant3,
            gsigs3,
            end3,
            [holder]
        );

    sigers = gsigs3.map((sig: any) => new signify.Siger({ qb64: sig }));

    gims = signify.d(
        signify.messagize(grant3, sigers, seal)
    );
    atc = gims.substring(grant3.size);
    atc += end3;

    gembeds = {
        exn: [grant3, atc],
    };
    recp = [aid1['state'], aid2['state']].map((state) => state['i']);
    await client3
        .exchanges()
        .send(
            'member3',
            'multisig',
            aid3,
            '/multisig/exn',
            { gid: m['prefix'] },
            gembeds,
            recp
        );

    console.log('Member3 joined grant message, waiting for others to join...');

    msgSaid = await waitForMessage(client4, '/exn/ipex/grant');
    console.log('Holder received exchange message with the grant message');
    res = await client4.exchanges().get(msgSaid);

    let [admit, asigs, aend] = await client4
        .ipex()
        .admit('holder', '', res.exn.d);

    res = await client4.ipex().submitAdmit('holder', admit, asigs, aend, [m['prefix']] );
    
    console.log('Holder creates and sends admit message');

    msgSaid = await waitForMessage(client1, '/exn/ipex/admit');
    console.log('Member1 received exchange message with the admit response');
    let creds = await client4.credentials().list('holder');
    console.log(`Holder holds ${creds.length} credential`)


}

async function waitForOp(client:SignifyClient, op:any) {
    while (!op['done']) {
        op = await client.operations().get(op.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    return op
}

async function waitForMessage(client:SignifyClient, route:string) {
    let msgSaid = '';
    while (msgSaid == '') {
        let notifications = await client.notifications().list();
        for (let notif of notifications.notes) {
            if (notif.a.r == route) {
                msgSaid = notif.a.d;
                await client.notifications().mark(notif.i);
            }
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    return msgSaid
    
}

async function bootClient():Promise<SignifyClient>{
    let bran = signify.randomPasscode();
    let client = new signify.SignifyClient(
        url,
        bran,
        signify.Tier.low,
        boot_url
    );
    await client.boot();
    await client.connect();
    let state = await client.state();
    console.log(
        'Client AID:',
        state.controller.state.i,
        'Agent AID: ',
        state.agent.i
    );
    return client
}

async function createAID(client:SignifyClient, name:string){
    let icpResult1 = await client.identifiers().create(name, {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    let op = await icpResult1.op();
    op = await waitForOp(client, op);
    let aid = await client.identifiers().get(name);
    await client
        .identifiers()
        .addEndRole(name, 'agent', client!.agent!.pre);
    console.log(name, "AID:", aid.prefix);
    return aid
}
