import { strict as assert } from 'assert';
import signify, {
    SignifyClient,
    Saider,
    Serder,
    CredentialSubject,
    CredentialData,
    CreateIdentiferArgs,
    EventResult,
    randomNonce,
    Salter,
} from 'signify-ts';
import { resolveEnvironment } from './utils/resolve-env';
import {
    resolveOobi,
    waitOperation,
    waitForNotifications,
} from './utils/test-util';
import { getOrCreateClients, getOrCreateContact } from './utils/test-setup';
import { HabState } from '../../src/keri/core/state';

const { vleiServerUrl, witnessIds } = resolveEnvironment();

const QVI_SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const LE_SCHEMA_SAID = 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY';
const ECR_SCHEMA_SAID = 'EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw';

const vLEIServerHostUrl = `${vleiServerUrl}/oobi`;
const QVI_SCHEMA_URL = `${vLEIServerHostUrl}/${QVI_SCHEMA_SAID}`;
const LE_SCHEMA_URL = `${vLEIServerHostUrl}/${LE_SCHEMA_SAID}`;
const ECR_SCHEMA_URL = `${vLEIServerHostUrl}/${ECR_SCHEMA_SAID}`;

const qviData = {
    LEI: '254900OPPU84GM83MG36',
};

const leData = {
    LEI: '875500ELOZEL05BVXV37',
};

