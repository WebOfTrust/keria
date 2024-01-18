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

        delegate1 = await client2.identifiers().get('delegate1');
        let seal = {
            i: delegate1.prefix,
            s: '0',
            d: delegate1.prefix,
        };
        result = await client1.identifiers().interact('name1', seal);
        let op1 = await result.op();

        let op2 = await client2.keyStates().query(name1_id, '1');

        await Promise.all([
            (op = await waitOperation(client2, op)),
            waitOperation(client1, op1),
            waitOperation(client2, op2),
        ]);

        delegate1 = await client2.identifiers().get('delegate1');
        expect(delegate1.prefix).toEqual(op.response.i);

        // delegate creates identifier with default witness config
        let env = resolveEnvironment();
        kargs = {
            delpre: name1_id,
            toad: env.witnessIds.length,
            wits: env.witnessIds,
        };
        result = await client2.identifiers().create('delegate2', kargs);
        op = await result.op();
        let delegate2 = await client2.identifiers().get('delegate2');
        expect(op.name).toEqual(`delegation.${delegate2.prefix}`);

        // delegator approves delegate
        delegate2 = await client2.identifiers().get('delegate2');
        seal = {
            i: delegate2.prefix,
            s: '0',
            d: delegate2.prefix,
        };
        result = await client1.identifiers().interact('name1', seal);
        op1 = await result.op();

        op2 = await client2.keyStates().query(name1_id, '2');

        await Promise.all([
            (op = await waitOperation(client2, op)),
            waitOperation(client1, op1),
            waitOperation(client2, op2),
        ]);

        // delegate waits for completion
        delegate2 = await client2.identifiers().get('delegate2');
        expect(delegate2.prefix).toEqual(op.response.i);
    });
});
