import { strict as assert } from 'assert';
import signify from 'signify-ts';
import { BIP39Shim } from './modules/bip39_shim';
import { resolveEnvironment } from './utils/resolve-env';

const { url, bootUrl } = resolveEnvironment();

test('bip39_shim', async () => {
    await signify.ready();
    const bran1 = signify.randomPasscode();
    const externalModule: signify.ExternalModule = {
        type: 'bip39_shim',
        name: 'bip39_shim',
        module: BIP39Shim,
    };
    const client1 = new signify.SignifyClient(
        url,
        bran1,
        signify.Tier.low,
        bootUrl,
        [externalModule]
    );
    await client1.boot();
    await client1.connect();
    const state1 = await client1.state();
    console.log(
        'Client 1 connected. Client AID:',
        state1.controller.state.i,
        'Agent AID: ',
        state1.agent.i
    );
    const words = new BIP39Shim(0, {}).generateMnemonic(256);
    const icpResult = await client1.identifiers().create('aid1', {
        algo: signify.Algos.extern,
        extern_type: 'bip39_shim',
        extern: { mnemonics: words },
    });
    const op = await icpResult.op();
    assert.equal(op['done'], true);
}, 30000);