const ecrData = {
    LEI: leData.LEI,
    personLegalName: 'John Doe',
    engagementContextRole: 'EBA Submitter',
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

test('multisig-vlei-issuance', async function run() {
    /**
     * The abbreviations used in this script follows GLEIF vLEI
     * ecosystem governance framework (EGF).
     *      GEDA: GLEIF External Delegated AID
     *      QVI:  Qualified vLEI Issuer
     *      LE:   Legal Entity
     *      GAR:  GLEIF Authorized Representative
     *      QAR:  Qualified vLEI Issuer Authorized Representative
     *      LAR:  Legal Entity Authorized Representative
     *      ECR:  Engagement Context Role Person
     */

    const [
        clientGAR1,
        clientGAR2,
        clientQAR1,
        clientQAR2,
        clientQAR3,
        clientLAR1,
        clientLAR2,
        clientLAR3,
        clientECR,
    ] = await getOrCreateClients(9);

    const kargsAID = {
        toad: witnessIds.length,
        wits: witnessIds,
    };
    const [
        aidGAR1,
        aidGAR2,
        aidQAR1,
        aidQAR2,
        aidQAR3,
        aidLAR1,
        aidLAR2,
        aidLAR3,
        aidECR,
    ] = await Promise.all([
        getOrCreateAID(clientGAR1, 'GAR1', kargsAID),
        getOrCreateAID(clientGAR2, 'GAR2', kargsAID),
        getOrCreateAID(clientQAR1, 'QAR1', kargsAID),
        getOrCreateAID(clientQAR2, 'QAR2', kargsAID),
        getOrCreateAID(clientQAR3, 'QAR3', kargsAID),
        getOrCreateAID(clientLAR1, 'LAR1', kargsAID),
        getOrCreateAID(clientLAR2, 'LAR2', kargsAID),
        getOrCreateAID(clientLAR3, 'LAR3', kargsAID),
        getOrCreateAID(clientECR, 'ECR', kargsAID),
    ]);

    const [
        oobiGAR1,
        oobiGAR2,
        oobiQAR1,
        oobiQAR2,
        oobiQAR3,
        oobiLAR1,
        oobiLAR2,
        oobiLAR3,
        oobiECR,
    ] = await Promise.all([
        clientGAR1.oobis().get('GAR1', 'agent'),
        clientGAR2.oobis().get('GAR2', 'agent'),
        clientQAR1.oobis().get('QAR1', 'agent'),
        clientQAR2.oobis().get('QAR2', 'agent'),
        clientQAR3.oobis().get('QAR3', 'agent'),
        clientLAR1.oobis().get('LAR1', 'agent'),
        clientLAR2.oobis().get('LAR2', 'agent'),
        clientLAR3.oobis().get('LAR3', 'agent'),
        clientECR.oobis().get('ECR', 'agent'),
    ]);

    await Promise.all([
        getOrCreateContact(clientGAR1, 'GAR2', oobiGAR2.oobis[0]),
        getOrCreateContact(clientGAR2, 'GAR1', oobiGAR1.oobis[0]),
        getOrCreateContact(clientQAR1, 'QAR2', oobiQAR2.oobis[0]),
        getOrCreateContact(clientQAR1, 'QAR3', oobiQAR3.oobis[0]),
        getOrCreateContact(clientQAR2, 'QAR1', oobiQAR1.oobis[0]),
        getOrCreateContact(clientQAR2, 'QAR3', oobiQAR3.oobis[0]),
        getOrCreateContact(clientQAR3, 'QAR1', oobiQAR1.oobis[0]),
        getOrCreateContact(clientQAR3, 'QAR2', oobiQAR2.oobis[0]),
        getOrCreateContact(clientLAR1, 'LAR2', oobiLAR2.oobis[0]),
        getOrCreateContact(clientLAR1, 'LAR3', oobiLAR3.oobis[0]),
        getOrCreateContact(clientLAR2, 'LAR1', oobiLAR1.oobis[0]),
        getOrCreateContact(clientLAR2, 'LAR3', oobiLAR3.oobis[0]),
        getOrCreateContact(clientLAR3, 'LAR1', oobiLAR1.oobis[0]),
        getOrCreateContact(clientLAR3, 'LAR2', oobiLAR2.oobis[0]),
        getOrCreateContact(clientLAR1, 'ECR', oobiECR.oobis[0]),
        getOrCreateContact(clientLAR2, 'ECR', oobiECR.oobis[0]),
        getOrCreateContact(clientLAR3, 'ECR', oobiECR.oobis[0]),
    ]);

    await Promise.all([
        resolveOobi(clientGAR1, QVI_SCHEMA_URL),
        resolveOobi(clientGAR2, QVI_SCHEMA_URL),
        resolveOobi(clientQAR1, QVI_SCHEMA_URL),
        resolveOobi(clientQAR1, LE_SCHEMA_URL),
        resolveOobi(clientQAR2, QVI_SCHEMA_URL),
        resolveOobi(clientQAR2, LE_SCHEMA_URL),
        resolveOobi(clientQAR3, QVI_SCHEMA_URL),
        resolveOobi(clientQAR3, LE_SCHEMA_URL),
        resolveOobi(clientLAR1, QVI_SCHEMA_URL),
        resolveOobi(clientLAR1, LE_SCHEMA_URL),
        resolveOobi(clientLAR1, ECR_SCHEMA_URL),
        resolveOobi(clientLAR2, QVI_SCHEMA_URL),
        resolveOobi(clientLAR2, LE_SCHEMA_URL),
        resolveOobi(clientLAR2, ECR_SCHEMA_URL),
        resolveOobi(clientLAR3, QVI_SCHEMA_URL),
        resolveOobi(clientLAR3, LE_SCHEMA_URL),
        resolveOobi(clientLAR3, ECR_SCHEMA_URL),
        resolveOobi(clientECR, QVI_SCHEMA_URL),
        resolveOobi(clientECR, LE_SCHEMA_URL),
        resolveOobi(clientECR, ECR_SCHEMA_URL),
    ]);

    // Create a multisig AID for the GEDA.
    // Skip if a GEDA AID has already been incepted.
    let aidGEDAbyGAR1, aidGEDAbyGAR2: HabState;
    try {
        aidGEDAbyGAR1 = await clientGAR1.identifiers().get('GEDA');
        aidGEDAbyGAR2 = await clientGAR2.identifiers().get('GEDA');
    } catch {
        const rstates = [aidGAR1.state, aidGAR2.state];
        const states = rstates;

        const kargsMultisigAID: CreateIdentiferArgs = {
            algo: signify.Algos.group,
            isith: ['1/2', '1/2'],
            nsith: ['1/2', '1/2'],
            toad: kargsAID.toad,
            wits: kargsAID.wits,
            states: states,
            rstates: rstates,
        };

        kargsMultisigAID.mhab = aidGAR1;
        const multisigAIDOp1 = await createAIDMultisig(
            clientGAR1,
            aidGAR1,
            [aidGAR2],
            'GEDA',
            kargsMultisigAID,
            true
        );
        kargsMultisigAID.mhab = aidGAR2;
        const multisigAIDOp2 = await createAIDMultisig(
            clientGAR2,
            aidGAR2,
            [aidGAR1],
            'GEDA',
            kargsMultisigAID
        );

        await Promise.all([
            waitOperation(clientGAR1, multisigAIDOp1),
            waitOperation(clientGAR2, multisigAIDOp2),
        ]);

        await waitAndMarkNotification(clientGAR1, '/multisig/icp');

        aidGEDAbyGAR1 = await clientGAR1.identifiers().get('GEDA');
        aidGEDAbyGAR2 = await clientGAR2.identifiers().get('GEDA');
    }
    assert.equal(aidGEDAbyGAR1.prefix, aidGEDAbyGAR2.prefix);
    assert.equal(aidGEDAbyGAR1.name, aidGEDAbyGAR2.name);
    const aidGEDA = aidGEDAbyGAR1;

    // Add endpoint role authorization for all GARs' agents.
    // Skip if they have already been authorized.
    let [oobiGEDAbyGAR1, oobiGEDAbyGAR2] = await Promise.all([
        clientGAR1.oobis().get(aidGEDA.name, 'agent'),
        clientGAR2.oobis().get(aidGEDA.name, 'agent'),
    ]);
    if (oobiGEDAbyGAR1.oobis.length == 0 || oobiGEDAbyGAR2.oobis.length == 0) {
        const timestamp = createTimestamp();
        const opList1 = await addEndRoleMultisig(
            clientGAR1,
            aidGAR1,
            [aidGAR2],
            aidGEDA,
            timestamp,
            true
        );
        const opList2 = await addEndRoleMultisig(
            clientGAR2,
            aidGAR2,
            [aidGAR1],
            aidGEDA,
            timestamp
        );

        await Promise.all(opList1.map((op) => waitOperation(clientGAR1, op)));
        await Promise.all(opList2.map((op) => waitOperation(clientGAR2, op)));

        await waitAndMarkNotification(clientGAR1, '/multisig/rpy');

        [oobiGEDAbyGAR1, oobiGEDAbyGAR2] = await Promise.all([
            clientGAR1.oobis().get(aidGEDA.name, 'agent'),
            clientGAR2.oobis().get(aidGEDA.name, 'agent'),
        ]);
    }
    assert.equal(oobiGEDAbyGAR1.role, oobiGEDAbyGAR2.role);
    assert.equal(oobiGEDAbyGAR1.oobis[0], oobiGEDAbyGAR2.oobis[0]);

    // QARs, LARs, ECR resolve GEDA's OOBI
    const oobiGEDA = oobiGEDAbyGAR1.oobis[0].split('/agent/')[0];
    await Promise.all([
        getOrCreateContact(clientQAR1, aidGEDA.name, oobiGEDA),
        getOrCreateContact(clientQAR2, aidGEDA.name, oobiGEDA),
        getOrCreateContact(clientQAR3, aidGEDA.name, oobiGEDA),
        getOrCreateContact(clientLAR1, aidGEDA.name, oobiGEDA),
        getOrCreateContact(clientLAR2, aidGEDA.name, oobiGEDA),
        getOrCreateContact(clientLAR3, aidGEDA.name, oobiGEDA),
        getOrCreateContact(clientECR, aidGEDA.name, oobiGEDA),
    ]);

    // Create a multisig AID for the QVI.
    // Skip if a QVI AID has already been incepted.
    let aidQVIbyQAR1, aidQVIbyQAR2, aidQVIbyQAR3: HabState;
    try {
        aidQVIbyQAR1 = await clientQAR1.identifiers().get('QVI');
        aidQVIbyQAR2 = await clientQAR2.identifiers().get('QVI');
        aidQVIbyQAR3 = await clientQAR3.identifiers().get('QVI');
    } catch {
        const rstates = [aidQAR1.state, aidQAR2.state, aidQAR3.state];
        const states = rstates;

        const kargsMultisigAID: CreateIdentiferArgs = {
            algo: signify.Algos.group,
            isith: ['2/3', '1/2', '1/2'],
            nsith: ['2/3', '1/2', '1/2'],
            toad: kargsAID.toad,
            wits: kargsAID.wits,
            states: states,
            rstates: rstates,
            delpre: aidGEDA.prefix,
        };

        kargsMultisigAID.mhab = aidQAR1;
        const multisigAIDOp1 = await createAIDMultisig(
            clientQAR1,
            aidQAR1,
            [aidQAR2, aidQAR3],
            'QVI',
            kargsMultisigAID,
            true
        );
        kargsMultisigAID.mhab = aidQAR2;
        const multisigAIDOp2 = await createAIDMultisig(
            clientQAR2,
            aidQAR2,
            [aidQAR1, aidQAR3],
            'QVI',
            kargsMultisigAID
        );
        kargsMultisigAID.mhab = aidQAR3;
        const multisigAIDOp3 = await createAIDMultisig(
            clientQAR3,
            aidQAR3,
            [aidQAR1, aidQAR2],
            'QVI',
            kargsMultisigAID
        );

        const aidQVIPrefix = multisigAIDOp1.name.split('.')[1];
        assert.equal(multisigAIDOp2.name.split('.')[1], aidQVIPrefix);
        assert.equal(multisigAIDOp3.name.split('.')[1], aidQVIPrefix);

        // GEDA anchors delegation with an interaction event.
        const anchor = {
            i: aidQVIPrefix,
            s: '0',
            d: aidQVIPrefix,
        };
        const ixnOp1 = await interactMultisig(
            clientGAR1,
            aidGAR1,
            [aidGAR2],
            aidGEDA,
            anchor,
            true
        );
        const ixnOp2 = await interactMultisig(
            clientGAR2,
            aidGAR2,
            [aidGAR1],
            aidGEDA,
            anchor
        );
        await Promise.all([
            waitOperation(clientGAR1, ixnOp1),
            waitOperation(clientGAR2, ixnOp2),
        ]);

        await waitAndMarkNotification(clientGAR1, '/multisig/ixn');

        // QARs query the GEDA's key state
        const queryOp1 = await clientQAR1
            .keyStates()
            .query(aidGEDA.prefix, '1');
        const queryOp2 = await clientQAR2
            .keyStates()
            .query(aidGEDA.prefix, '1');
        const queryOp3 = await clientQAR3
            .keyStates()
            .query(aidGEDA.prefix, '1');

        await Promise.all([
            waitOperation(clientQAR1, multisigAIDOp1),
            waitOperation(clientQAR2, multisigAIDOp2),
            waitOperation(clientQAR3, multisigAIDOp3),
            waitOperation(clientQAR1, queryOp1),
            waitOperation(clientQAR2, queryOp2),
            waitOperation(clientQAR3, queryOp3),
        ]);

        await waitAndMarkNotification(clientQAR1, '/multisig/icp');

        aidQVIbyQAR1 = await clientQAR1.identifiers().get('QVI');
        aidQVIbyQAR2 = await clientQAR2.identifiers().get('QVI');
        aidQVIbyQAR3 = await clientQAR3.identifiers().get('QVI');
    }
    assert.equal(aidQVIbyQAR1.prefix, aidQVIbyQAR2.prefix);
    assert.equal(aidQVIbyQAR1.prefix, aidQVIbyQAR3.prefix);
    assert.equal(aidQVIbyQAR1.name, aidQVIbyQAR2.name);
    assert.equal(aidQVIbyQAR1.name, aidQVIbyQAR3.name);
    const aidQVI = aidQVIbyQAR1;

    // Add endpoint role authorization for all QARs' agents.
    // Skip if they have already been authorized.
    let [oobiQVIbyQAR1, oobiQVIbyQAR2, oobiQVIbyQAR3] = await Promise.all([
        clientQAR1.oobis().get(aidQVI.name, 'agent'),
        clientQAR2.oobis().get(aidQVI.name, 'agent'),
        clientQAR3.oobis().get(aidQVI.name, 'agent'),
    ]);
    if (
        oobiQVIbyQAR1.oobis.length == 0 ||
        oobiQVIbyQAR2.oobis.length == 0 ||
        oobiQVIbyQAR3.oobis.length == 0
    ) {
        const timestamp = createTimestamp();
        const opList1 = await addEndRoleMultisig(
            clientQAR1,
            aidQAR1,
            [aidQAR2, aidQAR3],
            aidQVI,
            timestamp,
            true
        );
        const opList2 = await addEndRoleMultisig(
            clientQAR2,
            aidQAR2,
            [aidQAR1, aidQAR3],
            aidQVI,
            timestamp
        );
        const opList3 = await addEndRoleMultisig(
            clientQAR3,
            aidQAR3,
            [aidQAR1, aidQAR2],
            aidQVI,
            timestamp
        );

        await Promise.all(opList1.map((op) => waitOperation(clientQAR1, op)));
        await Promise.all(opList2.map((op) => waitOperation(clientQAR2, op)));
        await Promise.all(opList3.map((op) => waitOperation(clientQAR3, op)));

        await waitAndMarkNotification(clientQAR1, '/multisig/rpy');
        await waitAndMarkNotification(clientQAR2, '/multisig/rpy');

        [oobiQVIbyQAR1, oobiQVIbyQAR2, oobiQVIbyQAR3] = await Promise.all([
            clientQAR1.oobis().get(aidQVI.name, 'agent'),
            clientQAR2.oobis().get(aidQVI.name, 'agent'),
            clientQAR3.oobis().get(aidQVI.name, 'agent'),
        ]);
    }
    assert.equal(oobiQVIbyQAR1.role, oobiQVIbyQAR2.role);
    assert.equal(oobiQVIbyQAR1.role, oobiQVIbyQAR3.role);
    assert.equal(oobiQVIbyQAR1.oobis[0], oobiQVIbyQAR2.oobis[0]);
    assert.equal(oobiQVIbyQAR1.oobis[0], oobiQVIbyQAR3.oobis[0]);

    // GARs, LARs, ECR resolve QVI AID's OOBI
    const oobiQVI = oobiQVIbyQAR1.oobis[0].split('/agent/')[0];
    await Promise.all([
        getOrCreateContact(clientGAR1, aidQVI.name, oobiQVI),
        getOrCreateContact(clientGAR2, aidQVI.name, oobiQVI),
        getOrCreateContact(clientLAR1, aidQVI.name, oobiQVI),
        getOrCreateContact(clientLAR2, aidQVI.name, oobiQVI),
        getOrCreateContact(clientLAR3, aidQVI.name, oobiQVI),
        getOrCreateContact(clientECR, aidQVI.name, oobiQVI),
    ]);

    // GARs creates a registry for GEDA.
    // Skip if the registry has already been created.
    let [gedaRegistrybyGAR1, gedaRegistrybyGAR2] = await Promise.all([
        clientGAR1.registries().list(aidGEDA.name),
        clientGAR2.registries().list(aidGEDA.name),
    ]);
    if (gedaRegistrybyGAR1.length == 0 && gedaRegistrybyGAR2.length == 0) {
        const nonce = randomNonce();
        const registryOp1 = await createRegistryMultisig(
            clientGAR1,
            aidGAR1,
            [aidGAR2],
            aidGEDA,
            'gedaRegistry',
            nonce,
            true
        );
        const registryOp2 = await createRegistryMultisig(
            clientGAR2,
            aidGAR2,
            [aidGAR1],
            aidGEDA,
            'gedaRegistry',
            nonce
        );

        await Promise.all([
            waitOperation(clientGAR1, registryOp1),
            waitOperation(clientGAR2, registryOp2),
        ]);

        await waitAndMarkNotification(clientGAR1, '/multisig/vcp');

        [gedaRegistrybyGAR1, gedaRegistrybyGAR2] = await Promise.all([
            clientGAR1.registries().list(aidGEDA.name),
            clientGAR2.registries().list(aidGEDA.name),
        ]);
    }
    assert.equal(gedaRegistrybyGAR1[0].regk, gedaRegistrybyGAR2[0].regk);
    assert.equal(gedaRegistrybyGAR1[0].name, gedaRegistrybyGAR2[0].name);
    const gedaRegistry = gedaRegistrybyGAR1[0];

    // GEDA issues a QVI vLEI credential to the QVI AID.
    // Skip if the credential has already been issued.
    let qviCredbyGAR1 = await getIssuedCredential(
        clientGAR1,
        aidGEDA,
        aidQVI,
        QVI_SCHEMA_SAID
    );
    let qviCredbyGAR2 = await getIssuedCredential(
        clientGAR2,
        aidGEDA,
        aidQVI,
        QVI_SCHEMA_SAID
    );
    if (!(qviCredbyGAR1 && qviCredbyGAR2)) {
        const kargsSub: CredentialSubject = {
            i: aidQVI.prefix,
            dt: createTimestamp(),
            ...qviData,
        };
        const kargsIss: CredentialData = {
            i: aidGEDA.prefix,
            ri: gedaRegistry.regk,
            s: QVI_SCHEMA_SAID,
            a: kargsSub,
        };
        const IssOp1 = await issueCredentialMultisig(
            clientGAR1,
            aidGAR1,
            [aidGAR2],
            aidGEDA.name,
            kargsIss,
            true
        );
        const IssOp2 = await issueCredentialMultisig(
            clientGAR2,
            aidGAR2,
            [aidGAR1],
            aidGEDA.name,
            kargsIss
        );

        await Promise.all([
            waitOperation(clientGAR1, IssOp1),
            waitOperation(clientGAR2, IssOp2),
        ]);

        await waitAndMarkNotification(clientGAR1, '/multisig/iss');

        qviCredbyGAR1 = await getIssuedCredential(
            clientGAR1,
            aidGEDA,
            aidQVI,
            QVI_SCHEMA_SAID
        );
        qviCredbyGAR2 = await getIssuedCredential(
            clientGAR2,
            aidGEDA,
            aidQVI,
            QVI_SCHEMA_SAID
        );

        const grantTime = createTimestamp();
        await grantMultisig(
            clientGAR1,
            aidGAR1,
            [aidGAR2],
            aidGEDA,
            aidQVI,
            qviCredbyGAR1,
            grantTime,
            true
        );
        await grantMultisig(
            clientGAR2,
            aidGAR2,
            [aidGAR1],
            aidGEDA,
            aidQVI,
            qviCredbyGAR2,
            grantTime
        );

        await waitAndMarkNotification(clientGAR1, '/multisig/exn');
    }
    assert.equal(qviCredbyGAR1.sad.d, qviCredbyGAR2.sad.d);
    assert.equal(qviCredbyGAR1.sad.s, QVI_SCHEMA_SAID);
    assert.equal(qviCredbyGAR1.sad.i, aidGEDA.prefix);
    assert.equal(qviCredbyGAR1.sad.a.i, aidQVI.prefix);
    assert.equal(qviCredbyGAR1.status.s, '0');
    assert(qviCredbyGAR1.atc !== undefined);
    const qviCred = qviCredbyGAR1;
    console.log(
        'GEDA has issued a QVI vLEI credential with SAID:',
        qviCred.sad.d
    );

    // GEDA and QVI exchange grant and admit messages.
    // Skip if QVI has already received the credential.
    let qviCredbyQAR1 = await getReceivedCredential(clientQAR1, qviCred.sad.d);
    let qviCredbyQAR2 = await getReceivedCredential(clientQAR2, qviCred.sad.d);
    let qviCredbyQAR3 = await getReceivedCredential(clientQAR3, qviCred.sad.d);
    if (!(qviCredbyQAR1 && qviCredbyQAR2 && qviCredbyQAR3)) {
        const admitTime = createTimestamp();
        await admitMultisig(
            clientQAR1,
            aidQAR1,
            [aidQAR2, aidQAR3],
            aidQVI,
            aidGEDA,
            admitTime
        );
        await admitMultisig(
            clientQAR2,
            aidQAR2,
            [aidQAR1, aidQAR3],
            aidQVI,
            aidGEDA,
            admitTime
        );
        await admitMultisig(
            clientQAR3,
            aidQAR3,
            [aidQAR1, aidQAR2],
            aidQVI,
            aidGEDA,
            admitTime
        );
        await waitAndMarkNotification(clientGAR1, '/exn/ipex/admit');
        await waitAndMarkNotification(clientGAR2, '/exn/ipex/admit');
        await waitAndMarkNotification(clientQAR1, '/multisig/exn');
        await waitAndMarkNotification(clientQAR2, '/multisig/exn');
        await waitAndMarkNotification(clientQAR3, '/multisig/exn');
        await waitAndMarkNotification(clientQAR1, '/exn/ipex/admit');
        await waitAndMarkNotification(clientQAR2, '/exn/ipex/admit');
        await waitAndMarkNotification(clientQAR3, '/exn/ipex/admit');

        qviCredbyQAR1 = await waitForCredential(clientQAR1, qviCred.sad.d);
        qviCredbyQAR2 = await waitForCredential(clientQAR2, qviCred.sad.d);
        qviCredbyQAR3 = await waitForCredential(clientQAR3, qviCred.sad.d);
    }
    assert.equal(qviCred.sad.d, qviCredbyQAR1.sad.d);
    assert.equal(qviCred.sad.d, qviCredbyQAR2.sad.d);
    assert.equal(qviCred.sad.d, qviCredbyQAR3.sad.d);

    // Create a multisig AID for the LE.
    // Skip if a LE AID has already been incepted.
    let aidLEbyLAR1, aidLEbyLAR2, aidLEbyLAR3: HabState;
    try {
        aidLEbyLAR1 = await clientLAR1.identifiers().get('LE');
        aidLEbyLAR2 = await clientLAR2.identifiers().get('LE');
        aidLEbyLAR3 = await clientLAR3.identifiers().get('LE');
    } catch {
        const rstates = [aidLAR1.state, aidLAR2.state, aidLAR3.state];
        const states = rstates;

        const kargsMultisigAID: CreateIdentiferArgs = {
            algo: signify.Algos.group,
            isith: ['2/3', '1/2', '1/2'],
            nsith: ['2/3', '1/2', '1/2'],
            toad: kargsAID.toad,
            wits: kargsAID.wits,
            states: states,
            rstates: rstates,
        };

        kargsMultisigAID.mhab = aidLAR1;
        const multisigAIDOp1 = await createAIDMultisig(
            clientLAR1,
            aidLAR1,
            [aidLAR2, aidLAR3],
            'LE',
            kargsMultisigAID,
            true
        );
        kargsMultisigAID.mhab = aidLAR2;
        const multisigAIDOp2 = await createAIDMultisig(
            clientLAR2,
            aidLAR2,
            [aidLAR1, aidLAR3],
            'LE',
            kargsMultisigAID
        );
        kargsMultisigAID.mhab = aidLAR3;
        const multisigAIDOp3 = await createAIDMultisig(
            clientLAR3,
            aidLAR3,
            [aidLAR1, aidLAR2],
            'LE',
            kargsMultisigAID
        );

        await Promise.all([
            waitOperation(clientLAR1, multisigAIDOp1),
            waitOperation(clientLAR2, multisigAIDOp2),
            waitOperation(clientLAR3, multisigAIDOp3),
        ]);

        await waitAndMarkNotification(clientLAR1, '/multisig/icp');

        aidLEbyLAR1 = await clientLAR1.identifiers().get('LE');
        aidLEbyLAR2 = await clientLAR2.identifiers().get('LE');
        aidLEbyLAR3 = await clientLAR3.identifiers().get('LE');
    }
    assert.equal(aidLEbyLAR1.prefix, aidLEbyLAR2.prefix);
    assert.equal(aidLEbyLAR1.prefix, aidLEbyLAR3.prefix);
    assert.equal(aidLEbyLAR1.name, aidLEbyLAR2.name);
    assert.equal(aidLEbyLAR1.name, aidLEbyLAR3.name);
    const aidLE = aidLEbyLAR1;

    // Add endpoint role authorization for all LARs' agents.
    // Skip if they have already been authorized.
    let [oobiLEbyLAR1, oobiLEbyLAR2, oobiLEbyLAR3] = await Promise.all([
        clientLAR1.oobis().get(aidLE.name, 'agent'),
        clientLAR2.oobis().get(aidLE.name, 'agent'),
        clientLAR3.oobis().get(aidLE.name, 'agent'),
    ]);
    if (
        oobiLEbyLAR1.oobis.length == 0 ||
        oobiLEbyLAR2.oobis.length == 0 ||
        oobiLEbyLAR3.oobis.length == 0
    ) {
        const timestamp = createTimestamp();
        const opList1 = await addEndRoleMultisig(
            clientLAR1,
            aidLAR1,
            [aidLAR2, aidLAR3],
            aidLE,
            timestamp,
            true
        );
        const opList2 = await addEndRoleMultisig(
            clientLAR2,
            aidLAR2,
            [aidLAR1, aidLAR3],
            aidLE,
            timestamp
        );
        const opList3 = await addEndRoleMultisig(
            clientLAR3,
            aidLAR3,
            [aidLAR1, aidLAR2],
            aidLE,
            timestamp
        );

        await Promise.all(opList1.map((op) => waitOperation(clientLAR1, op)));
        await Promise.all(opList2.map((op) => waitOperation(clientLAR2, op)));
        await Promise.all(opList3.map((op) => waitOperation(clientLAR3, op)));

        await waitAndMarkNotification(clientLAR1, '/multisig/rpy');
        await waitAndMarkNotification(clientLAR2, '/multisig/rpy');

        [oobiLEbyLAR1, oobiLEbyLAR2, oobiLEbyLAR3] = await Promise.all([
            clientLAR1.oobis().get(aidLE.name, 'agent'),
            clientLAR2.oobis().get(aidLE.name, 'agent'),
            clientLAR3.oobis().get(aidLE.name, 'agent'),
        ]);
    }
    assert.equal(oobiLEbyLAR1.role, oobiLEbyLAR2.role);
    assert.equal(oobiLEbyLAR1.role, oobiLEbyLAR3.role);
    assert.equal(oobiLEbyLAR1.oobis[0], oobiLEbyLAR2.oobis[0]);
    assert.equal(oobiLEbyLAR1.oobis[0], oobiLEbyLAR3.oobis[0]);

    // QARs, ECR resolve LE AID's OOBI
    const oobiLE = oobiLEbyLAR1.oobis[0].split('/agent/')[0];
    await Promise.all([
        getOrCreateContact(clientQAR1, aidLE.name, oobiLE),
        getOrCreateContact(clientQAR2, aidLE.name, oobiLE),
        getOrCreateContact(clientQAR3, aidLE.name, oobiLE),
        getOrCreateContact(clientECR, aidLE.name, oobiLE),
    ]);

    // QARs creates a registry for QVI AID.
    // Skip if the registry has already been created.
    let [qviRegistrybyQAR1, qviRegistrybyQAR2, qviRegistrybyQAR3] =
        await Promise.all([
            clientQAR1.registries().list(aidQVI.name),
            clientQAR2.registries().list(aidQVI.name),
            clientQAR3.registries().list(aidQVI.name),
        ]);
    if (
        qviRegistrybyQAR1.length == 0 &&
        qviRegistrybyQAR2.length == 0 &&
        qviRegistrybyQAR3.length == 0
    ) {
        const nonce = randomNonce();
        const registryOp1 = await createRegistryMultisig(
            clientQAR1,
            aidQAR1,
            [aidQAR2, aidQAR3],
            aidQVI,
            'qviRegistry',
            nonce,
            true
        );
        const registryOp2 = await createRegistryMultisig(
            clientQAR2,
            aidQAR2,
            [aidQAR1, aidQAR3],
            aidQVI,
            'qviRegistry',
            nonce
        );
        const registryOp3 = await createRegistryMultisig(
            clientQAR3,
            aidQAR3,
            [aidQAR1, aidQAR2],
            aidQVI,
            'qviRegistry',
            nonce
        );

        await Promise.all([
            waitOperation(clientQAR1, registryOp1),
            waitOperation(clientQAR2, registryOp2),
            waitOperation(clientQAR3, registryOp3),
        ]);

        await waitAndMarkNotification(clientQAR1, '/multisig/vcp');

        [qviRegistrybyQAR1, qviRegistrybyQAR2, qviRegistrybyQAR3] =
            await Promise.all([
                clientQAR1.registries().list(aidQVI.name),
                clientQAR2.registries().list(aidQVI.name),
                clientQAR3.registries().list(aidQVI.name),
            ]);
    }
    assert.equal(qviRegistrybyQAR1[0].regk, qviRegistrybyQAR2[0].regk);
    assert.equal(qviRegistrybyQAR1[0].regk, qviRegistrybyQAR3[0].regk);
    assert.equal(qviRegistrybyQAR1[0].name, qviRegistrybyQAR2[0].name);
    assert.equal(qviRegistrybyQAR1[0].name, qviRegistrybyQAR3[0].name);
    const qviRegistry = qviRegistrybyQAR1[0];

    // QVI issues a LE vLEI credential to the LE.
    // Skip if the credential has already been issued.
    let leCredbyQAR1 = await getIssuedCredential(
        clientQAR1,
        aidQVI,
        aidLE,
        LE_SCHEMA_SAID
    );
    let leCredbyQAR2 = await getIssuedCredential(
        clientQAR2,
        aidQVI,
        aidLE,
        LE_SCHEMA_SAID
    );
    let leCredbyQAR3 = await getIssuedCredential(
        clientQAR3,
        aidQVI,
        aidLE,
        LE_SCHEMA_SAID
    );
    if (!(leCredbyQAR1 && leCredbyQAR2 && leCredbyQAR3)) {
        const leCredSource = Saider.saidify({
            d: '',
            qvi: {
                n: qviCred.sad.d,
                s: qviCred.sad.s,
            },
        })[1];

        const kargsSub: CredentialSubject = {
            i: aidLE.prefix,
            dt: createTimestamp(),
            ...leData,
        };
        const kargsIss: CredentialData = {
            i: aidQVI.prefix,
            ri: qviRegistry.regk,
            s: LE_SCHEMA_SAID,
            a: kargsSub,
            e: leCredSource,
            r: LE_RULES,
        };
        const IssOp1 = await issueCredentialMultisig(
            clientQAR1,
            aidQAR1,
            [aidQAR2, aidQAR3],
            aidQVI.name,
            kargsIss,
            true
        );
        const IssOp2 = await issueCredentialMultisig(
            clientQAR2,
            aidQAR2,
            [aidQAR1, aidQAR3],
            aidQVI.name,
            kargsIss
        );
        const IssOp3 = await issueCredentialMultisig(
            clientQAR3,
            aidQAR3,
            [aidQAR1, aidQAR2],
            aidQVI.name,
            kargsIss
        );

        await Promise.all([
            waitOperation(clientQAR1, IssOp1),
            waitOperation(clientQAR2, IssOp2),
            waitOperation(clientQAR3, IssOp3),
        ]);

        await waitAndMarkNotification(clientQAR1, '/multisig/iss');

        leCredbyQAR1 = await getIssuedCredential(
            clientQAR1,
            aidQVI,
            aidLE,
            LE_SCHEMA_SAID
        );
        leCredbyQAR2 = await getIssuedCredential(
            clientQAR2,
            aidQVI,
            aidLE,
            LE_SCHEMA_SAID
        );
        leCredbyQAR3 = await getIssuedCredential(
            clientQAR3,
            aidQVI,
            aidLE,
            LE_SCHEMA_SAID
        );

        const grantTime = createTimestamp();
        await grantMultisig(
            clientQAR1,
            aidQAR1,
            [aidQAR2, aidQAR3],
            aidQVI,
            aidLE,
            leCredbyQAR1,
            grantTime,
            true
        );
        await grantMultisig(
            clientQAR2,
            aidQAR2,
            [aidQAR1, aidQAR3],
            aidQVI,
            aidLE,
            leCredbyQAR2,
            grantTime
        );
        await grantMultisig(
            clientQAR3,
            aidQAR3,
            [aidQAR1, aidQAR2],
            aidQVI,
            aidLE,
            leCredbyQAR3,
            grantTime
        );

        await waitAndMarkNotification(clientQAR1, '/multisig/exn');
    }
    assert.equal(leCredbyQAR1.sad.d, leCredbyQAR2.sad.d);
    assert.equal(leCredbyQAR1.sad.d, leCredbyQAR3.sad.d);
    assert.equal(leCredbyQAR1.sad.s, LE_SCHEMA_SAID);
    assert.equal(leCredbyQAR1.sad.i, aidQVI.prefix);
    assert.equal(leCredbyQAR1.sad.a.i, aidLE.prefix);
    assert.equal(leCredbyQAR1.status.s, '0');
    assert(leCredbyQAR1.atc !== undefined);
    const leCred = leCredbyQAR1;
    console.log('QVI has issued a LE vLEI credential with SAID:', leCred.sad.d);

    // QVI and LE exchange grant and admit messages.
    // Skip if LE has already received the credential.
    let leCredbyLAR1 = await getReceivedCredential(clientLAR1, leCred.sad.d);
    let leCredbyLAR2 = await getReceivedCredential(clientLAR2, leCred.sad.d);
    let leCredbyLAR3 = await getReceivedCredential(clientLAR3, leCred.sad.d);
    if (!(leCredbyLAR1 && leCredbyLAR2 && leCredbyLAR3)) {
        const admitTime = createTimestamp();
        await admitMultisig(
            clientLAR1,
            aidLAR1,
            [aidLAR2, aidLAR3],
            aidLE,
            aidQVI,
            admitTime
        );
        await admitMultisig(
            clientLAR2,
            aidLAR2,
            [aidLAR1, aidLAR3],
            aidLE,
            aidQVI,
            admitTime
        );
        await admitMultisig(
            clientLAR3,
            aidLAR3,
            [aidLAR1, aidLAR2],
            aidLE,
            aidQVI,
            admitTime
        );
        await waitAndMarkNotification(clientQAR1, '/exn/ipex/admit');
        await waitAndMarkNotification(clientQAR2, '/exn/ipex/admit');
        await waitAndMarkNotification(clientQAR3, '/exn/ipex/admit');
        await waitAndMarkNotification(clientLAR1, '/multisig/exn');
        await waitAndMarkNotification(clientLAR2, '/multisig/exn');
        await waitAndMarkNotification(clientLAR3, '/multisig/exn');
        await waitAndMarkNotification(clientLAR1, '/exn/ipex/admit');
        await waitAndMarkNotification(clientLAR2, '/exn/ipex/admit');
        await waitAndMarkNotification(clientLAR3, '/exn/ipex/admit');

        leCredbyLAR1 = await waitForCredential(clientLAR1, leCred.sad.d);
        leCredbyLAR2 = await waitForCredential(clientLAR2, leCred.sad.d);
        leCredbyLAR3 = await waitForCredential(clientLAR3, leCred.sad.d);
    }
    assert.equal(leCred.sad.d, leCredbyLAR1.sad.d);
    assert.equal(leCred.sad.d, leCredbyLAR2.sad.d);
    assert.equal(leCred.sad.d, leCredbyLAR3.sad.d);

    // LARs creates a registry for LE AID.
    // Skip if the registry has already been created.
    let [leRegistrybyLAR1, leRegistrybyLAR2, leRegistrybyLAR3] =
        await Promise.all([
            clientLAR1.registries().list(aidLE.name),
            clientLAR2.registries().list(aidLE.name),
            clientLAR3.registries().list(aidLE.name),
        ]);
    if (
        leRegistrybyLAR1.length == 0 &&
        leRegistrybyLAR2.length == 0 &&
        leRegistrybyLAR3.length == 0
    ) {
        const nonce = randomNonce();
        const registryOp1 = await createRegistryMultisig(
            clientLAR1,
            aidLAR1,
            [aidLAR2, aidLAR3],
            aidLE,
            'leRegistry',
            nonce,
            true
        );
        const registryOp2 = await createRegistryMultisig(
            clientLAR2,
            aidLAR2,
            [aidLAR1, aidLAR3],
            aidLE,
            'leRegistry',
            nonce
        );
        const registryOp3 = await createRegistryMultisig(
            clientLAR3,
            aidLAR3,
            [aidLAR1, aidLAR2],
            aidLE,
            'leRegistry',
            nonce
        );

        await Promise.all([
            waitOperation(clientLAR1, registryOp1),
            waitOperation(clientLAR2, registryOp2),
            waitOperation(clientLAR3, registryOp3),
        ]);

        await waitAndMarkNotification(clientLAR1, '/multisig/vcp');

        [leRegistrybyLAR1, leRegistrybyLAR2, leRegistrybyLAR3] =
            await Promise.all([
                clientLAR1.registries().list(aidLE.name),
                clientLAR2.registries().list(aidLE.name),
                clientLAR3.registries().list(aidLE.name),
            ]);
    }
    assert.equal(leRegistrybyLAR1[0].regk, leRegistrybyLAR2[0].regk);
    assert.equal(leRegistrybyLAR1[0].regk, leRegistrybyLAR3[0].regk);
    assert.equal(leRegistrybyLAR1[0].name, leRegistrybyLAR2[0].name);
    assert.equal(leRegistrybyLAR1[0].name, leRegistrybyLAR3[0].name);
    const leRegistry = leRegistrybyLAR1[0];

    // LE issues a ECR vLEI credential to the ECR Person.
    // Skip if the credential has already been issued.
    let ecrCredbyLAR1 = await getIssuedCredential(
        clientLAR1,
        aidLE,
        aidECR,
        ECR_SCHEMA_SAID
    );
    let ecrCredbyLAR2 = await getIssuedCredential(
        clientLAR2,
        aidLE,
        aidECR,
        ECR_SCHEMA_SAID
    );
    let ecrCredbyLAR3 = await getIssuedCredential(
        clientLAR3,
        aidLE,
        aidECR,
        ECR_SCHEMA_SAID
    );
    if (!(ecrCredbyLAR1 && ecrCredbyLAR2 && ecrCredbyLAR3)) {
        console.log('Issuing ECR vLEI Credential from LE');
        const ecrCredSource = Saider.saidify({
            d: '',
            le: {
                n: leCred.sad.d,
                s: leCred.sad.s,
            },
        })[1];

        const kargsSub: CredentialSubject = {
            i: aidECR.prefix,
            dt: createTimestamp(),
            u: new Salter({}).qb64,
            ...ecrData,
        };
        const kargsIss: CredentialData = {
            u: new Salter({}).qb64,
            i: aidLE.prefix,
            ri: leRegistry.regk,
            s: ECR_SCHEMA_SAID,
            a: kargsSub,
            e: ecrCredSource,
            r: ECR_RULES,
        };

        const IssOp1 = await issueCredentialMultisig(
            clientLAR1,
            aidLAR1,
            [aidLAR2, aidLAR3],
            aidLE.name,
            kargsIss,
            true
        );
        const IssOp2 = await issueCredentialMultisig(
            clientLAR2,
            aidLAR2,
            [aidLAR1, aidLAR3],
            aidLE.name,
            kargsIss
        );
        const IssOp3 = await issueCredentialMultisig(
            clientLAR3,
            aidLAR3,
            [aidLAR1, aidLAR2],
            aidLE.name,
            kargsIss
        );

        await Promise.all([
            waitOperation(clientLAR1, IssOp1),
            waitOperation(clientLAR2, IssOp2),
            waitOperation(clientLAR3, IssOp3),
        ]);

        await waitAndMarkNotification(clientLAR1, '/multisig/iss');

        ecrCredbyLAR1 = await getIssuedCredential(
            clientLAR1,
            aidLE,
            aidECR,
            ECR_SCHEMA_SAID
        );
        ecrCredbyLAR2 = await getIssuedCredential(
            clientLAR2,
            aidLE,
            aidECR,
            ECR_SCHEMA_SAID
        );
        ecrCredbyLAR3 = await getIssuedCredential(
            clientLAR3,
            aidLE,
            aidECR,
            ECR_SCHEMA_SAID
        );

        const grantTime = createTimestamp();
        await grantMultisig(
            clientLAR1,
            aidLAR1,
            [aidLAR2, aidLAR3],
            aidLE,
            aidECR,
            ecrCredbyLAR1,
            grantTime,
            true
        );
        await grantMultisig(
            clientLAR2,
            aidLAR2,
            [aidLAR1, aidLAR3],
            aidLE,
            aidECR,
            ecrCredbyLAR2,
            grantTime
        );
        await grantMultisig(
            clientLAR3,
            aidLAR3,
            [aidLAR1, aidLAR2],
            aidLE,
            aidECR,
            ecrCredbyLAR3,
            grantTime
        );

        await waitAndMarkNotification(clientLAR1, '/multisig/exn');
    }
    assert.equal(ecrCredbyLAR1.sad.d, ecrCredbyLAR2.sad.d);
    assert.equal(ecrCredbyLAR1.sad.d, ecrCredbyLAR3.sad.d);
    assert.equal(ecrCredbyLAR1.sad.s, ECR_SCHEMA_SAID);
    assert.equal(ecrCredbyLAR1.sad.i, aidLE.prefix);
    assert.equal(ecrCredbyLAR1.sad.a.i, aidECR.prefix);
    assert.equal(ecrCredbyLAR1.status.s, '0');
    assert(ecrCredbyLAR1.atc !== undefined);
    const ecrCred = ecrCredbyLAR1;
    console.log(
        'LE has issued an ECR vLEI credential with SAID:',
        ecrCred.sad.d
    );

    // LE and ECR Person exchange grant and admit messages.
    // Skip if ECR Person has already received the credential.
    let ecrCredbyECR = await getReceivedCredential(clientECR, ecrCred.sad.d);
    if (!ecrCredbyECR) {
        await admitSinglesig(clientECR, aidECR, aidLE);
        await waitAndMarkNotification(clientLAR1, '/exn/ipex/admit');
        await waitAndMarkNotification(clientLAR2, '/exn/ipex/admit');
        await waitAndMarkNotification(clientLAR3, '/exn/ipex/admit');

        ecrCredbyECR = await waitForCredential(clientECR, ecrCred.sad.d);
    }
    assert.equal(ecrCred.sad.d, ecrCredbyECR.sad.d);
}, 360000);

function createTimestamp() {
    return new Date().toISOString().replace('Z', '000+00:00');
}

async function getOrCreateAID(
    client: SignifyClient,
    name: string,
    kargs: CreateIdentiferArgs
): Promise<HabState> {
    try {
        return await client.identifiers().get(name);
    } catch {
        const result: EventResult = await client
            .identifiers()
            .create(name, kargs);

        await waitOperation(client, await result.op());
        const aid = await client.identifiers().get(name);

        const op = await client
            .identifiers()
            .addEndRole(name, 'agent', client!.agent!.pre);
        await waitOperation(client, await op.op());
        console.log(name, 'AID:', aid.prefix);
        return aid;
    }
}

async function createAIDMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    groupName: string,
    kargs: CreateIdentiferArgs,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/icp');

    const icpResult = await client.identifiers().create(groupName, kargs);
    const op = await icpResult.op();

    const serder = icpResult.serder;
    const sigs = icpResult.sigs;
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(serder, sigers));
    const atc = ims.substring(serder.size);
    const embeds = {
        icp: [serder, atc],
    };
    const smids = kargs.states?.map((state) => state['i']);
    const recp = otherMembersAIDs.map((aid) => aid.prefix);

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/icp',
            { gid: serder.pre, smids: smids, rmids: smids },
            embeds,
            recp
        );

    return op;
}

