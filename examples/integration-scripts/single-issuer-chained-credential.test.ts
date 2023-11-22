import assert from 'node:assert';
import signify, { SignifyClient, Saider } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';
import { resolveOobi, wait, waitOperation } from './utils/test-util';

const { bootUrl, url, vleiServerUrl } = resolveEnvironment();

const QVI_SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const LE_SCHEMA_SAID = 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY';
const WITNESS_AIDS: string[] = ['BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha'];

const QVI_SCHEMA_OOBI = `${vleiServerUrl}/oobi/${QVI_SCHEMA_SAID}`;
const LE_SCHEMA_OOBI = `${vleiServerUrl}/oobi/${LE_SCHEMA_SAID}`;

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
    await waitOperation(client, op, 15000);
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
    name: string,
    args: {
        registry: string;
        schema: string;
        recipient: string;
        data: Record<string, unknown>;
        source?: Record<string, unknown>;
        rules?: Record<string, unknown>;
    }
) {
    const result = await client.credentials().issue({
        issuerName: name,
        registryId: args.registry,
        schemaId: args.schema,
        recipient: args.recipient,
        data: args.data,
        rules: args.rules && Saider.saidify({ d: '', ...args.rules })[1],
        source: args.source && Saider.saidify({ d: '', ...args.source })[1],
    });

    await waitOperation(client, result.op, 10000);

    const creds = await client.credentials().list();
    const dt = createTimestamp();

    const [grant, gsigs, end] = await client.ipex().grant({
        senderName: name,
        anc: result.anc,
        iss: result.iss,
        acdc: result.acdc,
        recipient: args.recipient,
        datetime: dt,
    });

    await client.ipex().submitGrant(name, grant, gsigs, end, [args.recipient]);
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
    return wait(async () => {
        const notifications = await client.notifications().list();
        for (const notif of notifications.notes) {
            if (notif.a.r == route) {
                return notif;
            }
        }

        throw new Error('No notification');
    });
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

test('single issuer chained credentials', async () => {
    await signify.ready();
    const issuerClient = await connect(url, bootUrl);
    const holderClient = await connect(url, bootUrl);

    await issuerClient.state();
    await holderClient.state();
    const issuerPrefix = await createIdentifier(
        issuerClient,
        'issuer',
        WITNESS_AIDS
    );
    const holderPrefix = await createIdentifier(
        holderClient,
        'holder',
        WITNESS_AIDS
    );

    // Exchange OOBIs
    const issuerOobi = await getAgentOobi(issuerClient, 'issuer');
    const holderOobi = await getAgentOobi(holderClient, 'holder');
    await resolveOobi(issuerClient, holderOobi, 'holder');
    await resolveOobi(issuerClient, QVI_SCHEMA_OOBI, 'qvi-schema');
    await resolveOobi(issuerClient, LE_SCHEMA_OOBI, 'le-schema');
    await resolveOobi(holderClient, issuerOobi, 'issuer');
    await resolveOobi(holderClient, QVI_SCHEMA_OOBI, 'qvi-schema');
    await resolveOobi(holderClient, LE_SCHEMA_OOBI, 'le-schema');

    await createRegistry(issuerClient, 'issuer', 'vLEI');

    const registires = await issuerClient.registries().list('issuer');
    const result = await issuerClient.credentials().issue({
        issuerName: 'issuer',
        registryId: registires[0].regk,
        schemaId: QVI_SCHEMA_SAID,
        recipient: issuerPrefix,
        data: {
            LEI: '5493001KJTIIGC8Y1R17',
        },
    });

    await waitOperation(issuerClient, result.op, 5);
    const sourceCredential = await wait(async () => {
        const result = await issuerClient.credentials().list();
        assert(result.length >= 1);
        return result[0];
    });

    await issueCredential(issuerClient, 'issuer', {
        registry: registires[0].regk,
        schema: LE_SCHEMA_SAID,
        // schema: QVI_SCHEMA_SAID,
        recipient: holderPrefix,
        data: {
            LEI: '5493001KJTIIGC8Y1R17',
        },
        source: {
            qvi: {
                n: sourceCredential.sad.d,
                s: sourceCredential.sad.s,
            },
        },
        rules: {
            usageDisclaimer: {
                l: 'Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with any laws or that an implied or expressly intended purpose will be fulfilled.',
            },
            issuanceDisclaimer: {
                l: 'All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the validation process was complete. The vLEI Credential has been issued to the legal entity or person named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set forth in the vLEI Ecosystem Governance Framework.',
            },
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

    const holderCredential = await wait(
        async () => {
            const creds = await holderClient.credentials().list();
            const lei = creds.find(
                (cred: { schema: { $id: string } }) =>
                    cred.schema.$id === LE_SCHEMA_SAID
            );

            expect(lei).toBeDefined();
            return lei;
        },
        { timeout: 10000 }
    );

    expect(holderCredential).toMatchObject({
        sad: { a: { LEI: '5493001KJTIIGC8Y1R17' } },
    });
    expect(holderCredential.chains).toHaveLength(1);
    expect(holderCredential.chains[0]).toMatchObject({
        sad: { a: { LEI: '5493001KJTIIGC8Y1R17' } },
    });
}, 30000);
