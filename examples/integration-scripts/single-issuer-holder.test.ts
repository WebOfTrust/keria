import assert from 'node:assert';
import signify, {
    SignifyClient,
    IssueCredentialArgs,
    Operation,
    Serder,
} from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';

const SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const { bootUrl, url, vleiServerUrl, witnessUrls } = resolveEnvironment();

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
    await waitOperation(client, op, 5000);
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
    const result = await waitOperation<{ i: string }>(client, op, 5000);
    return result.response;
}

async function createRegistry(
    client: SignifyClient,
    name: string,
    registryName: string
) {
    const result = await client.registries().create({ name, registryName });
    const op = await result.op();
    await waitOperation(client, op, 5000);

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

    await waitOperation(client, result.op, 5000);

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
    // eslint-disable-next-line no-constant-condition
    while (true) {
        const notifications = await client.notifications().list();
        for (const notif of notifications.notes) {
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

async function wait<T>(fn: () => Promise<T>, timeout: number = 10000) {
    const start = Date.now();
    const errors: Error[] = [];
    while (Date.now() - start < timeout) {
        try {
            const result = await fn();
            return result;
        } catch (error) {
            errors.push(error as Error);
            await new Promise((resolve) => setTimeout(resolve, 1000));
        }
    }

    throw new RetryError(`Retry failed after ${Date.now() - start} ms`, errors);
}

async function waitOperation<T>(
    client: SignifyClient,
    op: Operation<T>,
    timeout: number = 30000
): Promise<Operation<T>> {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        const current = (await client
            .operations()
            .get(op.name)) as Operation<T>;

        if (current.done) {
            return current;
        }

        await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    throw new Error(`Operation timed out after ${Date.now() - start}ms`);
}

class RetryError extends Error {
    constructor(
        message: string,
        public errors: Error[]
    ) {
        super(message);
    }
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

        const issuerWits = await Promise.all(
            witnessUrls.map(async (url, i) => {
                const result = await resolveOobi(
                    issuerClient,
                    url + '/oobi',
                    `witness-${i}`
                );
                return result.i;
            })
        );

        const holderWits = await Promise.all(
            witnessUrls.map(async (url, i) => {
                const result = await resolveOobi(
                    holderClient,
                    url + '/oobi',
                    `witness-${i}`
                );
                return result.i;
            })
        );

        const verifierWits = await Promise.all(
            witnessUrls.map(async (url, i) => {
                const result = await resolveOobi(
                    verifierClient,
                    url + '/oobi',
                    `witness-${i}`
                );
                return result.i;
            })
        );

        // Create two identifiers, one for each client
        const issuerPrefix = await createIdentifier(
            issuerClient,
            'issuer',
            issuerWits
        );
        const holderPrefix = await createIdentifier(
            holderClient,
            'holder',
            holderWits
        );
        const verifierPrefix = await createIdentifier(
            verifierClient,
            'verifier',
            verifierWits
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

        const grantNotification = await waitForNotification(
            holderClient,
            '/exn/ipex/grant'
        );

        await admitCredential(
            holderClient,
            'holder',
            grantNotification.a.d!,
            issuerPrefix
        );

        await holderClient.notifications().mark(grantNotification.i);

        const c = await wait(async () => {
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

        const verifierGrantNotification = await waitForNotification(
            verifierClient,
            '/exn/ipex/grant'
        );

        console.log(
            `Notifcation of grant received by verifier ${verifierGrantNotification.a.d}`
        );
        await admitCredential(
            verifierClient,
            'verifier',
            verifierGrantNotification.a.d!,
            holderPrefix
        );

        await verifierClient.notifications().mark(verifierGrantNotification.i);

        console.log('Checking for credential');
        const p = await wait(async () => {
            const creds = await verifierClient.credentials().list();
            assert(creds.length >= 1);
            return creds[0];
        });

        console.log(`Credential ${p.sad.d} received by Verifier`);
    },
    1000 * 60 * 5
);
