import { deversify, Ilks, Serials, Version } from '../../src/keri/core/core.ts';
import { assert, describe, it } from 'vitest';
import { Salter, Tier } from '../../src/keri/core/salter.ts';
import { MtrDex } from '../../src/keri/core/matter.ts';
import { Diger } from '../../src/keri/core/diger.ts';
import { Serder } from '../../src/keri/core/serder.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { Prefixer } from '../../src/keri/core/prefixer.ts';

describe('deversify', () => {
    it('should parse a KERI event version string', async () => {
        const [, kind, version, size] = deversify('KERI10JSON00011c_');
        assert.equal(kind, Serials.JSON);
        assert.deepStrictEqual(version, new Version(1, 0));
        assert.equal(size, '00011c');
    });
});

describe('Serder', () => {
    it('should create KERI events from dicts', async () => {
        await libsodium.ready;

        const sith = 1;
        const nsith = 1;
        const sn = 0;
        const toad = 0;

        const raw = new Uint8Array([
            5, 170, 143, 45, 83, 154, 233, 250, 85, 156, 2, 156, 155, 8, 72,
            117,
        ]);
        const salter = new Salter({ raw: raw });
        const skp0 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'A',
            Tier.low,
            true
        );
        const keys = [skp0.verfer.qb64];

        const skp1 = salter.signer(
            MtrDex.Ed25519_Seed,
            true,
            'N',
            Tier.low,
            true
        );
        const ndiger = new Diger({}, skp1.verfer.qb64b);
        const nxt = [ndiger.qb64];
        assert.deepStrictEqual(nxt, [
            'EAKUR-LmLHWMwXTLWQ1QjxHrihBmwwrV2tYaSG7hOrWj',
        ]);

        const ked0 = {
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
        };

        const serder = new Serder(ked0);
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

        const serder1 = new Serder({
            ...ked0,
            a: {
                n: 'Lenksjö',
            },
        });
        assert.equal(serder1.sad.v, 'KERI10JSON000139_');
    });
});
