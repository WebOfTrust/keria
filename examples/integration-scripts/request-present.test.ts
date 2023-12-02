import { strict as assert } from 'assert';
import signify from 'signify-ts';
import { resolveOobi, waitOperation } from './utils/test-util';
import { resolveEnvironment } from './utils/resolve-env';

const { url, bootUrl, vleiServerUrl } = resolveEnvironment();

const schemaSAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const schemaOobi = `${vleiServerUrl}/oobi/${schemaSAID}`;

// TODO: Marked as skipped because request/present changes
test.skip('request-present', async () => {
    await signify.ready();
    // Boot three clients
    const bran1 = signify.randomPasscode();
    const bran2 = signify.randomPasscode();
    const bran3 = signify.randomPasscode();
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
    const client3 = new signify.SignifyClient(
        url,
        bran3,
        signify.Tier.low,
        bootUrl
    );

    const [state1, state2, state3] = await Promise.all([
        client1
            .boot()
            .then(() => client1.connect())
            .then(() => client1.state()),
        client2
            .boot()
            .then(() => client2.connect())
            .then(() => client2.state()),
        client3
            .boot()
            .then(() => client3.connect())
            .then(() => client3.state()),
    ]);
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
    console.log(
        'Client 3 connected. Client AID:',
        state3.controller.state.i,
        'Agent AID: ',
        state3.agent.i
    );

    // Create two identifiers, one for each client
    const op1 = await client1.identifiers().create('issuer', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    await waitOperation(client1, await op1.op());
    const aid1 = await client1.identifiers().get('issuer');
    await client1
        .identifiers()
        .addEndRole('issuer', 'agent', client1!.agent!.pre);
    console.log("Issuer's AID:", aid1.prefix);

    const op2 = await client2.identifiers().create('recipient', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    await waitOperation(client2, await op2.op());
    const aid2 = await client2.identifiers().get('recipient');
    await client2
        .identifiers()
        .addEndRole('recipient', 'agent', client2!.agent!.pre);
    console.log("Recipient's AID:", aid2.prefix);

    const op3 = await client3.identifiers().create('verifier', {
        toad: 3,
        wits: [
            'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
            'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
            'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
        ],
    });
    await waitOperation(client3, await op3.op());

    const aid3 = await client3.identifiers().get('verifier');
    await client3
        .identifiers()
        .addEndRole('verifier', 'agent', client3!.agent!.pre);
    console.log("Verifier's AID:", aid3.prefix);

    // Exchenge OOBIs
    console.log('Resolving OOBIs...');
    const [oobi1, oobi2, oobi3] = await Promise.all([
        client1.oobis().get('issuer', 'agent'),
        client2.oobis().get('recipient', 'agent'),
        client3.oobis().get('verifier', 'agent'),
    ]);

    await Promise.all([
        resolveOobi(client1, oobi2.oobis[0], 'recipient'),
        resolveOobi(client1, oobi3.oobis[0], 'verifier'),
        resolveOobi(client1, schemaOobi, 'schema'),
    ]);

    console.log('Issuer resolved 3 OOBIs');

    await Promise.all([
        resolveOobi(client2, oobi1.oobis[0], 'issuer'),
        resolveOobi(client2, oobi3.oobis[0], 'verifier'),
        resolveOobi(client2, schemaOobi, 'schema'),
    ]);
    console.log('Recipient resolved 3 OOBIs');

    await Promise.all([
        resolveOobi(client3, oobi1.oobis[0], 'issuer'),
        resolveOobi(client3, oobi2.oobis[0], 'recipient'),
        resolveOobi(client3, schemaOobi, 'schema'),
    ]);
    console.log('Verifier resolved 3 OOBIs');

    // Create registry for issuer
    const vcpResult = await client1
        .registries()
        .create({ name: 'issuer', registryName: 'vLEI' });
    await waitOperation(client1, await vcpResult.op());
    const registries = await client1.registries().list('issuer');
    assert.equal(registries.length, 1);
    assert.equal(registries[0].name, 'vLEI');
    const schema = await client1.schemas().get(schemaSAID);
    assert.equal(schema.$id, schemaSAID);
    const schemas = await client2.schemas().list();
    assert.equal(schemas.length, 1);
    assert.equal(schemas[0].$id, schemaSAID);
    console.log('Registry created');

    // Issue credential
    const vcdata = {
        LEI: '5493001KJTIIGC8Y1R17',
    };
    const credRes = await client1.credentials().issue({
        issuerName: 'issuer',
        registryId: registries[0].regk,
        schemaId: schemaSAID,
        recipient: aid2.prefix,
        data: vcdata,
    });
    await waitOperation(client1, credRes.op);

    const creds1 = await client1.credentials().list();
    assert.equal(creds1.length, 1);
    assert.equal(creds1[0].sad.s, schemaSAID);
    assert.equal(creds1[0].sad.i, aid1.prefix);
    assert.equal(creds1[0].status.s, '0'); // 0 = issued
    console.log('Credential issued');

    // Recipient check issued credential
    const creds2 = await client2.credentials().list();
    assert.equal(creds2.length, 1);
    assert.equal(creds2[0].sad.s, schemaSAID);
    assert.equal(creds2[0].sad.i, aid1.prefix);
    assert.equal(creds2[0].status.s, '0'); // 0 = issued
    console.log('Credential received by recipient');

    // Verifier request credential to recipient
    await client3.credentials().request('verifier', aid2.prefix, schemaSAID);

    // Recipient checks for a presentation request notification
    let requestReceived = false;
    while (!requestReceived) {
        const notifications = await client2.notifications().list();
        for (const notif of notifications) {
            if (notif.a.r == '/presentation/request') {
                assert.equal(notif.a.schema.n, schemaSAID);
                requestReceived = true;
                await client2.notifications().mark(notif.i);
            }
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    // Recipient present credential to verifier
    await client1
        .credentials()
        .present('issuer', creds1[0].sad.d, 'verifier', true);

    // Verifier checks for a presentation notification
    requestReceived = false;
    while (!requestReceived) {
        const notifications = await client3.notifications().list();
        for (const notif of notifications) {
            if (notif.a.r == '/presentation') {
                assert.equal(notif.a.schema.n, schemaSAID);
                requestReceived = true;
                await client3.notifications().mark(notif.i);
            }
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    const creds3 = await client3
        .credentials()
        .list({ filter: { '-i': { $eq: aid1.prefix } } }); // filter by issuer
    assert.equal(creds3.length, 1);
    assert.equal(creds3[0].sad.s, schemaSAID);
    assert.equal(creds3[0].sad.i, aid1.prefix);
    assert.equal(creds3[0].status.s, '0'); // 0 = issued
    assert.equal(creds3[0].sad.a.i, aid2.prefix); // verify that the issuee is the same as the presenter
}, 60000);
