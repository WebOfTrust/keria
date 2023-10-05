import {
    deversify,
    Dict,
    Ilks,
    Serials,
    Version,
} from '../../src/keri/core/core';
import { strict as assert } from 'assert';
import { Salter, Tier } from '../../src/keri/core/salter';
import { MtrDex } from '../../src/keri/core/matter';
import { Diger } from '../../src/keri/core/diger';
import { Serder } from '../../src/keri/core/serder';
import libsodium from 'libsodium-wrappers-sumo';
import { Prefixer } from '../../src/keri/core/prefixer';

describe('deversify', () => {
    it('should parse a KERI event version string', async () => {
        let [, kind, version, size] = deversify('KERI10JSON00011c_');
        assert.equal(kind, Serials.JSON);
        assert.deepStrictEqual(version, new Version(1, 0));
        assert.equal(size, '00011c');
    });
});

describe('Serder', () => {
    it('should create KERI events from dicts', async () => {
        await libsodium.ready;

        let sith = 1;
        let nsith = 1;
        let sn = 0;
        let toad = 0;

        let raw = new Uint8Array([
            5, 170, 143, 45, 83, 154, 233, 250, 85, 156, 2, 156, 155, 8, 72,
            117,
        ]);
        let salter = new Salter({ raw: raw });
        let skp0 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'A',
            Tier.low,
            true
        );
        let keys = [skp0.verfer.qb64];

        let skp1 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'N',
            Tier.low,
            true
        );
        let ndiger = new Diger({}, skp1.verfer.qb64b);
        let nxt = [ndiger.qb64];
        assert.deepStrictEqual(nxt, [
            'EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj',
        ]);

        let ked0 = {
            v: 'KERI10JSON000000_',
            t: Ilks.icp,
            d: '',
            i: '',
            s: sn.toString(16),
            kt: sith.toString(16),
            k: keys,
            nt: nsith.toString(16),
            n: nxt,
            bt: toad.toString(16),
            b: [],
            c: [],
            a: [],
        } as Dict<any>;

        let serder = new Serder(ked0);
        assert.equal(
            serder.raw,
            '{"v":"KERI10JSON0000d3_","t":"icp","d":"","i":"","s":"0","kt":"1","k":' +
                '["DAUDqkmn-hqlQKD8W-FAEa5JUvJC2I9yarEem-AAEg3e"],"nt":"1",' +
                '"n":["EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj"],"bt":"0","b":[],"c":[],"a":[]}'
        );
        let aid0 = new Prefixer({ code: MtrDex.Ed25519 }, ked0);
        assert.equal(aid0.code, MtrDex.Ed25519);
        assert.equal(aid0.qb64, skp0.verfer.qb64);
        assert.equal(
            skp0.verfer.qb64,
            'DAUDqkmn-hqlQKD8W-FAEa5JUvJC2I9yarEem-AAEg3e'
        );

        aid0 = new Prefixer({ code: MtrDex.Blake3_256 }, ked0);
        assert.equal(aid0.qb64, 'ECHOi6qRaswNpvytpCtpvEh2cB2aLAwVHBLFinno3YVW');
    });
});
