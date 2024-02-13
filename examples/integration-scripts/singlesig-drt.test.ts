import { CreateIdentiferArgs, SignifyClient } from 'signify-ts';
import {
    getOrCreateClients,
    getOrCreateContact,
    getOrCreateIdentifier,
} from './utils/test-setup';
import { assertOperations, waitOperation } from './utils/test-util';

let delegator: SignifyClient, delegate: SignifyClient;
let name1_id: string, name1_oobi: string;
let contact1_id: string;

beforeAll(async () => {
    [delegator, delegate] = await getOrCreateClients(2);
});
beforeAll(async () => {
    [name1_id, name1_oobi] = await getOrCreateIdentifier(delegator, 'name1');
});
beforeAll(async () => {
    contact1_id = await getOrCreateContact(delegate, 'contact1', name1_oobi);
});
afterAll(async () => {
    await assertOperations(delegator, delegate);
});

describe('singlesig-drt', () => {
    test('delegate1a', async () => {
        // delegate creates identifier without witnesses
        let kargs: CreateIdentiferArgs = {
            delpre: name1_id,
        };
        let result = await delegate.identifiers().create('delegate1', kargs);
        let op = await result.op();
        let delegate1 = await delegate.identifiers().get('delegate1');
        expect(op.name).toEqual(`delegation.${delegate1.prefix}`);

        // delegator approves delegate
        let seal = {
            i: delegate1.prefix,
            s: '0',
            d: delegate1.prefix,
        };
        result = await delegator.identifiers().interact('name1', seal);
        let op1 = await result.op();

        let op2 = await delegate.keyStates().query(name1_id, '1');

        await Promise.all([
            waitOperation(delegate, op),
            waitOperation(delegator, op1),
            waitOperation(delegate, op2),
        ]);

        kargs = {};
        result = await delegate.identifiers().rotate('delegate1', kargs);
        op = await result.op();
        expect(op.name).toEqual(`delegation.${delegate1.prefix}`);

        // delegator approves delegate
        delegate1 = await delegate.identifiers().get('delegate1');

        seal = {
            i: delegate1.prefix,
            s: '1',
            d: delegate1.state.d,
        };

        result = await delegator.identifiers().interact('name1', seal);
        op1 = await result.op();
        op2 = await delegate.keyStates().query(name1_id, '2');

        await Promise.all([
            (op = await waitOperation(delegate, op)),
            waitOperation(delegator, op1),
            waitOperation(delegate, op2),
        ]);

        expect(op.response.t).toEqual(`drt`);
        expect(op.response.s).toEqual(`1`);
    });
});
