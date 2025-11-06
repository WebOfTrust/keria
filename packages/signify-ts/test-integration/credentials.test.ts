import { assert, beforeAll, afterAll, test, expect } from 'vitest';
import { Ilks, Saider, Serder, SignifyClient } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env.ts';
import {
    assertNotifications,
    assertOperations,
    createAid,
    getOrCreateClients,
    getOrCreateContact,
    markAndRemoveNotification,
    resolveOobi,
    waitForNotifications,
    waitOperation,
} from './utils/test-util.ts';
import { retry } from './utils/retry.ts';
import { randomUUID } from 'node:crypto';
import { step } from './utils/test-step.ts';
import { CredentialResult } from '../src/keri/app/credentialing.ts';
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

let issuerClient: SignifyClient;
let holderClient: SignifyClient;
let verifierClient: SignifyClient;
let legalEntityClient: SignifyClient;

let issuerAid: Aid;
let holderAid: Aid;
let verifierAid: Aid;
let legalEntityAid: Aid;

let applySaid: string;
let offerSaid: string;
let agreeSaid: string;

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

afterAll(async () => {
    await assertOperations(
        issuerClient,
        holderClient,
        verifierClient,
        legalEntityClient
    );
    await assertNotifications(
        issuerClient,
        holderClient,
        verifierClient,
        legalEntityClient
    );
});

