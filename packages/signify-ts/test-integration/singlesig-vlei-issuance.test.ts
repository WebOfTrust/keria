import { assert, test } from 'vitest';
import { Saider, Serder, SignifyClient } from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env.ts';
import {
    Aid,
    assertOperations,
    createAid,
    getOrCreateClients,
    getOrCreateContact,
    getOrIssueCredential,
    getReceivedCredential,
    markAndRemoveNotification,
    resolveOobi,
    waitForNotifications,
    waitOperation,
    warnNotifications,
} from './utils/test-util.ts';
import { retry } from './utils/retry.ts';

const { vleiServerUrl } = resolveEnvironment();

const QVI_SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const LE_SCHEMA_SAID = 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY';
const ECR_AUTH_SCHEMA_SAID = 'EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g';
const ECR_SCHEMA_SAID = 'EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw';
const OOR_AUTH_SCHEMA_SAID = 'EKA57bKBKxr_kN7iN5i7lMUxpMG-s19dRcmov1iDxz-E';
const OOR_SCHEMA_SAID = 'EBNaNu-M9P5cgrnfl2Fvymy4E_jvxxyjb70PRtiANlJy';

const vLEIServerHostUrl = `${vleiServerUrl}/oobi`;
const QVI_SCHEMA_URL = `${vLEIServerHostUrl}/${QVI_SCHEMA_SAID}`;
const LE_SCHEMA_URL = `${vLEIServerHostUrl}/${LE_SCHEMA_SAID}`;
const ECR_AUTH_SCHEMA_URL = `${vLEIServerHostUrl}/${ECR_AUTH_SCHEMA_SAID}`;
const ECR_SCHEMA_URL = `${vLEIServerHostUrl}/${ECR_SCHEMA_SAID}`;
const OOR_AUTH_SCHEMA_URL = `${vLEIServerHostUrl}/${OOR_AUTH_SCHEMA_SAID}`;
const OOR_SCHEMA_URL = `${vLEIServerHostUrl}/${OOR_SCHEMA_SAID}`;

const qviData = {
    LEI: '254900OPPU84GM83MG36',
};

const leData = {
    LEI: '875500ELOZEL05BVXV37',
};

const ecrData = {
    LEI: leData.LEI,
    personLegalName: 'John Doe',
    engagementContextRole: 'EBA Data Submitter',
};

const ecrAuthData = {
    AID: '',
    LEI: ecrData.LEI,
    personLegalName: ecrData.personLegalName,
    engagementContextRole: ecrData.engagementContextRole,
};

const oorData = {
    LEI: leData.LEI,
    personLegalName: 'John Doe',
    officialRole: 'HR Manager',
};

const oorAuthData = {
    AID: '',
    LEI: oorData.LEI,
    personLegalName: oorData.personLegalName,
    officialRole: oorData.officialRole,
};

const LE_RULES = Saider.saidify({
    d: '',
    usageDisclaimer: {
        l: 'Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with any laws or that an implied or expressly intended purpose will be fulfilled.',
    },
    issuanceDisclaimer: {
        l: 'All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the validation process was complete. The vLEI Credential has been issued to the legal entity or person named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set forth in the vLEI Ecosystem Governance Framework.',
    },
})[1];

const ECR_RULES = Saider.saidify({
    d: '',
    usageDisclaimer: {
        l: 'Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with any laws or that an implied or expressly intended purpose will be fulfilled.',
    },
    issuanceDisclaimer: {
        l: 'All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the validation process was complete. The vLEI Credential has been issued to the legal entity or person named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set forth in the vLEI Ecosystem Governance Framework.',
    },
    privacyDisclaimer: {
        l: 'It is the sole responsibility of Holders as Issuees of an ECR vLEI Credential to present that Credential in a privacy-preserving manner using the mechanisms provided in the Issuance and Presentation Exchange (IPEX) protocol specification and the Authentic Chained Data Container (ACDC) specification. https://github.com/WebOfTrust/IETF-IPEX and https://github.com/trustoverip/tswg-acdc-specification.',
    },
})[1];