async function interactMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    anchor: { i: string; s: string; d: string },
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/ixn');

    const ixnResult = await client
        .identifiers()
        .interact(multisigAID.name, anchor);
    const op = await ixnResult.op();
    const serder = ixnResult.serder;
    const sigs = ixnResult.sigs;
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(serder, sigers));
    const atc = ims.substring(serder.size);
    const xembeds = {
        ixn: [serder, atc],
    };
    const smids = [aid.prefix, ...otherMembersAIDs.map((aid) => aid.prefix)];
    const recp = otherMembersAIDs.map((aid) => aid.prefix);

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/ixn',
            { gid: serder.pre, smids: smids, rmids: smids },
            xembeds,
            recp
        );

    return op;
}

async function addEndRoleMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    timestamp: string,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/rpy');

    const opList: any[] = [];
    const members = await client.identifiers().members(multisigAID.name);
    const signings = members['signing'];

    for (const signing of signings) {
        const eid = Object.keys(signing.ends.agent)[0];
        const endRoleResult = await client
            .identifiers()
            .addEndRole(multisigAID.name, 'agent', eid, timestamp);
        const op = await endRoleResult.op();
        opList.push(op);

        const rpy = endRoleResult.serder;
        const sigs = endRoleResult.sigs;
        const ghabState1 = multisigAID.state;
        const seal = [
            'SealEvent',
            {
                i: multisigAID.prefix,
                s: ghabState1['ee']['s'],
                d: ghabState1['ee']['d'],
            },
        ];
        const sigers = sigs.map(
            (sig: string) => new signify.Siger({ qb64: sig })
        );
        const roleims = signify.d(
            signify.messagize(rpy, sigers, seal, undefined, undefined, false)
        );
        const atc = roleims.substring(rpy.size);
        const roleembeds = {
            rpy: [rpy, atc],
        };
        const recp = otherMembersAIDs.map((aid) => aid.prefix);
        await client
            .exchanges()
            .send(
                aid.name,
                'multisig',
                aid,
                '/multisig/rpy',
                { gid: multisigAID.prefix },
                roleembeds,
                recp
            );
    }

    return opList;
}

