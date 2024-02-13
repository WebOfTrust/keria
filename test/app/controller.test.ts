import { Controller } from '../../src/keri/app/controller';
import { strict as assert } from 'assert';
import libsodium from 'libsodium-wrappers-sumo';
import { openManager } from '../../src/keri/core/manager';
import { Signer } from '../../src/keri/core/signer';
import { MtrDex } from '../../src/keri/core/matter';
import { Tier } from '../../src';

describe('Controller', () => {
    it('manage account AID signing and agent verification', async () => {
        await libsodium.ready;
        let passcode = '0123456789abcdefghijk';
        const mgr = openManager(passcode);
        assert.equal(mgr.aeid, 'BMbZTXzB7LmWPT2TXLGV88PQz5vDEM2L2flUs2yxn3U9');

        const raw = new Uint8Array([
            187, 140, 234, 145, 219, 254, 20, 194, 16, 18, 97, 194, 140, 192,
            61, 145, 222, 110, 59, 160, 152, 2, 72, 122, 87, 143, 109, 39, 98,
            153, 192, 148,
        ]);
        const agentSigner = new Signer({
            raw: raw,
            code: MtrDex.Ed25519_Seed,
            transferable: false,
        });
        assert.equal(
            agentSigner.verfer.qb64,
            'BHptu91ecGv_mxO8T3b98vNQUCghT8nfYkWRkVqOZark'
        );

        // New account needed.  Send to remote my name and encryption pubk and get back
        // their pubk and and my encrypted account package
        // let pkg = {}
        let controller = new Controller(passcode, Tier.low);
        assert.equal(
            controller.pre,
            'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'
        );

        passcode = 'abcdefghijk0123456789';
        controller = new Controller(passcode, Tier.low);
        assert.equal(
            controller.pre,
            'EIIY2SgE_bqKLl2MlnREUawJ79jTuucvWwh-S6zsSUFo'
        );
    });
});