const ECR_AUTH_RULES = Saider.saidify({
    d: '',
    usageDisclaimer: {
        l: 'Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, does not assert that the Legal Entity is trustworthy, honest, reputable in its business dealings, safe to do business with, or compliant with any laws or that an implied or expressly intended purpose will be fulfilled.',
    },
    issuanceDisclaimer: {
        l: 'All information in a valid, unexpired, and non-revoked vLEI Credential, as defined in the associated Ecosystem Governance Framework, is accurate as of the date the validation process was complete. The vLEI Credential has been issued to the legal entity or person named in the vLEI Credential as the subject; and the qualified vLEI Issuer exercised reasonable care to perform the validation process set forth in the vLEI Ecosystem Governance Framework.',
    },
    privacyDisclaimer: {
        l: 'Privacy Considerations are applicable to QVI ECR AUTH vLEI Credentials.  It is the sole responsibility of QVIs as Issuees of QVI ECR AUTH vLEI Credentials to present these Credentials in a privacy-preserving manner using the mechanisms provided in the Issuance and Presentation Exchange (IPEX) protocol specification and the Authentic Chained Data Container (ACDC) specification.  https://github.com/WebOfTrust/IETF-IPEX and https://github.com/trustoverip/tswg-acdc-specification.',
    },
})[1];

const OOR_RULES = LE_RULES;
const OOR_AUTH_RULES = LE_RULES;

const CRED_RETRY_DEFAULTS = {
    maxSleep: 10000,
    minSleep: 1000,
    maxRetries: undefined,
    timeout: 30000,
};

function createTimestamp() {
    return new Date().toISOString().replace('Z', '000+00:00');
}

