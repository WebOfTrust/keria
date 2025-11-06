import { assert, test } from 'vitest';
import signify, { SignifyClient, Operation, CredentialData } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env.ts';
import {
    assertOperations,
    getOrCreateClient,
    getOrCreateIdentifier,
    waitAndMarkNotification,
    waitOperation,
    warnNotifications,
} from './utils/test-util.ts';
import {
    acceptMultisigIncept,
    startMultisigIncept,
} from './utils/multisig-utils.ts';

const { vleiServerUrl } = resolveEnvironment();
const WITNESS_AIDS = [
    'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
    'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
    'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
];

const SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const SCHEMA_OOBI = `${vleiServerUrl}/oobi/${SCHEMA_SAID}`;

const TIME = createTimestamp();

test('multisig', async function run() {
    await signify.ready();
    // Boot Four clients
    const [client1, client2, client3] = await Promise.all([
        getOrCreateClient(),
        getOrCreateClient(),
        getOrCreateClient(),
    ]);

    // Create three identifiers, one for each client
    let [aid1, aid2, _aid3] = await Promise.all([
        createAID(client1, 'member1', WITNESS_AIDS),
        createAID(client2, 'member2', WITNESS_AIDS),
        createAID(client3, 'issuer', WITNESS_AIDS),
    ]);

    await createRegistry(client3, 'issuer', 'issuer-reg');

    // Exchange OOBIs
    console.log('Resolving OOBIs');
    const [oobi1, oobi2, oobi3] = await Promise.all([
        client1.oobis().get('member1', 'agent'),
        client2.oobis().get('member2', 'agent'),
        client3.oobis().get('issuer', 'agent'),
    ]);

    let op1 = await client1.oobis().resolve(oobi2.oobis[0], 'member2');
    op1 = await waitOperation(client1, op1);
    op1 = await client1.oobis().resolve(oobi3.oobis[0], 'issuer');
    op1 = await waitOperation(client1, op1);
    op1 = await client1.oobis().resolve(SCHEMA_OOBI, 'schema');
    op1 = await waitOperation(client1, op1);
    console.log('Member1 resolved 3 OOBIs');

    let op2 = await client2.oobis().resolve(oobi1.oobis[0], 'member1');
    op2 = await waitOperation(client2, op2);
    op2 = await client2.oobis().resolve(oobi3.oobis[0], 'issuer');
    op2 = await waitOperation(client2, op2);
    op2 = await client2.oobis().resolve(SCHEMA_OOBI, 'schema');
    op2 = await waitOperation(client2, op2);
    console.log('Member2 resolved 3 OOBIs');

    let op3 = await client3.oobis().resolve(oobi1.oobis[0], 'member1');
    op3 = await waitOperation(client3, op3);
    op3 = await client3.oobis().resolve(oobi2.oobis[0], 'member2');
    op3 = await waitOperation(client3, op3);
    op3 = await client3.oobis().resolve(SCHEMA_OOBI, 'schema');
    op3 = await waitOperation(client3, op3);
    console.log('Issuer resolved 3 OOBIs');

    //// First member start the creation of a multisig identifier
    op1 = await startMultisigIncept(client1, {
        groupName: 'holder',
        localMemberName: aid1.name,
        isith: 2,
        nsith: 2,
        toad: aid1.state.b.length,
        wits: aid1.state.b,
        participants: [aid1.prefix, aid2.prefix],
    });
    console.log('Member1 initiated multisig, waiting for others to join...');

    // Second member check notifications and join the multisig
    let msgSaid = await waitAndMarkNotification(client2, '/multisig/icp');
    console.log('Member2 received exchange message to join multisig');
    op2 = await acceptMultisigIncept(client2, {
        groupName: 'holder',
        localMemberName: aid2.name,
        msgSaid,
    });
    console.log('Member2 joined multisig, waiting for others...');

    // Check for completion
    op1 = await waitOperation(client1, op1);
    op2 = await waitOperation(client2, op2);
    console.log('Multisig created!');

    const identifiers1 = await client1.identifiers().list();
    assert.equal(identifiers1.aids.length, 2);

    const identifiers2 = await client2.identifiers().list();
    assert.equal(identifiers2.aids.length, 2);

    console.log(
        'Member 1 managed AIDs:\n',
        identifiers1.aids[0].name,
        `[${identifiers1.aids[0].prefix}]\n`,
        identifiers1.aids[1].name,
        `[${identifiers1.aids[1].prefix}]`
    );
    console.log(
        'Member 2 managed AIDs:\n',
        identifiers2.aids[0].name,
        `[${identifiers2.aids[0].prefix}]\n`,
        identifiers2.aids[1].name,
        `[${identifiers2.aids[1].prefix}]`
    );

    // Multisig end role

    aid1 = await client1.identifiers().get('member1');
    aid2 = await client2.identifiers().get('member2');
    const members = await client1.identifiers().members('holder');
    let ghab1 = await client1.identifiers().get('holder');
    const signing = members['signing'];

    const agentEnds1 = signing[0].ends.agent;
    if (!agentEnds1) {
        throw new Error('signing[0].ends.agent is null or undefined');
    }
    const eid1 = Object.keys(agentEnds1)[0];

    const agentEnds2 = signing[1].ends.agent;
    if (!agentEnds2) {
        throw new Error('signing[1].ends.agent is null or undefined');
    }
    const eid2 = Object.keys(agentEnds2)[0];

    console.log(`Starting multisig end role authorization for agent ${eid1}`);

    const stamp = createTimestamp();

    let endRoleRes = await client1
        .identifiers()
        .addEndRole('holder', 'agent', eid1, stamp);
    op1 = await endRoleRes.op();
    let rpy = endRoleRes.serder;
    let sigs = endRoleRes.sigs;
    let ghabState1 = ghab1['state'];
    let seal = [
        'SealEvent',
        {
            i: ghab1['prefix'],
            s: ghabState1['ee']['s'],
            d: ghabState1['ee']['d'],
        },
    ];
    let sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    let roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    let atc = roleims.substring(rpy.size);
    let roleembeds = {
        rpy: [rpy, atc],
    };
    let recp = [aid2['state']].map((state) => state['i']);
    let res = await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/rpy',
            { gid: ghab1['prefix'] },
            roleembeds,
            recp
        );
    console.log(
        `Member1 authorized agent role to ${eid1}, waiting for others to authorize...`
    );

    //Member2 check for notifications and join the authorization
    msgSaid = await waitAndMarkNotification(client2, '/multisig/rpy');
    console.log(
        'Member2 received exchange message to join the end role authorization'
    );
    res = await client2.groups().getRequest(msgSaid);
    let exn = res[0].exn;
    // stamp, eid and role are provided in the exn message
    let rpystamp = exn.e.rpy.dt;
    let rpyrole = exn.e.rpy.a.role;
    let rpyeid = exn.e.rpy.a.eid;

    endRoleRes = await client2
        .identifiers()
        .addEndRole('holder', rpyrole, rpyeid, rpystamp);
    op2 = await endRoleRes.op();
    rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;

    let ghab2 = await client2.identifiers().get('holder');
    let ghabState2 = ghab2['state'];
    seal = [
        'SealEvent',
        {
            i: ghab2['prefix'],
            s: ghabState2['ee']['s'],
            d: ghabState2['ee']['d'],
        },
    ];
    sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    roleembeds = {
        rpy: [rpy, atc],
    };
    recp = [aid1['state']].map((state) => state['i']);
    res = await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/rpy',
            { gid: ghab2['prefix'] },
            roleembeds,
            recp
        );
    console.log(
        `Member2 authorized agent role to ${eid1}, waiting for others to authorize...`
    );
    // Check for completion
    await waitOperation(client1, op1);
    await waitOperation(client2, op2);
    console.log(`End role authorization for agent ${eid1} completed!`);

    console.log(`Starting multisig end role authorization for agent ${eid2}`);

    endRoleRes = await client1
        .identifiers()
        .addEndRole('holder', 'agent', eid2, stamp);
    op1 = await endRoleRes.op();
    rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;

    ghab1 = await client1.identifiers().get('holder');
    ghabState1 = ghab1['state'];
    seal = [
        'SealEvent',
        {
            i: ghab1['prefix'],
            s: ghabState1['ee']['s'],
            d: ghabState1['ee']['d'],
        },
    ];
    sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    roleembeds = {
        rpy: [rpy, atc],
    };
    recp = [aid2['state']].map((state) => state['i']);
    res = await client1
        .exchanges()
        .send(
            'member1',
            'multisig',
            aid1,
            '/multisig/rpy',
            { gid: ghab1['prefix'] },
            roleembeds,
            recp
        );
    console.log(
        `Member1 authorized agent role to ${eid2}, waiting for others to authorize...`
    );

    //Member2 check for notifications and join the authorization
    msgSaid = await waitAndMarkNotification(client2, '/multisig/rpy');
    console.log(
        'Member2 received exchange message to join the end role authorization'
    );
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;
    // stamp, eid and role are provided in the exn message
    rpystamp = exn.e.rpy.dt;
    rpyrole = exn.e.rpy.a.role;
    rpyeid = exn.e.rpy.a.eid;
    endRoleRes = await client2
        .identifiers()
        .addEndRole('holder', rpyrole, rpyeid, rpystamp);
    op2 = await endRoleRes.op();

    rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;

    ghab2 = await client2.identifiers().get('holder');
    ghabState2 = ghab2['state'];
    seal = [
        'SealEvent',
        {
            i: ghab2['prefix'],
            s: ghabState2['ee']['s'],
            d: ghabState2['ee']['d'],
        },
    ];

    sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    roleembeds = {
        rpy: [rpy, atc],
    };
    recp = [aid1['state']].map((state) => state['i']);
    res = await client2
        .exchanges()
        .send(
            'member2',
            'multisig',
            aid2,
            '/multisig/rpy',
            { gid: ghab2['prefix'] },
            roleembeds,
            recp
        );

    console.log(
        `Member2 authorized agent role to ${eid2}, waiting for others to authorize...`
    );
    // Check for completion
    await waitOperation(client1, op1);
    await waitOperation(client2, op2);
    console.log(`End role authorization for agent ${eid2} completed!`);

    // Holder resolve multisig OOBI
    const oobisRes = await client1.oobis().get('holder', 'agent');
    const oobiMultisig = oobisRes.oobis[0].split('/agent/')[0];

    op3 = await client3.oobis().resolve(oobiMultisig, 'holder');
    await waitOperation(client3, op3);
    console.log(`Issuer resolved multisig holder OOBI`);

    const holderAid = await client1.identifiers().get('holder');
    aid1 = await client1.identifiers().get('member1');
    aid2 = await client2.identifiers().get('member2');

    console.log(`Issuer starting credential issuance to holder...`);
    const registires = await client3.registries().list('issuer');
    await issueCredential(client3, 'issuer', {
        ri: registires[0].regk,
        s: SCHEMA_SAID,
        a: {
            i: holderAid['prefix'],
            LEI: '5493001KJTIIGC8Y1R17',
        },
    });
    console.log(`Issuer sent credential grant to holder.`);

    const grantMsgSaid = await waitAndMarkNotification(
        client1,
        '/exn/ipex/grant'
    );
    console.log(
        `Member1 received /exn/ipex/grant msg with SAID: ${grantMsgSaid} `
    );
    const exnRes = await client1.exchanges().get(grantMsgSaid);

    recp = [aid2['state']].map((state) => state['i']);
    op1 = await multisigAdmitCredential(
        client1,
        'holder',
        'member1',
        exnRes.exn.d,
        exnRes.exn.i,
        recp
    );
    console.log(
        `Member1 admitted credential with SAID : ${exnRes.exn.e.acdc.d}`
    );

    const grantMsgSaid2 = await waitAndMarkNotification(
        client2,
        '/exn/ipex/grant'
    );
    console.log(
        `Member2 received /exn/ipex/grant msg with SAID: ${grantMsgSaid2} `
    );
    const exnRes2 = await client2.exchanges().get(grantMsgSaid2);

    assert.equal(grantMsgSaid, grantMsgSaid2);

    console.log(`Member2 /exn/ipex/grant msg :  ` + JSON.stringify(exnRes2));

    const recp2 = [aid1['state']].map((state) => state['i']);
    op2 = await multisigAdmitCredential(
        client2,
        'holder',
        'member2',
        exnRes.exn.d,
        exnRes.exn.i,
        recp2
    );
    console.log(
        `Member2 admitted credential with SAID : ${exnRes.exn.e.acdc.d}`
    );

    await waitOperation(client1, op1);
    await waitOperation(client2, op2);

    let creds1 = await client1.credentials().list();
    console.log(`Member1 has ${creds1.length} credential`);

    const MAX_RETRIES: number = 10;
    let retryCount = 0;
    while (retryCount < MAX_RETRIES) {
        retryCount = retryCount + 1;
        console.log(` retry-${retryCount}: No credentials yet...`);

        creds1 = await client1.credentials().list();
        if (creds1.length > 0) break;

        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    console.log(
        `Member1 has ${creds1.length} credential : ` + JSON.stringify(creds1)
    );
    assert.equal(creds1.length, 1);

    await assertOperations(client1, client2, client3);
    await warnNotifications(client1, client2, client3);
}, 360000);

