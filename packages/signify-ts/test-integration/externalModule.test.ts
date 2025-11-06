import { assert, test } from 'vitest';
import signify from 'signify-ts';
import { BIP39Shim } from './modules/bip39_shim.ts';
import {
    assertOperations,
    getOrCreateClient,
    waitOperation,
} from './utils/test-util.ts';

test('bip39_shim', async () => {
    const externalModule: signify.ExternalModule = {
        type: 'bip39_shim',
        name: 'bip39_shim',
        module: BIP39Shim,
    };
    const client1 = await getOrCreateClient(undefined, [externalModule]);

    const words = new BIP39Shim(0, {}).generateMnemonic(256);
    const icpResult = await client1.identifiers().create('aid1', {
        algo: signify.Algos.extern,
        extern_type: 'bip39_shim',
        extern: { mnemonics: words },
    });
    const op = await waitOperation(client1, await icpResult.op());
    assert.equal(op['done'], true);

    await assertOperations(client1);
}, 30000);