async function createRegistryMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    registryName: string,
    nonce: string,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/vcp');

    const vcpResult = await client.registries().create({
        name: multisigAID.name,
        registryName: registryName,
        nonce: nonce,
    });
    const op = await vcpResult.op();

    const serder = vcpResult.regser;
    const anc = vcpResult.serder;
    const sigs = vcpResult.sigs;
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(anc, sigers));
    const atc = ims.substring(anc.size);
    const regbeds = {
        vcp: [serder, ''],
        anc: [anc, atc],
    };
    const recp = otherMembersAIDs.map((aid) => aid.prefix);

    await client
        .exchanges()
        .send(
            aid.name,
            'registry',
            aid,
            '/multisig/vcp',
            { gid: multisigAID.prefix },
            regbeds,
            recp
        );

    return op;
}

async function getIssuedCredential(
    issuerClient: SignifyClient,
    issuerAID: HabState,
    recipientAID: HabState,
    schemaSAID: string
) {
    const credentialList = await issuerClient.credentials().list({
        filter: {
            '-i': issuerAID.prefix,
            '-s': schemaSAID,
            '-a-i': recipientAID.prefix,
        },
    });
    assert(credentialList.length <= 1);
    return credentialList[0];
}

async function issueCredentialMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAIDName: string,
    kargsIss: CredentialData,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/iss');

    const credResult = await client
        .credentials()
        .issue(multisigAIDName, kargsIss);
    const op = credResult.op;

    const multisigAID = await client.identifiers().get(multisigAIDName);
    const keeper = client.manager!.get(multisigAID);
    const sigs = await keeper.sign(signify.b(credResult.anc.raw));
    const sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(credResult.anc, sigers));
    const atc = ims.substring(credResult.anc.size);
    const embeds = {
        acdc: [credResult.acdc, ''],
        iss: [credResult.iss, ''],
        anc: [credResult.anc, atc],
    };
    const recp = otherMembersAIDs.map((aid) => aid.prefix);

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/iss',
            { gid: multisigAID.prefix },
            embeds,
            recp
        );

    return op;
}

