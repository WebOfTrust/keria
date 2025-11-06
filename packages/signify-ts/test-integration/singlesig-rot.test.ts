import { afterAll, assert, beforeAll, describe, expect, test } from 'vitest';
import { EventResult, RotateIdentifierArgs, SignifyClient } from 'signify-ts';
import {
    assertOperations,
    getOrCreateClients,
    getOrCreateContact,
    getOrCreateIdentifier,
    waitOperation,
} from './utils/test-util.ts';

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
        assert.equal(name1_id, contact1_id);

        const keystate1 = await client1.keyStates().get(name1_id);
        assert.strictEqual(keystate1.length, 1);

        const keystate2 = await client2.keyStates().get(contact1_id);
        assert.strictEqual(keystate2.length, 1);

        // local and remote keystate sequence match
        assert.equal(keystate1[0].s, keystate2[0].s);
    });
    test('rot1', async () => {
        // local keystate before rot
        const keystate0: KeyState = (
            await client1.keyStates().get(name1_id)
        ).at(0);
        expect(keystate0).not.toBeNull();
        assert.strictEqual(keystate0.k.length, 1);
        assert.strictEqual(keystate0.n.length, 1);

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
        assert.equal(parseInt(keystate1.s), parseInt(keystate0.s) + 1);
        // current keys changed
        expect(keystate1.k[0]).not.toEqual(keystate0.k[0]);
        // next key hashes changed
        expect(keystate1.n[0]).not.toEqual(keystate0.n[0]);

        // remote keystate after rot
        const keystate2: KeyState = (
            await client2.keyStates().get(contact1_id)
        ).at(0);
        // remote keystate is one behind
        assert.equal(parseInt(keystate2.s), parseInt(keystate1.s) - 1);

        // refresh remote keystate
        let op = await client2
            .keyStates()
            .query(contact1_id, keystate1.s, undefined);
        op = await waitOperation(client2, op);
        const keystate3: KeyState = op.response;
        // local and remote keystate match
        assert.equal(keystate3.s, keystate1.s);
        assert.equal(keystate3.k[0], keystate1.k[0]);
        assert.equal(keystate3.n[0], keystate1.n[0]);
    });
});
