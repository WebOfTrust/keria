import { strict as assert } from 'assert';
import { Saider, Serder, SignifyClient } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';
import {
    resolveOobi,
    waitForNotifications,
    waitOperation,
} from './utils/test-util';
import { retry } from './utils/retry';
import {
    getOrCreateClients,
    getOrCreateContact,
    getOrCreateIdentifier,
} from './utils/test-setup';
import { randomUUID } from 'crypto';
import { step } from './utils/test-step';

const { vleiServerUrl } = resolveEnvironment();

const QVI_SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const LE_SCHEMA_SAID = 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY';
const vLEIServerHostUrl = `${vleiServerUrl}/oobi`;
const QVI_SCHEMA_URL = `${vLEIServerHostUrl}/${QVI_SCHEMA_SAID}`;
const LE_SCHEMA_URL = `${vLEIServerHostUrl}/${LE_SCHEMA_SAID}`;

interface Aid {
    name: string;
    prefix: string;
    oobi: string;
}

function createTimestamp() {
    return new Date().toISOString().replace('Z', '000+00:00');
}

async function createAid(client: SignifyClient, name: string): Promise<Aid> {
    const [prefix, oobi] = await getOrCreateIdentifier(client, name);
    return { prefix, oobi, name };
}

let issuerClient: SignifyClient;
let holderClient: SignifyClient;
let verifierClient: SignifyClient;
let legalEntityClient: SignifyClient;

let issuerAid: Aid;
let holderAid: Aid;
let verifierAid: Aid;
let legalEntityAid: Aid;

beforeAll(async () => {
    [issuerClient, holderClient, verifierClient, legalEntityClient] =
        await getOrCreateClients(4);
});

beforeAll(async () => {
    [issuerAid, holderAid, verifierAid, legalEntityAid] = await Promise.all([
        createAid(issuerClient, 'issuer'),
        createAid(holderClient, 'holder'),
        createAid(verifierClient, 'verifier'),
        createAid(legalEntityClient, 'legal-entity'),
    ]);
});

beforeAll(async () => {
    await Promise.all([
        getOrCreateContact(issuerClient, 'holder', holderAid.oobi),
        getOrCreateContact(issuerClient, 'verifier', verifierAid.oobi),
        getOrCreateContact(holderClient, 'issuer', issuerAid.oobi),
        getOrCreateContact(holderClient, 'verifier', verifierAid.oobi),
        getOrCreateContact(holderClient, 'legal-entity', legalEntityAid.oobi),
        getOrCreateContact(verifierClient, 'issuer', issuerAid.oobi),
        getOrCreateContact(verifierClient, 'holder', holderAid.oobi),
        getOrCreateContact(legalEntityClient, 'holder', holderAid.oobi),
    ]);
});

