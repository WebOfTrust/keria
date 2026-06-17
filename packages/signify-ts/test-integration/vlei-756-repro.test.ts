import { afterAll, assert, test } from 'vitest';
import signify, {
    CredentialData,
    HabState,
    randomNonce,
    SignifyClient,
} from '#signify-ts';
import { resolveEnvironment } from './utils/resolve-env.ts';
import {
    probeCredentialGet,
    probeCredentialState,
} from './utils/credential-health.ts';
import {
    acceptMultisigIncept,
    addEndRoleMultisig,
    createRegistryMultisig,
    grantMultisig,
    issueCredentialMultisig,
    multisigIssue,
    startMultisigIncept,
} from './utils/multisig-utils.ts';
import { retry } from './utils/retry.ts';
import {
    createClient,
    createIdentifier,
    createTimestamp,
    resolveOobi,
    waitAndMarkNotification,
    waitOperation,
} from './utils/test-util.ts';

const env = resolveEnvironment();
const wits = env.witnessIds.slice(1);
const groupName = 'multisig';

const SCHEMA_SAID = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao';
const SCHEMA_URL = `${env.vleiServerUrl}/oobi/${SCHEMA_SAID}`;
const LEI = '5493001KJTIIGC8Y1R17';

let clientM1: SignifyClient;
let clientM2: SignifyClient;
let aidM1: HabState;
let aidM2: HabState;
let aidHolder1: HabState;
let aidHolder2: HabState;
let aidGroup: HabState;
let registryRegk: string;
let cred1Said: string;
let cred2Said: string;
let cred1IssExn: { e: { acdc: CredentialData } };

afterAll(() => {
    console.dir({
        m1: { prefix: aidM1?.prefix, bran: clientM1?.bran },
        m2: { prefix: aidM2?.prefix, bran: clientM2?.bran },
        group: aidGroup?.prefix,
        cred1Said,
        cred2Said,
    });
});

test('Create clients', async () => {
    await signify.ready();
    [clientM1, clientM2] = await Promise.all([createClient(), createClient()]);
});

test('Create members', async () => {
    [aidM1, aidM2, aidHolder1, aidHolder2] = await Promise.all([
        createIdentifier(clientM1, 'member1', { toad: 1, wits }),
        createIdentifier(clientM2, 'member2', { toad: 1, wits }),
        createIdentifier(clientM1, 'holder1', { toad: 1, wits }),
        createIdentifier(clientM1, 'holder2', { toad: 1, wits }),
    ]);
});

test('Resolve oobis', async () => {
    const [oobiM1, oobiM2] = await Promise.all([
        clientM1.oobis().get('member1', 'agent'),
        clientM2.oobis().get('member2', 'agent'),
    ]);
    await resolveOobi(clientM1, oobiM2.oobis[0], 'member2');
    await resolveOobi(clientM2, oobiM1.oobis[0], 'member1');
    await resolveOobi(clientM1, SCHEMA_URL);
    await resolveOobi(clientM2, SCHEMA_URL);
});

test('Create 2-of-2 multisig', async () => {
    const op1 = await startMultisigIncept(clientM1, {
        groupName,
        localMemberName: 'member1',
        participants: [aidM1.prefix, aidM2.prefix],
        isith: 2,
        nsith: 2,
        toad: aidM1.state.b.length,
        wits: aidM1.state.b,
    });
    const said2 = await waitAndMarkNotification(clientM2, '/multisig/icp');
    const op2 = await acceptMultisigIncept(clientM2, {
        localMemberName: 'member2',
        groupName,
        msgSaid: said2,
    });
    await Promise.all([
        waitOperation(clientM1, op1),
        waitOperation(clientM2, op2),
    ]);
    aidGroup = await clientM1.identifiers().get(groupName);
});

test('authorize end roles', async () => {
    const stamp = createTimestamp();
    const op1 = await addEndRoleMultisig(
        clientM1,
        await clientM1.identifiers().get(groupName),
        stamp
    );
    const op2 = await addEndRoleMultisig(
        clientM2,
        await clientM2.identifiers().get(groupName),
        stamp
    );
    await Promise.all([
        waitOperation(clientM1, op1[0]),
        waitOperation(clientM2, op2[0]),
    ]);
});

test('create registry', { timeout: 120000 }, async () => {
    const nonce = randomNonce();
    const regOp1 = await createRegistryMultisig(
        clientM1,
        aidM1,
        [aidM2],
        await clientM1.identifiers().get(groupName),
        'vLEI Registry',
        nonce,
        true
    );
    const regOp2 = await createRegistryMultisig(
        clientM2,
        aidM2,
        [aidM1],
        await clientM2.identifiers().get(groupName),
        'vLEI Registry',
        nonce
    );
    await Promise.all([
        waitOperation(clientM1, regOp1),
        waitOperation(clientM2, regOp2),
    ]);
    registryRegk = (
        await retry(async () => {
            const regs = await clientM1.registries().list(groupName);
            assert(regs.length > 0);
            return regs;
        })
    )[0].regk;
});

