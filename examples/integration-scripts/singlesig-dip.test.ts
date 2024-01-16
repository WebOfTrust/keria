import { CreateIdentiferArgs, SignifyClient } from 'signify-ts';
import {
    getOrCreateClients,
    getOrCreateContact,
    getOrCreateIdentifier,
} from './utils/test-setup';
import { waitOperation } from './utils/test-util';
import { resolveEnvironment } from './utils/resolve-env';

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

describe('singlesig-dip', () => {
    test('delegate1a', async () => {
        // delegate creates identifier without witnesses
        let kargs: CreateIdentiferArgs = {
            delpre: name1_id,
        };
        let result = await client2.identifiers().create('delegate1', kargs);
        let op = await result.op();
        let delegate1 = await client2.identifiers().get('delegate1');
        expect(op.name).toEqual(`delegation.${delegate1.prefix}`);
    });
    test('delegator1', async () => {
        // delegator approves delegate
        let delegate1 = await client2.identifiers().get('delegate1');
        let seal = {
            i: delegate1.prefix,
            s: '0',
            d: delegate1.prefix,
        };
        let result = await client1.identifiers().interact('name1', seal);
        let op = waitOperation(client1, await result.op());
    });
    test('delegate1b', async () => {
        // delegate waits for completion
        let delegate1 = await client2.identifiers().get('delegate1');
        let op: any = { name: `delegation.${delegate1.prefix}` };
        op = await waitOperation(client2, op);
        expect(delegate1.prefix).toEqual(op.response.i);
    });
    test('delegate2a', async () => {
        // delegate creates identifier with default witness config
        let env = resolveEnvironment();
        let kargs: CreateIdentiferArgs = {
            delpre: name1_id,
            toad: env.witnessIds.length,
            wits: env.witnessIds,
        };
        let result = await client2.identifiers().create('delegate2', kargs);
        let op = await result.op();
        let delegate2 = await client2.identifiers().get('delegate2');
        expect(op.name).toEqual(`delegation.${delegate2.prefix}`);
    });
    test('delegator2', async () => {
        // delegator approves delegate
        let delegate2 = await client2.identifiers().get('delegate2');
        let seal = {
            i: delegate2.prefix,
            s: '0',
            d: delegate2.prefix,
        };
        let result = await client1.identifiers().interact('name1', seal);
        let op = waitOperation(client1, await result.op());
    });
    test('delegate2b', async () => {
        // delegate waits for completion
        let delegate2 = await client2.identifiers().get('delegate2');
        let op: any = { name: `delegation.${delegate2.prefix}` };
        op = await waitOperation(client2, op);
        expect(delegate2.prefix).toEqual(op.response.i);
    });
});
