import assert from 'node:assert';
import signify, {
    SignifyClient,
    IssueCredentialArgs,
    Serder,
} from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';
import { waitForNotifications, waitOperation } from './utils/test-util';
import { retry } from './utils/retry';

const SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const { bootUrl, url, vleiServerUrl, witnessIds } = resolveEnvironment();

function createTimestamp() {
    const dt = new Date().toISOString().replace('Z', '000+00:00');
    return dt;
}

async function connect(url: string, bootUrl: string) {
    const client = new signify.SignifyClient(
        url,
        signify.randomPasscode(),
        signify.Tier.low,
        bootUrl
    );

    await client.boot();
    await client.connect();

    return client;
}

async function createIdentifier(
    client: signify.SignifyClient,
    name: string,
    witnesses: string[]
) {
    const icpResult1 = await client.identifiers().create(name, {
        toad: witnesses.length,
        wits: witnesses,
    });
    const op = await icpResult1.op();
    await waitOperation(client, op);
    const aid = await client.identifiers().get(name);

    if (!client.agent) {
        throw new Error('No agent on client');
    }

    await client.identifiers().addEndRole(name, 'agent', client.agent.pre);

    return aid.prefix;
}

async function getAgentOobi(
    client: signify.SignifyClient,
    name: string
): Promise<string> {
    const result = await client.oobis().get(name, 'agent');
    return result.oobis[0];
}

async function resolveOobi(client: SignifyClient, oobi: string, alias: string) {
    console.log(`Resolve ${alias} -> ${oobi}`);
    const op = await client.oobis().resolve(oobi, alias);
    const result = await waitOperation<{ i: string }>(client, op);
    return result.response;
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
    args: IssueCredentialArgs
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

        await client
            .exchanges()
            .sendFromEvents(args.issuerName, 'credential', grant, gsigs, end, [
                args.recipient,
            ]);
    }

    console.log('Grant message sent');

    return creds[0];
}

async function grantCredential(
    client: SignifyClient,
    issuerName: string,
    recipient: string,
    acdc: Serder,
    acdcAttachment: string,
    anc: Serder,
    ancAttachment: string,
    iss: Serder,
    issAttachment: string
) {
    const dt = createTimestamp();

    const [grant, gsigs, end] = await client.ipex().grant({
        senderName: issuerName,
        recipient: recipient,
        datetime: dt,
        acdc: acdc,
        acdcAttachment: acdcAttachment,
        anc: anc,
        ancAttachment: ancAttachment,
        iss: iss,
        issAttachment: issAttachment,
    });

    await client.ipex().submitGrant(issuerName, grant, gsigs, end, [recipient]);
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

test(
    'Single issuer holder',
    async () => {
        await signify.ready();
        const issuerClient = await connect(url, bootUrl);
        const holderClient = await connect(url, bootUrl);
        const verifierClient = await connect(url, bootUrl);

        await issuerClient.state();
        await holderClient.state();
        await verifierClient.state();

        // Create two identifiers, one for each client
        const issuerPrefix = await createIdentifier(
            issuerClient,
            'issuer',
            witnessIds
        );
        const holderPrefix = await createIdentifier(
            holderClient,
            'holder',
            witnessIds
        );
        const verifierPrefix = await createIdentifier(
            verifierClient,
            'verifier',
            witnessIds
        );

        // Exchange OOBIs
        const issuerOobi = await getAgentOobi(issuerClient, 'issuer');
        const holderOobi = await getAgentOobi(holderClient, 'holder');
        const verifierOobi = await getAgentOobi(verifierClient, 'verifier');
        await resolveOobi(issuerClient, holderOobi, 'holder');
        await resolveOobi(
            issuerClient,
            vleiServerUrl + '/oobi/' + SCHEMA_SAID,
            'schema'
        );
        await resolveOobi(holderClient, issuerOobi, 'issuer');
        await resolveOobi(
            holderClient,
            vleiServerUrl + '/oobi/' + SCHEMA_SAID,
            'schema'
        );
        await resolveOobi(verifierClient, holderOobi, 'holder');
        await resolveOobi(holderClient, verifierOobi, 'verifier');
        await resolveOobi(
            verifierClient,
            vleiServerUrl + '/oobi/' + SCHEMA_SAID,
            'schema'
        );

        await createRegistry(issuerClient, 'issuer', 'vLEI');

        const registires = await issuerClient.registries().list('issuer');
        await issueCredential(issuerClient, {
            issuerName: 'issuer',
            registryId: registires[0].regk,
            schemaId: SCHEMA_SAID,
            recipient: holderPrefix,
            data: {
                LEI: '5493001KJTIIGC8Y1R17',
            },
        });

        const grantNotifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/grant'
        );

        await admitCredential(
            holderClient,
            'holder',
            grantNotifications[0].a.d!,
            issuerPrefix
        );

        await holderClient.notifications().mark(grantNotifications[0].i);

        const c = await retry(async () => {
            const creds = await holderClient.credentials().list();
            assert(creds.length >= 1);
            return creds[0];
        });

        console.log('Loading full credential');
        const cred = await holderClient
            .credentials()
            .get('holder', c['sad']['d']);

        const acdc = new Serder(cred['sad']);
        const iss = new Serder(cred['iss']);
        const anc = new Serder(cred['anc']);

        console.log(`Presenting credential to verifier: ${c['sad']['d']}`);
        await grantCredential(
            holderClient,
            'holder',
            verifierPrefix,
            acdc,
            cred['atc'],
            anc,
            cred['ancatc'],
            iss,
            cred['issatc']
        );

        const verifierGrantNotifications = await waitForNotifications(
            verifierClient,
            '/exn/ipex/grant'
        );

        console.log(
            `Notifcation of grant received by verifier ${verifierGrantNotifications[0].a.d}`
        );
        await admitCredential(
            verifierClient,
            'verifier',
            verifierGrantNotifications[0].a.d!,
            holderPrefix
        );

        await verifierClient
            .notifications()
            .mark(verifierGrantNotifications[0].i);

        console.log('Checking for credential');
        const p = await retry(async () => {
            const creds = await verifierClient.credentials().list();
            assert(creds.length >= 1);
            return creds[0];
        });

        console.log(`Credential ${p.sad.d} received by Verifier`);
    },
    1000 * 60 * 5
);