test('single signature credentials', { timeout: 90000 }, async () => {
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
        const updatedRegistryName = 'vLEI-test-registry-1';
        const regResult = await issuerClient
            .registries()
            .create({ name: issuerAid.name, registryName: registryName });

        await waitOperation(issuerClient, await regResult.op());
        let registries = await issuerClient.registries().list(issuerAid.name);
        const registry: { name: string; regk: string } = registries[0];
        assert.equal(registries.length, 1);
        assert.equal(registry.name, registryName);

        await issuerClient
            .registries()
            .rename(issuerAid.name, registryName, updatedRegistryName);

        registries = await issuerClient.registries().list(issuerAid.name);
        const updateRegistry: { name: string; regk: string } = registries[0];
        assert.equal(registries.length, 1);
        assert.equal(updateRegistry.name, updatedRegistryName);

        return updateRegistry;
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

        const issResult = await issuerClient
            .credentials()
            .issue(issuerAid.name, {
                ri: registry.regk,
                s: QVI_SCHEMA_SAID,
                a: {
                    i: holderAid.prefix,
                    ...vcdata,
                },
            });

        await waitOperation(issuerClient, issResult.op);
        return issResult.acdc.sad.d as string;
    });

    await step('issuer list credentials', async () => {
        const issuerCredentials = await issuerClient.credentials().list();
        assertLength(issuerCredentials, 1);
        assert(issuerCredentials.length >= 1);
        assert.equal(issuerCredentials[0].sad.s, QVI_SCHEMA_SAID);
        assert.equal(issuerCredentials[0].sad.i, issuerAid.prefix);
        assert.equal(issuerCredentials[0].status.s, '0');
    });

    function assertLength(obj: unknown, length: number) {
        assert(obj);
        assert(typeof obj === 'object');
        assert('length' in obj);
        assert.strictEqual(obj.length, length);
    }
    await step('issuer list credentials with filter', async () => {
        assertLength(
            await issuerClient
                .credentials()
                .list({ filter: { '-i': issuerAid.prefix } }),
            1
        );

        assertLength(
            await issuerClient
                .credentials()
                .list({ filter: { '-s': QVI_SCHEMA_SAID } }),
            1
        );

        assertLength(
            await issuerClient
                .credentials()
                .list({ filter: { '-a-i': holderAid.prefix } }),
            1
        );

        assertLength(
            await issuerClient.credentials().list({
                filter: {
                    '-i': issuerAid.prefix,
                    '-s': QVI_SCHEMA_SAID,
                    '-a-i': holderAid.prefix,
                },
            }),
            1
        );

        assertLength(
            await issuerClient.credentials().list({
                filter: {
                    '-i': randomUUID(),
                    '-s': QVI_SCHEMA_SAID,
                    '-a-i': holderAid.prefix,
                },
            }),
            0
        );
    });

    await step('issuer get credential by id', async () => {
        const issuerCredential = await issuerClient
            .credentials()
            .get(qviCredentialId);
        assert(issuerCredential !== undefined);
        assert.equal(issuerCredential.sad.s, QVI_SCHEMA_SAID);
        assert.equal(issuerCredential.sad.i, issuerAid.prefix);
        assert.equal(issuerCredential.status.s, '0');
    });

    await step('issuer IPEX grant', async () => {
        const dt = createTimestamp();
        const issuerCredential = await issuerClient
            .credentials()
            .get(qviCredentialId);
        assert(issuerCredential !== undefined);

        const [grant, gsigs, gend] = await issuerClient.ipex().grant({
            senderName: issuerAid.name,
            acdc: new Serder(issuerCredential.sad),
            anc: new Serder(issuerCredential.anc),
            iss: new Serder(issuerCredential.iss),
            ancAttachment: issuerCredential.ancatc,
            recipient: holderAid.prefix,
            datetime: dt,
        });

        const op = await issuerClient
            .ipex()
            .submitGrant(issuerAid.name, grant, gsigs, gend, [
                holderAid.prefix,
            ]);
        await waitOperation(issuerClient, op);
    });

    await step(
        'holder can get the credential status before or without holding',
        async () => {
            const state = await retry(async () =>
                holderClient.credentials().state(registry.regk, qviCredentialId)
            );
            assert.equal(state.i, qviCredentialId);
            assert.equal(state.ri, registry.regk);
            assert.equal(state.et, Ilks.iss);
        }
    );

    await step('holder IPEX admit', async () => {
        const holderNotifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/grant'
        );
        const grantNotification = holderNotifications[0]; // should only have one notification right now

        const [admit, sigs, aend] = await holderClient.ipex().admit({
            senderName: holderAid.name,
            message: '',
            grantSaid: grantNotification.a.d!,
            recipient: issuerAid.prefix,
            datetime: createTimestamp(),
        });
        const op = await holderClient
            .ipex()
            .submitAdmit(holderAid.name, admit, sigs, aend, [issuerAid.prefix]);
        await waitOperation(holderClient, op);

        await markAndRemoveNotification(holderClient, grantNotification);
    });

    await step('issuer IPEX grant response', async () => {
        const issuerNotifications = await waitForNotifications(
            issuerClient,
            '/exn/ipex/admit'
        );
        await markAndRemoveNotification(issuerClient, issuerNotifications[0]);
    });

    await step('holder has credential', async () => {
        const holderCredential = await retry(async () => {
            const result = await holderClient
                .credentials()
                .get(qviCredentialId);
            assert(result !== undefined);
            return result;
        });
        assert.equal(holderCredential.sad.s, QVI_SCHEMA_SAID);
        assert.equal(holderCredential.sad.i, issuerAid.prefix);
        assert.equal(holderCredential.status.s, '0');
        assert(holderCredential.atc !== undefined);
    });

    await step('verifier IPEX apply', async () => {
        const [apply, sigs, _] = await verifierClient.ipex().apply({
            senderName: verifierAid.name,
            schemaSaid: QVI_SCHEMA_SAID,
            attributes: { LEI: '5493001KJTIIGC8Y1R17' },
            recipient: holderAid.prefix,
            datetime: createTimestamp(),
        });

        const op = await verifierClient
            .ipex()
            .submitApply(verifierAid.name, apply, sigs, [holderAid.prefix]);
        await waitOperation(verifierClient, op);
    });

    await step('holder IPEX apply receive and offer', async () => {
        const holderNotifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/apply'
        );

        const holderApplyNote = holderNotifications[0];
        assert(holderApplyNote.a.d);

        const apply = await holderClient.exchanges().get(holderApplyNote.a.d);
        applySaid = apply.exn.d;

        const filter: { [x: string]: any } = { '-s': apply.exn.a.s };
        for (const key in apply.exn.a.a) {
            filter[`-a-${key}`] = apply.exn.a.a[key];
        }

        const matchingCreds = await holderClient.credentials().list({ filter });
        assert.strictEqual(matchingCreds.length, 1);

        await markAndRemoveNotification(holderClient, holderNotifications[0]);

        const [offer, sigs, end] = await holderClient.ipex().offer({
            senderName: holderAid.name,
            recipient: verifierAid.prefix,
            acdc: new Serder(matchingCreds[0].sad),
            applySaid: applySaid,
            datetime: createTimestamp(),
        });

        const op = await holderClient
            .ipex()
            .submitOffer(holderAid.name, offer, sigs, end, [
                verifierAid.prefix,
            ]);
        await waitOperation(holderClient, op);
    });

    await step('verifier receive offer and agree', async () => {
        const verifierNotifications = await waitForNotifications(
            verifierClient,
            '/exn/ipex/offer'
        );

        const verifierOfferNote = verifierNotifications[0];
        assert(verifierOfferNote.a.d);

        const offer = await verifierClient
            .exchanges()
            .get(verifierOfferNote.a.d);
        offerSaid = offer.exn.d;

        assert.strictEqual(offer.exn.p, applySaid);
        assert.strictEqual(offer.exn.e.acdc.a.LEI, '5493001KJTIIGC8Y1R17');

        await markAndRemoveNotification(verifierClient, verifierOfferNote);

        const [agree, sigs, _] = await verifierClient.ipex().agree({
            senderName: verifierAid.name,
            recipient: holderAid.prefix,
            offerSaid: offerSaid,
            datetime: createTimestamp(),
        });

        const op = await verifierClient
            .ipex()
            .submitAgree(verifierAid.name, agree, sigs, [holderAid.prefix]);
        await waitOperation(verifierClient, op);
    });

    await step('holder IPEX receive agree and grant/present', async () => {
        const holderNotifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/agree'
        );

        const holderAgreeNote = holderNotifications[0];
        assert(holderAgreeNote.a.d);

        const agree = await holderClient.exchanges().get(holderAgreeNote.a.d);
        agreeSaid = agree.exn.d;

        assert.strictEqual(agree.exn.p, offerSaid);

        await markAndRemoveNotification(holderClient, holderAgreeNote);

        const holderCredential = await holderClient
            .credentials()
            .get(qviCredentialId);

        const [grant2, gsigs2, gend2] = await holderClient.ipex().grant({
            senderName: holderAid.name,
            recipient: verifierAid.prefix,
            acdc: new Serder(holderCredential.sad),
            anc: new Serder(holderCredential.anc),
            iss: new Serder(holderCredential.iss),
            acdcAttachment: holderCredential.atc,
            ancAttachment: holderCredential.ancatc,
            issAttachment: holderCredential.issatc,
            agreeSaid: agreeSaid,
            datetime: createTimestamp(),
        });

        const op = await holderClient
            .ipex()
            .submitGrant(holderAid.name, grant2, gsigs2, gend2, [
                verifierAid.prefix,
            ]);
        await waitOperation(holderClient, op);
    });

    await step('verifier receives IPEX grant', async () => {
        const verifierNotifications = await waitForNotifications(
            verifierClient,
            '/exn/ipex/grant'
        );

        const verifierGrantNote = verifierNotifications[0];
        assert(verifierGrantNote.a.d);

        const grant = await holderClient.exchanges().get(verifierGrantNote.a.d);
        assert.strictEqual(grant.exn.p, agreeSaid);

        const [admit3, sigs3, aend3] = await verifierClient.ipex().admit({
            senderName: verifierAid.name,
            message: '',
            grantSaid: verifierGrantNote.a.d!,
            recipient: holderAid.prefix,
            datetime: createTimestamp(),
        });

        const op = await verifierClient
            .ipex()
            .submitAdmit(verifierAid.name, admit3, sigs3, aend3, [
                holderAid.prefix,
            ]);
        await waitOperation(verifierClient, op);

        await markAndRemoveNotification(verifierClient, verifierGrantNote);

        const verifierCredential = await retry(async () =>
            verifierClient.credentials().get(qviCredentialId)
        );

        assert.equal(verifierCredential.sad.s, QVI_SCHEMA_SAID);
        assert.equal(verifierCredential.sad.i, issuerAid.prefix);
        assert.equal(verifierCredential.status.s, '0'); // 0 = issued
    });

    await step('holder IPEX present response', async () => {
        const holderNotifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/admit'
        );

        await markAndRemoveNotification(holderClient, holderNotifications[0]);
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
                .get(qviCredentialId);

            const result = await holderClient
                .credentials()
                .issue(holderAid.name, {
                    a: {
                        i: legalEntityAid.prefix,
                        LEI: '5493001KJTIIGC8Y1R17',
                    },
                    ri: holderRegistry.regk,
                    s: LE_SCHEMA_SAID,
                    r: Saider.saidify({
                        d: '',
                        usageDisclaimer: {
                            l: 'Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with any laws or that an implied or expressly intended purpose will be fulfilled.',
                        },
                        issuanceDisclaimer: {
                            l: 'All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the validation process was complete. The vLEI Credential has been issued to the legal entity or person named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set forth in the vLEI Ecosystem Governance Framework.',
                        },
                    })[1],
                    e: Saider.saidify({
                        d: '',
                        qvi: {
                            n: qviCredential.sad.d,
                            s: qviCredential.sad.s,
                        },
                    })[1],
                });

            await waitOperation(holderClient, result.op);
            return result.acdc.sad.d;
        }
    );

    await step('LE credential IPEX grant', async () => {
        const dt = createTimestamp();
        const leCredential = await holderClient
            .credentials()
            .get(leCredentialId);
        assert(leCredential !== undefined);

        const [grant, gsigs, gend] = await holderClient.ipex().grant({
            senderName: holderAid.name,
            acdc: new Serder(leCredential.sad),
            anc: new Serder(leCredential.anc),
            iss: new Serder(leCredential.iss),
            ancAttachment: leCredential.ancatc,
            recipient: legalEntityAid.prefix,
            datetime: dt,
        });

        const op = await holderClient
            .ipex()
            .submitGrant(holderAid.name, grant, gsigs, gend, [
                legalEntityAid.prefix,
            ]);
        await waitOperation(holderClient, op);
    });

    await step('Legal Entity IPEX admit', async () => {
        const notifications = await waitForNotifications(
            legalEntityClient,
            '/exn/ipex/grant'
        );
        const grantNotification = notifications[0];

        const [admit, sigs, aend] = await legalEntityClient.ipex().admit({
            senderName: legalEntityAid.name,
            message: '',
            grantSaid: grantNotification.a.d!,
            recipient: holderAid.prefix,
            datetime: createTimestamp(),
        });

        const op = await legalEntityClient
            .ipex()
            .submitAdmit(legalEntityAid.name, admit, sigs, aend, [
                holderAid.prefix,
            ]);
        await waitOperation(legalEntityClient, op);

        await markAndRemoveNotification(legalEntityClient, grantNotification);
    });

    await step('LE credential IPEX grant response', async () => {
        const notifications = await waitForNotifications(
            holderClient,
            '/exn/ipex/admit'
        );
        await markAndRemoveNotification(holderClient, notifications[0]);
    });

    await step('Legal Entity has chained credential', async () => {
        const legalEntityCredential = await retry(async () =>
            legalEntityClient.credentials().get(leCredentialId)
        );
        assert.equal(legalEntityCredential.sad.s, LE_SCHEMA_SAID);
        assert.equal(legalEntityCredential.sad.i, holderAid.prefix);

        if (
            'a' in legalEntityCredential.sad &&
            legalEntityCredential.sad.a !== undefined
        ) {
            assert.equal(legalEntityCredential.sad.a !== undefined, true);
            assert.equal(legalEntityCredential.sad.a.i, legalEntityAid.prefix);
        }

        assert.equal(legalEntityCredential.status.s, '0');
        assert(Array.isArray(legalEntityCredential.chains));
        assert(legalEntityCredential.chains.length > 0);
        const firstChain = legalEntityCredential.chains[0] as {
            sad: { d: string };
        };
        assert.equal(firstChain.sad.d, qviCredentialId);
        assert(legalEntityCredential.atc !== undefined);
    });

    await step('Issuer revoke QVI credential', async () => {
        const revokeOperation = await issuerClient
            .credentials()
            .revoke(issuerAid.name, qviCredentialId);

        await waitOperation(issuerClient, revokeOperation.op);
        const issuerCredential = await issuerClient
            .credentials()
            .get(qviCredentialId);

        assert.equal(issuerCredential.status.s, '1');
    });

    await step('Holder deletes LE credential', async () => {
        await holderClient.credentials().delete(leCredentialId);
        await expect(async () => {
            await holderClient.credentials().get(leCredentialId);
        }).rejects.toThrowError(
            `HTTP GET /credentials/${leCredentialId} - 404 Not Found - {"title": "404 Not Found", "description": "credential for said ${leCredentialId} not found."}`
        );

        assert.equal((await holderClient.credentials().list()).length, 1);
    });
});
