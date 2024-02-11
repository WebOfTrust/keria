import { EventResult, SignifyClient } from 'signify-ts';
import {
    getOrCreateClients,
    getOrCreateContact,
    getOrCreateIdentifier,
} from './utils/test-setup';
import { assertOperations, waitOperation } from './utils/test-util';

let client1: SignifyClient, client2: SignifyClient;
let name1_id: string, name1_oobi: string;
let contact1_id: string;

beforeAll(async () => {
    [client1, client2] = await getOrCreateClients(2);
});
beforeAll(async () => {
    [name1_id, name1_oobi] = await getOrCreateIdentifier(client1, 'name1');
});
beforeAll(async () => {
    contact1_id = await getOrCreateContact(client2, 'contact1', name1_oobi);
});
afterAll(async () => {
    await assertOperations(client1, client2);
});

interface KeyState {
    i: string;
    s: string;
    [property: string]: any;
}

describe('singlesig-ixn', () => {
    test('step1', async () => {
        expect(name1_id).toEqual(contact1_id);

        const keystate1 = await client1.keyStates().get(name1_id);
        expect(keystate1).toHaveLength(1);

        const keystate2 = await client2.keyStates().get(contact1_id);
        expect(keystate2).toHaveLength(1);

        // local and remote keystate sequence match
        expect(keystate1[0].s).toEqual(keystate2[0].s);
    });
    test('ixn1', async () => {
        // local keystate before ixn
        const keystate0: KeyState = (
            await client1.keyStates().get(name1_id)
        ).at(0);
        expect(keystate0).not.toBeNull();

        // ixn
        const result: EventResult = await client1
            .identifiers()
            .interact('name1', {});
        await waitOperation(client1, await result.op());

        // local keystate after ixn
        const keystate1: KeyState = (
            await client1.keyStates().get(name1_id)
        ).at(0);
        expect(parseInt(keystate1.s)).toBeGreaterThan(0);
        // sequence has incremented
        expect(parseInt(keystate1.s)).toEqual(parseInt(keystate0.s) + 1);

        // remote keystate after ixn
        const keystate2: KeyState = (
            await client2.keyStates().get(contact1_id)
        ).at(0);
        // remote keystate is one behind
        expect(parseInt(keystate2.s)).toEqual(parseInt(keystate1.s) - 1);

        // refresh remote keystate
        let op = await client2
            .keyStates()
            .query(contact1_id, keystate1.s, undefined);
        op = await waitOperation(client2, op);
        const keystate3: KeyState = op.response;
        // local and remote keystate match
        expect(keystate3.s).toEqual(keystate1.s);
    });
});
