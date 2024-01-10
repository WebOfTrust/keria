import { strict as assert } from 'assert';
import signify, {
    SignifyClient,
    Serder,
    IssueCredentialResult,
    IssueCredentialArgs,
    Operation,
} from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';
import { sleep, waitForNotifications } from './utils/test-util';
import { getOrCreateClient } from './utils/test-setup';

const { vleiServerUrl } = resolveEnvironment();
const WITNESS_AIDS = [
    'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
    'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
    'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
];

const SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const SCHEMA_OOBI = `${vleiServerUrl}/oobi/${SCHEMA_SAID}`;

test('multisig', async function run() {
    await signify.ready();
    // Boot Four clients
    const [client1, client2, client3] = await Promise.all([
        getOrCreateClient(),
        getOrCreateClient(),
        getOrCreateClient()
    ]);

    // Create three identifiers, one for each client
    let [aid1, aid2, aid3] = await Promise.all([
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
        client3.oobis().get('issuer', 'agent')
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
    let rstates = [aid1['state'], aid2['state']];
    let states = rstates;
    let icpResult1 = await client1.identifiers().create('holder', {
        algo: signify.Algos.group,
        mhab: aid1,
        isith: 2,
        nsith: 2,
        toad: aid1.state.b.length,
        wits: aid1.state.b,
        states: states,
        rstates: rstates,
    });
    op1 = await icpResult1.op();
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

    let msgSaid = await waitAndMarkNotification(client2, '/multisig/icp');
    console.log('Member2 received exchange message to join multisig');

    let res = await client2.groups().getRequest(msgSaid);
    let exn = res[0].exn;
    let icp = exn.e.icp;

    let icpResult2 = await client2.identifiers().create('holder', {
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

    const multisig = identifiers2.aids[1].prefix;

    // Multisig end role   

    aid1 = await client1.identifiers().get('member1');
    aid2 = await client2.identifiers().get('member2');
    const members = await client1.identifiers().members('holder');
    let ghab1 = await client1.identifiers().get('holder');
    const signing = members['signing'];
    const eid1 = Object.keys(signing[0].ends.agent)[0];
    const eid2 = Object.keys(signing[1].ends.agent)[0];

    console.log(`Starting multisig end role authorization for agent ${eid1}`);


    let stamp = createTimestamp();

    let endRoleRes = await client1.identifiers().addEndRole('holder', 'agent', eid1, stamp);
    op1 = await endRoleRes.op();
    let rpy = endRoleRes.serder;
    sigs = endRoleRes.sigs;
    let ghabState1 = ghab1['state'];
    let seal = [
        'SealEvent',
        { i: ghab1['prefix'], s: ghabState1['ee']['s'], d: ghabState1['ee']['d'] },
    ];
    sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    let roleims = signify.d(
        signify.messagize(rpy, sigers, seal, undefined, undefined, false)
    );
    atc = roleims.substring(rpy.size);
    let roleembeds = {
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
        `Member1 authorized agent role to ${eid1}, waiting for others to authorize...`
    );

    //Member2 check for notifications and join the authorization
    msgSaid = await waitAndMarkNotification(client2, '/multisig/rpy');
    console.log(
        'Member2 received exchange message to join the end role authorization'
    );
    res = await client2.groups().getRequest(msgSaid);
    exn = res[0].exn;
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
        { i: ghab2['prefix'], s: ghabState2['ee']['s'], d: ghabState2['ee']['d'] },
    ];
    sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
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
    op1 = await waitOperation(client1, op1, 30);
    op2 = await waitOperation(client2, op2, 30);
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
        { i: ghab1['prefix'], s: ghabState1['ee']['s'], d: ghabState1['ee']['d'] },
    ];
    sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
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
        { i: ghab2['prefix'], s: ghabState2['ee']['s'], d: ghabState2['ee']['d'] },
    ];

    sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
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
    op1 = await waitOperation(client1, op1);
    op2 = await waitOperation(client2, op2);
    console.log(`End role authorization for agent ${eid2} completed!`);


    // Holder resolve multisig OOBI
    const oobiMultisig = await client1.oobis().get('holder', 'agent');
    console.log(`Memeber1: Holder multisig AID OOBIs: ` + JSON.stringify(oobiMultisig));

    const oobiMultisig2 = await client2.oobis().get('holder', 'agent');
    console.log(`Memeber2: Holder multisig AID OOBIs: ` + JSON.stringify(oobiMultisig2));


    op3 = await client3.oobis().resolve(oobiMultisig.oobis[0], 'holder');
    op3 = await waitOperation(client3, op3);
    console.log(`Issuer resolved multisig holder OOBI`);


    let holderAid = await client1.identifiers().get('holder');
    aid1 = await client1.identifiers().get('member1');
    aid2 = await client2.identifiers().get('member2');

    console.log(`Issuer starting credential issuance to holder...`);
    const registires = await client3.registries().list('issuer');
    let recps: string[] = [aid1['prefix'], aid2['prefix']]
    await issueCredential(client3, {
        issuerName: 'issuer',
        registryId: registires[0].regk,
        schemaId: SCHEMA_SAID,
        recipient: holderAid['prefix'],
        data: {
            LEI: '5493001KJTIIGC8Y1R17',
        },
    }
        , recps
    );
    console.log(`Issuer sent credential grant to holder.`);


    let grantMsgSaid = await waitForNotification(client1, '/exn/ipex/grant')
    console.log(`Member1 received /exn/ipex/grant msg with SAID: ${grantMsgSaid} `);
    let exnRes = await client1.exchanges().get(grantMsgSaid)

    recp = [aid2['state']].map((state) => state['i']);
    await multisigAdmitCredential(
        client1,
        'holder',
        'member1',
        exnRes.exn.d,
        exnRes.exn.i,
        recp
    )
    console.log(`Member1 admitted credential with SAID : ${exnRes.exn.e.acdc.d}`)


    let grantMsgSaid2 = await waitForNotification(client2, '/exn/ipex/grant')
    //grantMsgSaid2 = await waitForNotification(client2, '/multisig/exn', true)
    console.log(`Member2 received /exn/ipex/grant msg with SAID: ${grantMsgSaid2} `);
    let exnRes2 = await client2.exchanges().get(grantMsgSaid2)

    assert.equal(grantMsgSaid, grantMsgSaid2);

    console.log(`Member2 /exn/ipex/grant msg :  ` + JSON.stringify(exnRes2));

    let recp2 = [aid1['state']].map((state) => state['i']);
    await multisigAdmitCredential(
        client2,
        'holder',
        'member2',
        exnRes.exn.d,
        exnRes.exn.i,
        recp2
    )
    console.log(`Member2 admitted credential with SAID : ${exnRes.exn.e.acdc.d}`)

    // msgSaid = await waitForNotification(client3, '/exn/ipex/admit');
    // console.log('Issuer received exn admit response');

    let creds1 = await client1.credentials().list();
    console.log(`Member1 has ${creds1.length} credential`);

    const MAX_RETRIES: number = 10
    let retryCount = 0
    while (retryCount < MAX_RETRIES) {
        retryCount = retryCount + 1
        console.log(` retry-${retryCount}: No credentials yet...`);

        creds1 = await client1.credentials().list();
        if (creds1.length > 0)
            break;

        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    console.log(`Member1 has ${creds1.length} credential : ` + JSON.stringify(creds1));
    assert.equal(creds1.length, 1);

}, 360000);

async function waitAndMarkNotification(client: SignifyClient, route: string) {
    const notes = await waitForNotifications(client, route);

    await Promise.all(
        notes.map(async (note) => {
            await client.notifications().mark(note.i);
        })
    );

    return notes[notes.length - 1]?.a.d ?? '';
}

export async function waitForNotification(
    client: SignifyClient,
    route: string,
    enableLog: boolean = false,
    maxRetries: number = 10
) {
    if (enableLog === true) {
        console.log(`  Waiting for notification with route : ${route}`)
    }
    let retryCount = 0
    let msgSaid = ''
    while (msgSaid == '') {
        retryCount = retryCount + 1

        const notifications = await client.notifications().list()
        if (enableLog === true) {
            console.log(`  Notifications list : ${JSON.stringify(notifications)}`)
        }
        for (const notif of notifications.notes) {
            if (notif.a.r == route) {
                msgSaid = notif.a.d
                await client.notifications().mark(notif.i)
            }
        }
        if (retryCount >= maxRetries) {
            console.log(`No notification found with route : ${route}`)
            break;
        }

        await new Promise((resolve) => setTimeout(resolve, 1000))
    }
    return msgSaid
}

export async function waitOperation<T>(
    client: SignifyClient,
    op: Operation<T>,
    retries: number = 10
): Promise<Operation<T>> {
    const WAIT = 1000;
    while (retries-- > 0) {
        op = await client.operations().get(op.name);
        if (op.done === true) return op;
        await sleep(WAIT);
    }
    throw new Error(`Timeout: operation ${op.name}`);
}

async function createAID(client: SignifyClient, name: string, wits: string[]) {
    const icpResult1 = await client.identifiers().create(name, {
        toad: wits.length,
        wits: wits,
    });
    await waitOperation(client, await icpResult1.op());
    const aid = await client.identifiers().get(name);
    await client.identifiers().addEndRole(name, 'agent', client!.agent!.pre);
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
    args: IssueCredentialArgs,
    recps: string[]
) {
    const result = await client.credentials().issue(args);

    await waitOperation(client, result.op);

    const creds = await client.credentials().list();
    assert.equal(creds.length, 1);
    assert.equal(creds[0].sad.s, args.schemaId);
    assert.equal(creds[0].status.s, '0');

    const dt = createTimestamp();

    if (args.recipient) {
        const [grant, gsigs, end] = await client.ipex().grant({
            senderName: args.issuerName,
            recipient: args.recipient,
            datetime: dt,
            acdc: result.acdc,
            anc: result.anc,
            iss: result.iss,
        });

        //// TODO: use multisig holder as exn recipient
        //await client.ipex().submitGrant(args.issuerName, grant, gsigs, end, [args.recipient]);
        await client.ipex().submitGrant(args.issuerName, grant, gsigs, end, recps);
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
) {
    const dt = createTimestamp()

    let mHab = await client.identifiers().get(memberAlias)
    let gHab = await client.identifiers().get(groupName)

    const [admit, sigs, end] = await client
        .ipex()
        .admit(groupName, '', grantSaid, dt)

    await client.ipex().submitAdmit(groupName, admit, sigs, end, [issuerPrefix]);
    // await client
    //   .exchanges()
    //   .sendFromEvents(groupName, 'credential', admit, sigs, end, [issuerPrefix])

    if (recipients?.length < 1) {
        return;
    }

    let mstate = gHab['state']
    let seal = [
        'SealEvent',
        { i: gHab['prefix'], s: mstate['ee']['s'], d: mstate['ee']['d'] }
    ]
    let sigers = sigs.map((sig: any) => new signify.Siger({ qb64: sig }))
    let ims = signify.d(signify.messagize(admit, sigers, seal))
    let atc = ims.substring(admit.size)
    atc += end
    let gembeds = {
        exn: [admit, atc]
    }

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
        )
}