function credKargs(holder: HabState): CredentialData {
    return {
        i: aidGroup.prefix,
        ri: registryRegk,
        s: SCHEMA_SAID,
        a: { i: holder.prefix, dt: createTimestamp(), LEI },
    };
}

test('Issue credential 1 — both members healthy', async () => {
    const issOp1 = await issueCredentialMultisig(
        clientM1,
        aidM1,
        [aidM2],
        groupName,
        credKargs(aidHolder1),
        true
    );

    const msgSaid = await waitAndMarkNotification(clientM2, '/multisig/iss');
    cred1IssExn = (await clientM2.groups().getRequest(msgSaid))[0].exn;
    const issM2 = await clientM2
        .credentials()
        .issue(groupName, cred1IssExn.e.acdc);
    await multisigIssue(clientM2, groupName, issM2);

    await Promise.all([
        waitOperation(clientM1, issOp1),
        waitOperation(clientM2, issM2.op),
    ]);

    cred1Said = (
        await clientM1.credentials().list({
            filter: { '-a-i': aidHolder1.prefix },
        })
    )[0].sad.d;

    await probeCredentialState(clientM1, cred1Said, 'M1 cred1');
    await probeCredentialState(clientM2, cred1Said, 'M2 cred1');
});

test(
    'Issue credential 2 — stale iss poisons M2',
    { timeout: 120000 },
    async () => {
        const issOp2 = await issueCredentialMultisig(
            clientM1,
            aidM1,
            [aidM2],
            groupName,
            credKargs(aidHolder2),
            true
        );

        // M2 accepts stale /multisig/iss for credential 1 — expect HTTP 500, do not wait.
        let staleAcceptError: string | undefined;
        try {
            const issStale = await clientM2
                .credentials()
                .issue(groupName, cred1IssExn.e.acdc);
            await multisigIssue(clientM2, groupName, issStale);
            staleAcceptError = 'unexpected: stale accept succeeded';
        } catch (err) {
            staleAcceptError = err instanceof Error ? err.message : String(err);
        }
        console.dir({ step: 'stale cred1 re-accept', staleAcceptError });

        const staleProbe = await probeCredentialGet(clientM2, cred1Said);
        console.dir({
            step: 'after stale cred1 re-accept',
            m2Cred1Status: staleProbe.status,
        });

        // M2 accepts credential 2 iss (submit only — coordination stuck, do not wait).
        const msgSaid2 = await waitAndMarkNotification(
            clientM2,
            '/multisig/iss'
        );
        const exn2 = (await clientM2.groups().getRequest(msgSaid2))[0].exn;
        const issM2Cred2 = await clientM2
            .credentials()
            .issue(groupName, exn2.e.acdc);
        await multisigIssue(clientM2, groupName, issM2Cred2);

        // M1 sees issuance complete (only needed its own half).
        await waitOperation(clientM1, issOp2);

        cred2Said = (
            await clientM1.credentials().list({
                filter: { '-a-i': aidHolder2.prefix },
            })
        )[0].sad.d;
    }
);

test('Report state after credential 2 issuance', async () => {
    const state = [
        await probeCredentialState(clientM1, cred1Said, 'M1 cred1'),
        await probeCredentialState(clientM2, cred1Said, 'M2 cred1'),
        await probeCredentialState(clientM1, cred2Said, 'M1 cred2'),
        await probeCredentialState(clientM2, cred2Said, 'M2 cred2'),
    ];
    console.dir({ cred1Said, cred2Said, state }, { depth: null });
});

test('Grant credential 2 — M2 getCredential fails on grant accept', async () => {
    const grantTime = createTimestamp();
    const cred2OnM1 = await clientM1.credentials().get(cred2Said);

    await grantMultisig(
        clientM1,
        aidM1,
        [aidM2],
        aidGroup,
        aidHolder2,
        cred2OnM1,
        grantTime,
        true
    );

    const m2Cred2Probe = await probeCredentialGet(clientM2, cred2Said);
    console.dir({
        step: 'before M2 grant accept',
        m2Cred2Status: m2Cred2Probe.status,
    });

    const msgSaid = await waitAndMarkNotification(clientM2, '/multisig/exn');
    await clientM2.groups().getRequest(msgSaid);

    let grantAcceptError: string | undefined;
    try {
        await clientM2.credentials().get(cred2Said);
        grantAcceptError = 'unexpected: getCredential succeeded';
    } catch (err) {
        grantAcceptError = err instanceof Error ? err.message : String(err);
    }

    console.dir({ grantAcceptError });
    if (
        !grantAcceptError?.includes('500') &&
        !grantAcceptError?.includes('HTTP')
    ) {
        console.warn(
            'Bug did not reproduce on grant accept:',
            grantAcceptError
        );
    }
});