async function grantMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    recipientAID: HabState,
    credential: any,
    timestamp: string,
    isInitiator: boolean = false
) {
    if (!isInitiator) await waitAndMarkNotification(client, '/multisig/exn');

    const [grant, sigs, end] = await client.ipex().grant({
        senderName: multisigAID.name,
        acdc: new Serder(credential.sad),
        anc: new Serder(credential.anc),
        iss: new Serder(credential.iss),
        recipient: recipientAID.prefix,
        datetime: timestamp,
    });

    await client
        .ipex()
        .submitGrant(multisigAID.name, grant, sigs, end, [recipientAID.prefix]);

    const mstate = multisigAID.state;
    const seal = [
        'SealEvent',
        { i: multisigAID.prefix, s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    const sigers = sigs.map((sig) => new signify.Siger({ qb64: sig }));
    const gims = signify.d(signify.messagize(grant, sigers, seal));
    let atc = gims.substring(grant.size);
    atc += end;
    const gembeds = {
        exn: [grant, atc],
    };
    const recp = otherMembersAIDs.map((aid) => aid.prefix);

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/exn',
            { gid: multisigAID.prefix },
            gembeds,
            recp
        );
}

async function admitMultisig(
    client: SignifyClient,
    aid: HabState,
    otherMembersAIDs: HabState[],
    multisigAID: HabState,
    recipientAID: HabState,
    timestamp: string
    // numGrantMsgs: number
) {
    const grantMsgSaid = await waitAndMarkNotification(
        client,
        '/exn/ipex/grant'
    );

    const [admit, sigs, end] = await client
        .ipex()
        .admit(multisigAID.name, '', grantMsgSaid, timestamp);

    await client
        .ipex()
        .submitAdmit(multisigAID.name, admit, sigs, end, [recipientAID.prefix]);

    const mstate = multisigAID.state;
    const seal = [
        'SealEvent',
        { i: multisigAID.prefix, s: mstate['ee']['s'], d: mstate['ee']['d'] },
    ];
    const sigers = sigs.map((sig: string) => new signify.Siger({ qb64: sig }));
    const ims = signify.d(signify.messagize(admit, sigers, seal));
    let atc = ims.substring(admit.size);
    atc += end;
    const gembeds = {
        exn: [admit, atc],
    };
    const recp = otherMembersAIDs.map((aid) => aid.prefix);

    await client
        .exchanges()
        .send(
            aid.name,
            'multisig',
            aid,
            '/multisig/exn',
            { gid: multisigAID.prefix },
            gembeds,
            recp
        );
}

async function admitSinglesig(
    client: SignifyClient,
    aid: HabState,
    recipientAid: HabState
) {
    const grantMsgSaid = await waitAndMarkNotification(
        client,
        '/exn/ipex/grant'
    );

    const [admit, sigs, aend] = await client
        .ipex()
        .admit(aid.name, '', grantMsgSaid);

    await client
        .ipex()
        .submitAdmit(aid.name, admit, sigs, aend, [recipientAid.prefix]);
}

async function waitAndMarkNotification(client: SignifyClient, route: string) {
    const notes = await waitForNotifications(client, route);

    await Promise.all(
        notes.map(async (note) => {
            await client.notifications().mark(note.i);
        })
    );

    return notes[notes.length - 1]?.a.d ?? '';
}

async function getReceivedCredential(
    client: SignifyClient,
    credId: string
): Promise<any> {
    const credentialList = await client.credentials().list({
        filter: {
            '-d': credId,
        },
    });
    return credentialList[0];
}

async function waitForCredential(
    client: SignifyClient,
    credSAID: string,
    MAX_RETRIES: number = 10
) {
    let retryCount = 0;
    while (retryCount < MAX_RETRIES) {
        const cred = await getReceivedCredential(client, credSAID);
        if (cred) return cred;

        await new Promise((resolve) => setTimeout(resolve, 1000));
        console.log(` retry-${retryCount}: No credentials yet...`);
        retryCount = retryCount + 1;
    }
    throw Error('Credential SAID: ' + credSAID + ' has not been received');
}