async function createAID(client: SignifyClient, name: string, wits: string[]) {
    await getOrCreateIdentifier(client, name);
    const aid = await client.identifiers().get(name);
    console.log(name, 'AID:', aid.prefix);
    return aid;
}

async function createRegistry(
    client: SignifyClient,
    name: string,
    registryName: string
) {
    const result = await client.registries().create({ name, registryName });
    const op = await result.op();
    await waitOperation(client, op);

    const registries = await client.registries().list(name);
    assert.equal(registries.length, 1);
    assert.equal(registries[0].name, registryName);

    return registries[0];
}

async function issueCredential(
    client: SignifyClient,
    name: string,
    data: CredentialData
) {
    const result = await client.credentials().issue(name, data);

    await waitOperation(client, result.op);

    const creds = await client.credentials().list();
    assert.equal(creds.length, 1);
    assert.equal(creds[0].sad.s, data.s);
    assert.equal(creds[0].status.s, '0');

    const dt = createTimestamp();

    if (data.a.i) {
        const [grant, gsigs, end] = await client.ipex().grant({
            senderName: name,
            recipient: data.a.i,
            datetime: dt,
            acdc: result.acdc,
            anc: result.anc,
            iss: result.iss,
        });

        let op = await client
            .ipex()
            .submitGrant(name, grant, gsigs, end, [data.a.i]);
        op = await waitOperation(client, op);
    }

    console.log('Grant message sent');

    return creds[0];
}

function createTimestamp() {
    const dt = new Date().toISOString().replace('Z', '000+00:00');
    return dt;
}

async function multisigAdmitCredential(
    client: SignifyClient,
    groupName: string,
    memberAlias: string,
    grantSaid: string,
    issuerPrefix: string,
    recipients: string[]
): Promise<Operation> {
    const mHab = await client.identifiers().get(memberAlias);
    const gHab = await client.identifiers().get(groupName);

    const [admit, sigs, end] = await client.ipex().admit({
        senderName: groupName,
        message: '',
        grantSaid: grantSaid,
        recipient: issuerPrefix,
        datetime: TIME,
    });

    const op = await client
        .ipex()
        .submitAdmit(groupName, admit, sigs, end, [issuerPrefix]);

    const mstate = gHab['state'];
    const seal = [
        'SealEvent',
        { i: gHab['prefix'], s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    const sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(admit, sigers, seal));
    let atc = ims.substring(admit.size);
    atc += end;
    const gembeds = {
        exn: [admit, atc],
    };

    await client
        .exchanges()
        .send(
            mHab.name,
            'multisig',
            mHab,
            '/multisig/exn',
            { gid: gHab['prefix'] },
            gembeds,
            recipients
        );

    return op;
}
