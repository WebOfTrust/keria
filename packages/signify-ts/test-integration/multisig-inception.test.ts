import signify from 'signify-ts';
import {
    getOrCreateClient,
    getOrCreateIdentifier,
    resolveOobi,
    waitForNotifications,
    waitOperation,
} from './utils/test-util.ts';
import {
    acceptMultisigIncept,
    startMultisigIncept,
} from './utils/multisig-utils.ts';
import { assert, test } from 'vitest';
import { step } from './utils/test-step.ts';

test('multisig inception', async () => {
    await signify.ready();
    const [client1, client2] = await Promise.all([
        getOrCreateClient(),
        getOrCreateClient(),
    ]);

    const [[aid1], [aid2]] = await Promise.all([
        getOrCreateIdentifier(client1, 'member1'),
        getOrCreateIdentifier(client2, 'member2'),
    ]);

    await step('Resolve oobis', async () => {
        const oobi1 = await client1.oobis().get('member1', 'agent');
        const oobi2 = await client2.oobis().get('member2', 'agent');

        await Promise.all([
            resolveOobi(client1, oobi2.oobis[0], 'member2'),
            resolveOobi(client2, oobi1.oobis[0], 'member1'),
        ]);
    });

    await step('Create multisig group', async () => {
        const groupName = 'multisig';
        const op1 = await startMultisigIncept(client1, {
            groupName,
            localMemberName: 'member1',
            participants: [aid1, aid2],
            toad: 2,
            isith: 2,
            nsith: 2,
            wits: [
                'BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha',
                'BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM',
                'BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX',
            ],
        });
        console.log(
            'Member1 initiated multisig, waiting for others to join...'
        );

        // Second member check notifications and join the multisig
        const notifications = await waitForNotifications(
            client2,
            '/multisig/icp'
        );
        await Promise.all(
            notifications.map((note) => client2.notifications().mark(note.i))
        );
        const msgSaid = notifications[notifications.length - 1].a.d;
        assert(msgSaid, 'msgSaid not defined');
        const op2 = await acceptMultisigIncept(client2, {
            localMemberName: 'member2',
            groupName,
            msgSaid,
        });
        console.log('Member2 joined multisig, waiting for others...');

        // Check for completion
        await Promise.all([
            waitOperation(client1, op1),
            waitOperation(client2, op2),
        ]);
        console.log('Multisig created!');

        const multisig1 = await client1.identifiers().get(groupName);
        const multisig2 = await client2.identifiers().get(groupName);
        assert.strictEqual(multisig1.prefix, multisig2.prefix);
        const members = await client1.identifiers().members(groupName);
        assert.strictEqual(members.signing.length, 2);
        assert.strictEqual(members.rotation.length, 2);
        assert.strictEqual(members.signing[0].aid, aid1);
        assert.strictEqual(members.signing[1].aid, aid2);
        assert.strictEqual(members.rotation[0].aid, aid1);
        assert.strictEqual(members.rotation[1].aid, aid2);
    });

    await step('Test creating another group', async () => {
        const groupName = 'multisig2';
        const op1 = await startMultisigIncept(client1, {
            groupName,
            localMemberName: 'member1',
            participants: [aid1, aid2],
            toad: 0,
            isith: 2,
            nsith: 2,
            wits: [],
        });
        console.log(
            'Member1 initiated multisig, waiting for others to join...'
        );

        // Second member check notifications and join the multisig
        const notifications = await waitForNotifications(
            client2,
            '/multisig/icp'
        );
        await Promise.all(
            notifications.map((note) => client2.notifications().mark(note.i))
        );
        const msgSaid = notifications[notifications.length - 1].a.d;
        assert(msgSaid, 'msgSaid not defined');
        const op2 = await acceptMultisigIncept(client2, {
            localMemberName: 'member2',
            groupName,
            msgSaid,
        });

        await Promise.all([
            waitOperation(client1, op1),
            waitOperation(client2, op2),
        ]);

        // TODO: https://github.com/WebOfTrust/keria/issues/189
        // const members = await client1.identifiers().members(groupName);
        // assert.strictEqual(members.signing.length, 2);
        // assert.strictEqual(members.rotating.length, 2);
    });
}, 30000);
