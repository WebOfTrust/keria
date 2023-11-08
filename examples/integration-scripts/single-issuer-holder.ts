import { strict as assert } from 'assert';
import signify, {
    CredentialResult,
    Serder,
    Siger,
    SignifyClient,
    d,
    messagize,
} from 'signify-ts';

const URL = 'http://127.0.0.1:3901';
const BOOT_URL = 'http://127.0.0.1:3903';
const SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const WITNESS_AIDS: string[] = []; // ['BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'];
const SCHEMA_OOBI =
    'http://127.0.0.1:7723/oobi/EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';

await run();

function createTimestamp() {
    const dt = new Date().toISOString().replace('Z', '000+00:00');
    return dt;
}

async function connect() {
    const client = new signify.SignifyClient(
        URL,
        signify.randomPasscode(),
        signify.Tier.low,
        BOOT_URL
    );

    await client.boot();
    await client.connect();

    return client;
}

async function createIdentifier(client: signify.SignifyClient, name: string) {
    const icpResult1 = await client.identifiers().create(name, {
        toad: WITNESS_AIDS.length,
        wits: WITNESS_AIDS,
    });
    let op = await icpResult1.op();
    while (!op.done) {
        op = await client.operations().get(op.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    const aid = await client.identifiers().get(name);

    if (!client.agent) {
        throw new Error('No agent on client');
    }

    await client.identifiers().addEndRole(name, 'agent', client.agent.pre);

    return aid.prefix;
}

async function getAgentOobi(
    client: SignifyClient,
    name: string
): Promise<string> {
    const result = await client.oobis().get(name, 'agent');
    return result.oobis[0];
}

async function resolveOobi(
    client: SignifyClient,
    oobi: string,
    alias: string
): Promise<void> {
    console.log(`Resolve ${alias} -> ${oobi}`);
    let op = await client.oobis().resolve(oobi, alias);
    while (!op['done']) {
        op = await client.operations().get(op.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
}

async function createRegistry(
    client: SignifyClient,
    name: string,
    registryName: string
) {
    const result = await client.registries().create({ name, registryName });
    let op = await result.op();
    while (!op['done']) {
        op = await client.operations().get(op.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    const registries = await client.registries().list(name);
    assert.equal(registries.length, 1);
    assert.equal(registries[0].name, registryName);

    return registries[0];
}

async function issueCredential(
    client: SignifyClient,
    name: string,
    args: { registry: string; schema: string; recipient: string; data: unknown }
) {
    const result: CredentialResult = await client
        .credentials()
        .issue(name, args.registry, args.schema, args.recipient, args.data);

    let op = await result.op();
    while (!op['done']) {
        op = await client.operations().get(op.name);
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    const creds = await client.credentials().list(name);
    assert.equal(creds.length, 1);
    assert.equal(creds[0].sad.s, SCHEMA_SAID);
    assert.equal(creds[0].status.s, '0');

    const acdc = new Serder(result.acdc);
    const iss = result.iserder;
    const ianc = result.anc;

    const sigers = result.sigs.map((sig: string) => new Siger({ qb64: sig }));
    const ims = d(messagize(ianc, sigers));

    const atc = ims.substring(result.anc.size);
    const dt = createTimestamp();

    const [grant, gsigs, end] = await client
        .ipex()
        .grant(
            name,
            args.recipient,
            '',
            acdc,
            result.acdcSaider,
            iss,
            result.issExnSaider,
            result.anc,
            atc,
            undefined,
            dt
        );
    await client
        .exchanges()
        .sendFromEvents(name, 'credential', grant, gsigs, end, [
            args.recipient,
        ]);

    console.log('Grant message sent');

    return creds[0];
}

interface Notification {
    i: string;
    dt: string;
    r: boolean;
    a: { r: string; d?: string; m?: string };
}

async function waitForNotification(
    client: SignifyClient,
    route: string
): Promise<Notification> {
    while (true) {
        let notifications = await client.notifications().list();
        for (let notif of notifications.notes) {
            if (notif.a.r == route) {
                return notif;
            }
        }

        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
}

async function admitCredential(
    client: SignifyClient,
    name: string,
    said: string,
    recipient: string
) {
    const dt = createTimestamp();

    const [admit, sigs, end] = await client.ipex().admit(name, '', said, dt);

    await client.ipex().submitAdmit(name, admit, sigs, end, [recipient]);
}

async function run() {
    await signify.ready();
    // Boot three clients
    const issuerClient = await connect();
    const holderClient = await connect();

    const issuerState = await issuerClient.state();
    const holderState = await holderClient.state();
    console.log(
        'Issuer connected. Client AID:',
        issuerState.controller.state.i,
        'Agent AID: ',
        issuerState.agent.i
    );
    console.log(
        'Holder connected. Client AID:',
        holderState.controller.state.i,
        'Agent AID: ',
        holderState.agent.i
    );

    // Create two identifiers, one for each client
    const issuerPrefix = await createIdentifier(issuerClient, 'issuer');
    const holderPrefix = await createIdentifier(holderClient, 'holder');
    console.log("Issuer's AID: ", issuerPrefix);
    console.log("Holder's AID: ", holderPrefix);

    // Exchange OOBIs
    console.log('Resolving OOBIs...');
    const issuerOobi = await getAgentOobi(issuerClient, 'issuer');
    const holderOobi = await getAgentOobi(holderClient, 'holder');
    await resolveOobi(issuerClient, holderOobi, 'holder');
    await resolveOobi(issuerClient, SCHEMA_OOBI, 'schema');
    await resolveOobi(holderClient, issuerOobi, 'issuer');
    await resolveOobi(holderClient, SCHEMA_OOBI, 'schema');

    console.log('Resolved oobis');

    await createRegistry(issuerClient, 'issuer', 'vLEI');

    // Issue credential
    const registires = await issuerClient.registries().list('issuer');
    const creds = await issueCredential(issuerClient, 'issuer', {
        registry: registires[0].regk,
        schema: SCHEMA_SAID,
        recipient: holderPrefix,
        data: {
            LEI: '5493001KJTIIGC8Y1R17',
        },
    });

    console.log('Credential issued', creds);

    const grantNotification = await waitForNotification(
        holderClient,
        '/exn/ipex/grant'
    );

    console.log(grantNotification);

    await admitCredential(
        holderClient,
        'holder',
        grantNotification.a.d!,
        issuerPrefix
    );
    console.log('Admit sent!');

    await holderClient.notifications().mark(grantNotification.i);
    console.log('Notification marked!');

    console.log('Listing credentials...');
    let credentials = await holderClient.credentials().list('holder');
    while (credentials.length < 1) {
        console.log('No credentials yet...');
        await new Promise((resolve) => setTimeout(resolve, 1000));
        credentials = await holderClient.credentials().list('holder');
    }

    console.log('Succeeded');
    console.dir(credentials, { depth: 15 });
}
