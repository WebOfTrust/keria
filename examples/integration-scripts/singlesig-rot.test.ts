import { EventResult, RotateIdentifierArgs, SignifyClient } from 'signify-ts';
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
    k: string[];
    n: string[];
    [property: string]: any;
}

describe('singlesig-rot', () => {
    test('step1', async () => {
        expect(name1_id).toEqual(contact1_id);

        const keystate1 = await client1.keyStates().get(name1_id);
        expect(keystate1).toHaveLength(1);

        const keystate2 = await client2.keyStates().get(contact1_id);
        expect(keystate2).toHaveLength(1);

        // local and remote keystate sequence match
        expect(keystate1[0].s).toEqual(keystate2[0].s);
    });
    test('rot1', async () => {
        // local keystate before rot
        const keystate0: KeyState = (
            await client1.keyStates().get(name1_id)
        ).at(0);
        expect(keystate0).not.toBeNull();
        expect(keystate0.k).toHaveLength(1);
        expect(keystate0.n).toHaveLength(1);

        // rot
        const args: RotateIdentifierArgs = {};
        const result: EventResult = await client1
            .identifiers()
            .rotate('name1', args);
        await waitOperation(client1, await result.op());

        // local keystate after rot
        const keystate1: KeyState = (
            await client1.keyStates().get(name1_id)
        ).at(0);
        expect(parseInt(keystate1.s)).toBeGreaterThan(0);
        // sequence has incremented
        expect(parseInt(keystate1.s)).toEqual(parseInt(keystate0.s) + 1);
        // current keys changed
        expect(keystate1.k[0]).not.toEqual(keystate0.k[0]);
        // next key hashes changed
        expect(keystate1.n[0]).not.toEqual(keystate0.n[0]);

        // remote keystate after rot
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
        expect(keystate3.k[0]).toEqual(keystate1.k[0]);
        expect(keystate3.n[0]).toEqual(keystate1.n[0]);
    });
});
