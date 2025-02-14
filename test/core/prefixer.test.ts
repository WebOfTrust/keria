import libsodium from 'libsodium-wrappers-sumo';
import {
    Protocols,
    Ilks,
    Serials,
    versify,
    Vrsn_1_0,
} from '../../src/keri/core/core';
import { MtrDex } from '../../src/keri/core/matter';
import { Prefixer } from '../../src/keri/core/prefixer';
import { strict as assert } from 'assert';

describe('Prefixer', () => {
    it('should create autonomic identifier prefix using derivation as determined by code from ked', async () => {
        await libsodium.ready;

        // (b'\xacr\xda\xc83~\x99r\xaf\xeb`\xc0\x8cR\xd7\xd7\xf69\xc8E\x1e\xd2\xf0=`\xf7\xbf\x8a\x18\x8a`q') // from keripy
        const verkey = new Uint8Array([
            172, 114, 218, 200, 51, 126, 153, 114, 175, 235, 96, 192, 140, 82,
            215, 215, 246, 57, 200, 69, 30, 210, 240, 61, 96, 247, 191, 138, 24,
            138, 96, 113,
        ]);
        let prefixer = new Prefixer({ raw: verkey, code: MtrDex.Ed25519 });
        assert.equal(prefixer.code, MtrDex.Ed25519);
        assert.equal(
            prefixer.qb64,
            'DKxy2sgzfplyr-tgwIxS19f2OchFHtLwPWD3v4oYimBx'
        );

        // Test digest derivation from inception ked
        const vs = versify(Protocols.KERI, Vrsn_1_0, Serials.JSON, 0);
        const sn = 0;
        const ilk = Ilks.icp;
        const sith = '1';
        const keys = [new Prefixer({ raw: verkey, code: MtrDex.Ed25519 }).qb64];
        const nxt = '';
        const toad = 0;
        const wits = new Array<string>();
        const cnfg = new Array<string>();

        const ked = {
            v: vs, // version string
            i: '', // qb64 prefix
            s: sn.toString(16), // hex string no leading zeros lowercase
            t: ilk,
            kt: sith, // hex string no leading zeros lowercase
            k: keys, // list of qb64
            n: nxt, // hash qual Base64
            wt: toad.toString(16), // hex string no leading zeros lowercase
            w: wits, // list of qb64 may be empty
            c: cnfg, // list of config ordered mappings may be empty
        };

        prefixer = new Prefixer({ code: MtrDex.Blake3_256 }, ked);
        assert.equal(
            prefixer.qb64,
            'ELEjyRTtmfyp4VpTBTkv_b6KONMS1V8-EW-aGJ5P_QMo'
        );
    });
});