test('single signature credentials', async () => {
    await step('Resolve schema oobis', async () => {
        await Promise.all([
            resolveOobi(issuerClient, QVI_SCHEMA_URL),
            resolveOobi(issuerClient, LE_SCHEMA_URL),
            resolveOobi(holderClient, QVI_SCHEMA_URL),
            resolveOobi(holderClient, LE_SCHEMA_URL),
            resolveOobi(verifierClient, QVI_SCHEMA_URL),
            resolveOobi(verifierClient, LE_SCHEMA_URL),
            resolveOobi(legalEntityClient, QVI_SCHEMA_URL),
            resolveOobi(legalEntityClient, LE_SCHEMA_URL),
        ]);
    });

    const registry = await step('Create registry', async () => {
        const registryName = 'vLEI-test-registry';
        const regResult = await issuerClient
            .registries()
            .create({ name: issuerAid.name, registryName: registryName });

        await waitOperation(issuerClient, await regResult.op());
        const registries = await issuerClient.registries().list(issuerAid.name);
        const registry: { name: string; regk: string } = registries[0];
        assert.equal(registries.length, 1);
        assert.equal(registry.name, registryName);
        return registry;
    });

    await step('issuer can get schemas', async () => {
        const issuerQviSchema = await issuerClient
            .schemas()
            .get(QVI_SCHEMA_SAID);

        assert.equal(issuerQviSchema.$id, QVI_SCHEMA_SAID);

        const issuerLeSchema = await issuerClient.schemas().get(LE_SCHEMA_SAID);

        assert.equal(issuerLeSchema.$id, LE_SCHEMA_SAID);
    });

    await step('holder can list schemas', async () => {
        const holderSchemas = await holderClient.schemas().list();
        assert.equal(holderSchemas.length, 2);
    });

    const qviCredentialId = await step('create QVI credential', async () => {
        const vcdata = {
            LEI: '5493001KJTIIGC8Y1R17',
        };

        const issResult = await issuerClient.credentials().issue({
            issuerName: issuerAid.name,
            registryId: registry.regk,
            schemaId: QVI_SCHEMA_SAID,
            recipient: holderAid.prefix,
            data: vcdata,
        });

        await waitOperation(issuerClient, issResult.op);
        return issResult.acdc.ked.d as string;
    });

    await step('issuer list credentials', async () => {
        const issuerCredentials = await issuerClient.credentials().list();
        assert(issuerCredentials.length >= 1);
        assert.equal(issuerCredentials[0].sad.s, QVI_SCHEMA_SAID);
        assert.equal(issuerCredentials[0].sad.i, issuerAid.prefix);
        assert.equal(issuerCredentials[0].status.s, '0');
    });

    await step('issuer list credentials with filter', async () => {
        expect(
            await issuerClient
                .credentials()
                .list({ filter: { '-i': issuerAid.prefix } })
        ).toHaveLength(1);

        expect(
            await issuerClient
                .credentials()
                .list({ filter: { '-s': QVI_SCHEMA_SAID } })
        ).toHaveLength(1);

        expect(
            await issuerClient
                .credentials()
                .list({ filter: { '-a-i': holderAid.prefix } })
        ).toHaveLength(1);

        expect(
            await issuerClient.credentials().list({
                filter: {
                    '-i': issuerAid.prefix,
                    '-s': QVI_SCHEMA_SAID,
                    '-a-i': holderAid.prefix,
                },
            })
        ).toHaveLength(1);

        expect(
            await issuerClient.credentials().list({
                filter: {
                    '-i': randomUUID(),
                    '-s': QVI_SCHEMA_SAID,
                    '-a-i': holderAid.prefix,
                },
            })
        ).toHaveLength(0);
    });

    await step('issuer get credential by id', async () => {
        const issuerCredential = await issuerClient
            .credentials()
            .get(issuerAid.name, qviCredentialId);
        assert.equal(issuerCredential.sad.s, QVI_SCHEMA_SAID);
        assert.equal(issuerCredential.sad.i, issuerAid.prefix);
        assert.equal(issuerCredential.status.s, '0');
    });

    await step('issuer IPEX grant', async () => {
        const dt = createTimestamp();
        const issuerCredential = await issuerClient
            .credentials()
            .get(issuerAid.name, qviCredentialId);
        assert(issuerCredential !== undefined);

        const [grant, gsigs, gend] = await issuerClient.ipex().grant({
            senderName: issuerAid.name,
            acdc: new Serder(issuerCredential.sad),
            anc: new Serder(issuerCredential.anc),
            iss: new Serder(issuerCredential.iss),
            ancAttachment: issuerCredential.ancAttachment,
            recipient: holderAid.prefix,
            datetime: dt,
        });

        await issuerClient
            .ipex()
            .submitGrant(issuerAid.name, grant, gsigs, gend, [
                holderAid.prefix,
            ]);
    });

    await step('holder IPEX admit', async () => {
        const holderNotifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/grant'
        );
        const grantNotification = holderNotifications[0]; // should only have one notification right now

        const [admit, sigs, aend] = await holderClient
            .ipex()
            .admit(
                holderAid.name,
                '',
                grantNotification.a.d!,
                createTimestamp()
            );
        await holderClient
            .ipex()
            .submitAdmit(holderAid.name, admit, sigs, aend, [issuerAid.prefix]);

        await holderClient.notifications().mark(grantNotification.i);
    });

    await step('holder has credential', async () => {
        const holderCredential = await retry(async () => {
            const result = await holderClient
                .credentials()
                .get(holderAid.name, qviCredentialId);
            assert(result !== undefined);
            return result;
        });
        assert.equal(holderCredential.sad.s, QVI_SCHEMA_SAID);
        assert.equal(holderCredential.sad.i, issuerAid.prefix);
        assert.equal(holderCredential.status.s, '0');
        assert(holderCredential.atc !== undefined);
    });

    await step('holder IPEX present', async () => {
        const holderCredential = await holderClient
            .credentials()
            .get(holderAid.name, qviCredentialId);

        const [grant2, gsigs2, gend2] = await holderClient.ipex().grant({
            senderName: holderAid.name,
            recipient: verifierAid.prefix,
            acdc: new Serder(holderCredential.sad),
            anc: new Serder(holderCredential.anc),
            iss: new Serder(holderCredential.iss),
            acdcAttachment: holderCredential.atc,
            ancAttachment: holderCredential.ancatc,
            issAttachment: holderCredential.issAtc,
            datetime: createTimestamp(),
        });
        await holderClient
            .exchanges()
            .sendFromEvents(
                holderAid.name,
                'presentation',
                grant2,
                gsigs2,
                gend2,
                [verifierAid.prefix]
            );
    });

    await step('verifier receives IPEX grant', async () => {
        const verifierNotifications = await waitForNotifications(
            verifierClient,
            '/exn/ipex/grant'
        );

        const verifierGrantNote = verifierNotifications[0];

        const [admit3, sigs3, aend3] = await verifierClient
            .ipex()
            .admit(
                verifierAid.name,
                '',
                verifierGrantNote.a.d!,
                createTimestamp()
            );

        await verifierClient
            .ipex()
            .submitAdmit(verifierAid.name, admit3, sigs3, aend3, [
                holderAid.prefix,
            ]);

        await verifierClient.notifications().mark(verifierGrantNote.i);

        const verifierCredential = await retry(async () =>
            verifierClient.credentials().get(verifierAid.name, qviCredentialId)
        );

        assert.equal(verifierCredential.sad.s, QVI_SCHEMA_SAID);
        assert.equal(verifierCredential.sad.i, issuerAid.prefix);
        assert.equal(verifierCredential.status.s, '0'); // 0 = issued
    });

    const holderRegistry: { regk: string } = await step(
        'holder create registry for LE credential',
        async () => {
            const registryName = 'vLEI-test-registry';
            const regResult = await holderClient
                .registries()
                .create({ name: holderAid.name, registryName: registryName });

            await waitOperation(holderClient, await regResult.op());
            const registries = await holderClient
                .registries()
                .list(holderAid.name);
            assert(registries.length >= 1);
            return registries[0];
        }
    );

    const leCredentialId = await step(
        'holder create LE (chained) credential',
        async () => {
            const qviCredential = await holderClient
                .credentials()
                .get(holderAid.name, qviCredentialId);

            const result = await holderClient.credentials().issue({
                issuerName: holderAid.name,
                recipient: legalEntityAid.prefix,
                registryId: holderRegistry.regk,
                schemaId: LE_SCHEMA_SAID,
                data: {
                    LEI: '5493001KJTIIGC8Y1R17',
                },
                rules: Saider.saidify({
                    d: '',
                    usageDisclaimer: {
                        l: 'Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with any laws or that an implied or expressly intended purpose will be fulfilled.',
                    },
                    issuanceDisclaimer: {
                        l: 'All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the validation process was complete. The vLEI Credential has been issued to the legal entity or person named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set forth in the vLEI Ecosystem Governance Framework.',
                    },
                })[1],
                source: Saider.saidify({
                    d: '',
                    qvi: {
                        n: qviCredential.sad.d,
                        s: qviCredential.sad.s,
                    },
                })[1],
            });

            await waitOperation(holderClient, result.op);
            return result.acdc.ked.d;
        }
    );

    await step('LE credential IPEX grant', async () => {
        const dt = createTimestamp();
        const leCredential = await holderClient
            .credentials()
            .get(holderAid.name, leCredentialId);
        assert(leCredential !== undefined);

        const [grant, gsigs, gend] = await holderClient.ipex().grant({
            senderName: holderAid.name,
            acdc: new Serder(leCredential.sad),
            anc: new Serder(leCredential.anc),
            iss: new Serder(leCredential.iss),
            ancAttachment: leCredential.ancAttachment,
            recipient: legalEntityAid.prefix,
            datetime: dt,
        });

        await holderClient
            .ipex()
            .submitGrant(holderAid.name, grant, gsigs, gend, [
                legalEntityAid.prefix,
            ]);
    });

    await step('Legal Entity IPEX admit', async () => {
        const notifications = await waitForNotifications(
            legalEntityClient,
            '/exn/ipex/grant'
        );
        const grantNotification = notifications[0];

        const [admit, sigs, aend] = await legalEntityClient
            .ipex()
            .admit(
                legalEntityAid.name,
                '',
                grantNotification.a.d!,
                createTimestamp()
            );

        await legalEntityClient
            .ipex()
            .submitAdmit(legalEntityAid.name, admit, sigs, aend, [
                holderAid.prefix,
            ]);

        await legalEntityClient.notifications().mark(grantNotification.i);
    });

    await step('Legal Entity has chained credential', async () => {
        const legalEntityCredential = await retry(async () =>
            legalEntityClient
                .credentials()
                .get(legalEntityAid.name, leCredentialId)
        );

        assert.equal(legalEntityCredential.sad.s, LE_SCHEMA_SAID);
        assert.equal(legalEntityCredential.sad.i, holderAid.prefix);
        assert.equal(legalEntityCredential.sad.a.i, legalEntityAid.prefix);
        assert.equal(legalEntityCredential.status.s, '0');
        assert.equal(legalEntityCredential.chains[0].sad.d, qviCredentialId);
        assert(legalEntityCredential.atc !== undefined);
    });

    await step('Issuer revoke QVI credential', async () => {
        const revokeOperation = await issuerClient
            .credentials()
            .revoke(issuerAid.name, qviCredentialId);

        await waitOperation(issuerClient, revokeOperation);
        const issuerCredential = await issuerClient
            .credentials()
            .get(issuerAid.name, qviCredentialId);

        assert.equal(issuerCredential.status.s, '1');
    });
}, 90000);