test('singlesig-vlei-issuance', async function run() {
    const [gleifClient, qviClient, leClient, roleClient] =
        await getOrCreateClients(4);

    const [gleifAid, qviAid, leAid, roleAid] = await Promise.all([
        createAid(gleifClient, 'gleif'),
        createAid(qviClient, 'qvi'),
        createAid(leClient, 'le'),
        createAid(roleClient, 'role'),
    ]);

    await Promise.all([
        getOrCreateContact(gleifClient, 'qvi', qviAid.oobi),
        getOrCreateContact(qviClient, 'gleif', gleifAid.oobi),
        getOrCreateContact(qviClient, 'le', leAid.oobi),
        getOrCreateContact(qviClient, 'role', roleAid.oobi),
        getOrCreateContact(leClient, 'gleif', gleifAid.oobi),
        getOrCreateContact(leClient, 'qvi', qviAid.oobi),
        getOrCreateContact(leClient, 'role', roleAid.oobi),
        getOrCreateContact(roleClient, 'gleif', gleifAid.oobi),
        getOrCreateContact(roleClient, 'qvi', qviAid.oobi),
        getOrCreateContact(roleClient, 'le', leAid.oobi),
    ]);

    await Promise.all([
        resolveOobi(gleifClient, QVI_SCHEMA_URL),
        resolveOobi(qviClient, QVI_SCHEMA_URL),
        resolveOobi(qviClient, LE_SCHEMA_URL),
        resolveOobi(qviClient, ECR_AUTH_SCHEMA_URL),
        resolveOobi(qviClient, ECR_SCHEMA_URL),
        resolveOobi(qviClient, OOR_AUTH_SCHEMA_URL),
        resolveOobi(qviClient, OOR_SCHEMA_URL),
        resolveOobi(leClient, QVI_SCHEMA_URL),
        resolveOobi(leClient, LE_SCHEMA_URL),
        resolveOobi(leClient, ECR_AUTH_SCHEMA_URL),
        resolveOobi(leClient, ECR_SCHEMA_URL),
        resolveOobi(leClient, OOR_AUTH_SCHEMA_URL),
        resolveOobi(leClient, OOR_SCHEMA_URL),
        resolveOobi(roleClient, QVI_SCHEMA_URL),
        resolveOobi(roleClient, LE_SCHEMA_URL),
        resolveOobi(roleClient, ECR_AUTH_SCHEMA_URL),
        resolveOobi(roleClient, ECR_SCHEMA_URL),
        resolveOobi(roleClient, OOR_AUTH_SCHEMA_URL),
        resolveOobi(roleClient, OOR_SCHEMA_URL),
    ]);

    const [gleifRegistry, qviRegistry, leRegistry] = await Promise.all([
        getOrCreateRegistry(gleifClient, gleifAid, 'gleifRegistry'),
        getOrCreateRegistry(qviClient, qviAid, 'qviRegistry'),
        getOrCreateRegistry(leClient, leAid, 'leRegistry'),
    ]);

    console.log('Issuing QVI vLEI Credential');
    const qviCred = await getOrIssueCredential(
        gleifClient,
        gleifAid,
        qviAid,
        gleifRegistry,
        qviData,
        QVI_SCHEMA_SAID
    );

    let qviCredHolder = await getReceivedCredential(qviClient, qviCred.sad.d);

    if (!qviCredHolder) {
        await sendGrantMessage(gleifClient, gleifAid, qviAid, qviCred);
        await sendAdmitMessage(qviClient, qviAid, gleifAid);

        qviCredHolder = await retry(async () => {
            const cred = await getReceivedCredential(qviClient, qviCred.sad.d);
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(qviCredHolder.sad.d, qviCred.sad.d);
    assert.equal(qviCredHolder.sad.s, QVI_SCHEMA_SAID);
    assert.equal(qviCredHolder.sad.i, gleifAid.prefix);
    assert.equal(qviCredHolder.sad.a.i, qviAid.prefix);
    assert.equal(qviCredHolder.status.s, '0');
    assert(qviCredHolder.atc !== undefined);

    console.log('Issuing LE vLEI Credential');
    const leCredSource = Saider.saidify({
        d: '',
        qvi: {
            n: qviCred.sad.d,
            s: qviCred.sad.s,
        },
    })[1];

    const leCred = await getOrIssueCredential(
        qviClient,
        qviAid,
        leAid,
        qviRegistry,
        leData,
        LE_SCHEMA_SAID,
        LE_RULES,
        leCredSource
    );

    let leCredHolder = await getReceivedCredential(leClient, leCred.sad.d);

    if (!leCredHolder) {
        await sendGrantMessage(qviClient, qviAid, leAid, leCred);
        await sendAdmitMessage(leClient, leAid, qviAid);

        leCredHolder = await retry(async () => {
            const cred = await getReceivedCredential(leClient, leCred.sad.d);
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(leCredHolder.sad.d, leCred.sad.d);
    assert.equal(leCredHolder.sad.s, LE_SCHEMA_SAID);
    assert.equal(leCredHolder.sad.i, qviAid.prefix);
    assert.equal(leCredHolder.sad.a.i, leAid.prefix);
    assert.equal(leCredHolder.sad.e.qvi.n, qviCred.sad.d);
    assert.equal(leCredHolder.status.s, '0');
    assert(leCredHolder.atc !== undefined);

    console.log('Issuing ECR vLEI Credential from LE');
    const ecrCredSource = Saider.saidify({
        d: '',
        le: {
            n: leCred.sad.d,
            s: leCred.sad.s,
        },
    })[1];

    const ecrCred = await getOrIssueCredential(
        leClient,
        leAid,
        roleAid,
        leRegistry,
        ecrData,
        ECR_SCHEMA_SAID,
        ECR_RULES,
        ecrCredSource,
        true
    );

    let ecrCredHolder = await getReceivedCredential(roleClient, ecrCred.sad.d);

    if (!ecrCredHolder) {
        await sendGrantMessage(leClient, leAid, roleAid, ecrCred);
        await sendAdmitMessage(roleClient, roleAid, leAid);

        ecrCredHolder = await retry(async () => {
            const cred = await getReceivedCredential(roleClient, ecrCred.sad.d);
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(ecrCredHolder.sad.d, ecrCred.sad.d);
    assert.equal(ecrCredHolder.sad.s, ECR_SCHEMA_SAID);
    assert.equal(ecrCredHolder.sad.i, leAid.prefix);
    assert.equal(ecrCredHolder.sad.a.i, roleAid.prefix);
    assert.equal(ecrCredHolder.sad.e.le.n, leCred.sad.d);
    assert.equal(ecrCredHolder.status.s, '0');
    assert(ecrCredHolder.atc !== undefined);

    console.log('Issuing ECR AUTH vLEI Credential');
    ecrAuthData.AID = roleAid.prefix;
    const ecrAuthCredSource = Saider.saidify({
        d: '',
        le: {
            n: leCred.sad.d,
            s: leCred.sad.s,
        },
    })[1];

    const ecrAuthCred = await getOrIssueCredential(
        leClient,
        leAid,
        qviAid,
        leRegistry,
        ecrAuthData,
        ECR_AUTH_SCHEMA_SAID,
        ECR_AUTH_RULES,
        ecrAuthCredSource
    );

    let ecrAuthCredHolder = await getReceivedCredential(
        qviClient,
        ecrAuthCred.sad.d
    );

    if (!ecrAuthCredHolder) {
        await sendGrantMessage(leClient, leAid, qviAid, ecrAuthCred);
        await sendAdmitMessage(qviClient, qviAid, leAid);

        ecrAuthCredHolder = await retry(async () => {
            const cred = await getReceivedCredential(
                qviClient,
                ecrAuthCred.sad.d
            );
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(ecrAuthCredHolder.sad.d, ecrAuthCred.sad.d);
    assert.equal(ecrAuthCredHolder.sad.s, ECR_AUTH_SCHEMA_SAID);
    assert.equal(ecrAuthCredHolder.sad.i, leAid.prefix);
    assert.equal(ecrAuthCredHolder.sad.a.i, qviAid.prefix);
    assert.equal(ecrAuthCredHolder.sad.a.AID, roleAid.prefix);
    assert.equal(ecrAuthCredHolder.sad.e.le.n, leCred.sad.d);
    assert.equal(ecrAuthCredHolder.status.s, '0');
    assert(ecrAuthCredHolder.atc !== undefined);

    console.log('Issuing ECR vLEI Credential from ECR AUTH');
    const ecrCredSource2 = Saider.saidify({
        d: '',
        auth: {
            n: ecrAuthCred.sad.d,
            s: ecrAuthCred.sad.s,
            o: 'I2I',
        },
    })[1];

    const ecrCred2 = await getOrIssueCredential(
        qviClient,
        qviAid,
        roleAid,
        qviRegistry,
        ecrData,
        ECR_SCHEMA_SAID,
        ECR_RULES,
        ecrCredSource2,
        true
    );

    let ecrCredHolder2 = await getReceivedCredential(
        roleClient,
        ecrCred2.sad.d
    );

    if (!ecrCredHolder2) {
        await sendGrantMessage(qviClient, qviAid, roleAid, ecrCred2);
        await sendAdmitMessage(roleClient, roleAid, qviAid);

        ecrCredHolder2 = await retry(async () => {
            const cred = await getReceivedCredential(
                roleClient,
                ecrCred2.sad.d
            );
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(ecrCredHolder2.sad.d, ecrCred2.sad.d);
    assert.equal(ecrCredHolder2.sad.s, ECR_SCHEMA_SAID);
    assert.equal(ecrCredHolder2.sad.i, qviAid.prefix);
    assert.equal(ecrCredHolder2.sad.e.auth.n, ecrAuthCred.sad.d);
    assert.equal(ecrCredHolder2.status.s, '0');
    assert(ecrCredHolder2.atc !== undefined);

    console.log('Issuing OOR AUTH vLEI Credential');
    oorAuthData.AID = roleAid.prefix;
    const oorAuthCredSource = Saider.saidify({
        d: '',
        le: {
            n: leCred.sad.d,
            s: leCred.sad.s,
        },
    })[1];

    const oorAuthCred = await getOrIssueCredential(
        leClient,
        leAid,
        qviAid,
        leRegistry,
        oorAuthData,
        OOR_AUTH_SCHEMA_SAID,
        OOR_AUTH_RULES,
        oorAuthCredSource
    );

    let oorAuthCredHolder = await getReceivedCredential(
        qviClient,
        oorAuthCred.sad.d
    );

    if (!oorAuthCredHolder) {
        await sendGrantMessage(leClient, leAid, qviAid, oorAuthCred);
        await sendAdmitMessage(qviClient, qviAid, leAid);

        oorAuthCredHolder = await retry(async () => {
            const cred = await getReceivedCredential(
                qviClient,
                oorAuthCred.sad.d
            );
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(oorAuthCredHolder.sad.d, oorAuthCred.sad.d);
    assert.equal(oorAuthCredHolder.sad.s, OOR_AUTH_SCHEMA_SAID);
    assert.equal(oorAuthCredHolder.sad.i, leAid.prefix);
    assert.equal(oorAuthCredHolder.sad.a.i, qviAid.prefix);
    assert.equal(oorAuthCredHolder.sad.a.AID, roleAid.prefix);
    assert.equal(oorAuthCredHolder.sad.e.le.n, leCred.sad.d);
    assert.equal(oorAuthCredHolder.status.s, '0');
    assert(oorAuthCredHolder.atc !== undefined);

    console.log('Issuing OOR vLEI Credential from OOR AUTH');
    const oorCredSource = Saider.saidify({
        d: '',
        auth: {
            n: oorAuthCred.sad.d,
            s: oorAuthCred.sad.s,
            o: 'I2I',
        },
    })[1];

    const oorCred = await getOrIssueCredential(
        qviClient,
        qviAid,
        roleAid,
        qviRegistry,
        oorData,
        OOR_SCHEMA_SAID,
        OOR_RULES,
        oorCredSource
    );

    let oorCredHolder = await getReceivedCredential(roleClient, oorCred.sad.d);

    if (!oorCredHolder) {
        await sendGrantMessage(qviClient, qviAid, roleAid, oorCred);
        await sendAdmitMessage(roleClient, roleAid, qviAid);

        oorCredHolder = await retry(async () => {
            const cred = await getReceivedCredential(roleClient, oorCred.sad.d);
            assert(cred !== undefined);
            return cred;
        }, CRED_RETRY_DEFAULTS);
    }

    assert.equal(oorCredHolder.sad.d, oorCred.sad.d);
    assert.equal(oorCredHolder.sad.s, OOR_SCHEMA_SAID);
    assert.equal(oorCredHolder.sad.i, qviAid.prefix);
    assert.equal(oorCredHolder.sad.e.auth.n, oorAuthCred.sad.d);
    assert.equal(oorCredHolder.status.s, '0');
    assert(oorCredHolder.atc !== undefined);

    await assertOperations(gleifClient, qviClient, leClient, roleClient);
    await warnNotifications(gleifClient, qviClient, leClient, roleClient);
}, 360000);

async function getOrCreateRegistry(
    client: SignifyClient,
    aid: Aid,
    registryName: string
): Promise<{ name: string; regk: string }> {
    let registries = await client.registries().list(aid.name);
    if (registries.length > 0) {
        assert.equal(registries.length, 1);
    } else {
        const regResult = await client
            .registries()
            .create({ name: aid.name, registryName: registryName });
        await waitOperation(client, await regResult.op());
        registries = await client.registries().list(aid.name);
    }
    return registries[0];
}

async function sendGrantMessage(
    senderClient: SignifyClient,
    senderAid: Aid,
    recipientAid: Aid,
    credential: any
) {
    const [grant, gsigs, gend] = await senderClient.ipex().grant({
        senderName: senderAid.name,
        acdc: new Serder(credential.sad),
        anc: new Serder(credential.anc),
        iss: new Serder(credential.iss),
        ancAttachment: credential.ancAttachment,
        recipient: recipientAid.prefix,
        datetime: createTimestamp(),
    });

    let op = await senderClient
        .ipex()
        .submitGrant(senderAid.name, grant, gsigs, gend, [recipientAid.prefix]);
    op = await waitOperation(senderClient, op);
}

async function sendAdmitMessage(
    senderClient: SignifyClient,
    senderAid: Aid,
    recipientAid: Aid
) {
    const notifications = await waitForNotifications(
        senderClient,
        '/exn/ipex/grant'
    );
    assert.equal(notifications.length, 1);
    const grantNotification = notifications[0];

    const [admit, sigs, aend] = await senderClient.ipex().admit({
        senderName: senderAid.name,
        message: '',
        grantSaid: grantNotification.a.d!,
        recipient: recipientAid.prefix,
        datetime: createTimestamp(),
    });

    let op = await senderClient
        .ipex()
        .submitAdmit(senderAid.name, admit, sigs, aend, [recipientAid.prefix]);
    op = await waitOperation(senderClient, op);

    await markAndRemoveNotification(senderClient, grantNotification);
}
