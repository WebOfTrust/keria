import libsodium from 'libsodium-wrappers-sumo';
import { Signer } from '../../src/keri/core/signer.ts';
import { assert, describe, it } from 'vitest';
import { MtrDex } from '../../src/keri/core/matter.ts';
import { incept, messagize, rotate } from '../../src/keri/core/eventing.ts';
import { Saider } from '../../src/keri/core/saider.ts';
import { Diger } from '../../src/keri/core/diger.ts';
import { b, d, Ilks } from '../../src/keri/core/core.ts';
import { Siger } from '../../src/keri/core/siger.ts';

describe('key event function', () => {
    it('incept should create inception events', async () => {
        await libsodium.ready;

        const seed = new Uint8Array([
            159, 123, 168, 167, 168, 67, 57, 150, 38, 250, 177, 153, 235, 170,
            32, 196, 27, 71, 17, 196, 174, 83, 65, 82, 201, 189, 4, 157, 133,
            41, 126, 147,
        ]);
        let signer0 = new Signer({ raw: seed, transferable: false }); // original signing keypair non transferable
        assert.equal(signer0.code, MtrDex.Ed25519_Seed);
        assert.equal(signer0.verfer.code, MtrDex.Ed25519N);
        let keys0 = [signer0.verfer.qb64];
        let serder = incept({ keys: keys0 }); // default nxt is empty so abandoned
        assert.equal(
            serder.sad['i'],
            'BFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH'
        );
        assert.deepStrictEqual(serder.sad['n'], []);
        assert.equal(
            serder.raw,
            '{"v":"KERI10JSON0000fd_","t":"icp","d":"EMW0zK3bagYPO6gx3w7Ua90f-I7x5kGIaI4X' +
                'eq9W8_As","i":"BFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH","s":"0","kt":"1' +
                '","k":["BFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH"],"nt":"0","n":[],"bt":' +
                '"0","b":[],"c":[],"a":[]}'
        );
        let saider = new Saider({ code: MtrDex.Blake3_256 }, serder.sad);
        assert.equal(saider.verify(serder.sad), true);

        assert.throws(() => {
            serder = incept({
                keys: keys0,
                code: MtrDex.Ed25519N,
                ndigs: ['ABCDE'],
            });
        });

        assert.throws(() => {
            serder = incept({
                keys: keys0,
                code: MtrDex.Ed25519N,
                wits: ['ABCDE'],
            });
        });

        assert.throws(() => {
            serder = incept({
                keys: keys0,
                code: MtrDex.Ed25519N,
                data: [{ i: 'ABCDE' }],
            });
        });

        signer0 = new Signer({ raw: seed }); // original signing keypair transferable default
        assert.equal(signer0.code, MtrDex.Ed25519_Seed);
        assert.equal(signer0.verfer.code, MtrDex.Ed25519);
        keys0 = [signer0.verfer.qb64];
        serder = incept({ keys: keys0 }); // default nxt is empty so abandoned
        assert.equal(
            serder.sad['i'],
            'DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH'
        );
        assert.deepStrictEqual(serder.sad['n'], []);
        assert.equal(
            serder.raw,
            '{"v":"KERI10JSON0000fd_","t":"icp","d":"EPLRRJFe2FHdXKVTkSEX4xb4x-YaPFJ2Xds1' +
                'vhtNTd4n","i":"DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH","s":"0","kt":"1' +
                '","k":["DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH"],"nt":"0","n":[],"bt":' +
                '"0","b":[],"c":[],"a":[]}'
        );
        saider = new Saider({ code: MtrDex.Blake3_256 }, serder.sad);
        assert.equal(saider.verify(serder.sad), true);

        // (b'\x83B~\x04\x94\xe3\xceUQy\x11f\x0c\x93]\x1e\xbf\xacQ\xb5\xd6Y^\xa2E\xfa\x015\x98Y\xdd\xe8')
        let seed1 = new Uint8Array([
            131, 66, 126, 4, 148, 227, 206, 85, 81, 121, 17, 102, 12, 147, 93,
            30, 191, 172, 81, 181, 214, 89, 94, 162, 69, 250, 1, 53, 152, 89,
            221, 232,
        ]);
        let signer1 = new Signer({ raw: seed1 }); // next signing keypair transferable is default
        assert.equal(signer1.code, MtrDex.Ed25519_Seed);
        assert.equal(signer1.verfer.code, MtrDex.Ed25519);
        // compute nxt digest
        let nxt1 = [new Diger({}, signer1.verfer.qb64b).qb64]; // dfault sith is 1
        assert.deepStrictEqual(nxt1, [
            'EIf-ENw7PrM52w4H-S7NGU2qVIfraXVIlV9hEAaMHg7W',
        ]);
        let serder0 = incept({
            keys: keys0,
            ndigs: nxt1,
            code: MtrDex.Blake3_256,
        }); // intive false
        assert.equal(serder0.sad['t'], Ilks.icp);
        assert.equal(
            serder0.sad['d'],
            'EAKCxMOuoRzREVHsHCkLilBrUXTvyenBiuM2QtV8BB0C'
        );
        assert.equal(serder0.sad['d'], serder0.sad['i']);
        assert.equal(serder0.sad['s'], '0');
        assert.equal(serder0.sad['kt'], '1');
        assert.equal(serder0.sad['nt'], '1');
        assert.deepStrictEqual(serder0.sad['n'], nxt1);
        assert.equal(serder0.sad['bt'], '0'); // hex str
        assert.equal(
            serder0.raw,
            '{"v":"KERI10JSON00012b_","t":"icp","d":"EAKCxMOuoRzREVHsHCkLilBrUXTvyenBiuM2' +
                'QtV8BB0C","i":"EAKCxMOuoRzREVHsHCkLilBrUXTvyenBiuM2QtV8BB0C","s":"0","kt":"1' +
                '","k":["DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH"],"nt":"1","n":["EIf-EN' +
                'w7PrM52w4H-S7NGU2qVIfraXVIlV9hEAaMHg7W"],"bt":"0","b":[],"c":[],"a":[]}'
        );

        // (b'\x83B~\x04\x94\xe3\xceUQy\x11f\x0c\x93]\x1e\xbf\xacQ\xb5\xd6Y^\xa2E\xfa\x015\x98Y\xdd\xe8')
        seed1 = new Uint8Array([
            131, 66, 126, 4, 148, 227, 206, 85, 81, 121, 17, 102, 12, 147, 93,
            30, 191, 172, 81, 181, 214, 89, 94, 162, 69, 250, 1, 53, 152, 89,
            221, 232,
        ]);
        signer1 = new Signer({ raw: seed1 }); // next signing keypair transferable is default
        assert.equal(signer1.code, MtrDex.Ed25519_Seed);
        assert.equal(signer1.verfer.code, MtrDex.Ed25519);
        // compute nxt digest
        nxt1 = [new Diger({}, signer1.verfer.qb64b).qb64]; // dfault sith is 1
        assert.deepStrictEqual(nxt1, [
            'EIf-ENw7PrM52w4H-S7NGU2qVIfraXVIlV9hEAaMHg7W',
        ]);
        serder0 = incept({
            keys: keys0,
            ndigs: nxt1,
            code: MtrDex.Blake3_256,
            intive: true,
        }); // intive true
        assert.equal(serder0.sad['t'], Ilks.icp);
        assert.equal(
            serder0.sad['d'],
            'EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL'
        );
        assert.equal(serder0.sad['d'], serder0.sad['i']);
        assert.equal(serder0.sad['s'], '0');
        assert.equal(serder0.sad['kt'], 1);
        assert.equal(serder0.sad['nt'], 1);
        assert.deepStrictEqual(serder0.sad['n'], nxt1);
        assert.equal(serder0.sad['bt'], 0);
        assert.equal(
            serder0.raw,
            '{"v":"KERI10JSON000125_","t":"icp","d":"EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5u' +
                'k-WxvhsL","i":"EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL","s":"0","kt":1,' +
                '"k":["DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH"],"nt":1,"n":["EIf-ENw7Pr' +
                'M52w4H-S7NGU2qVIfraXVIlV9hEAaMHg7W"],"bt":0,"b":[],"c":[],"a":[]}'
        );

        const siger = signer0.sign(b(serder0.raw), 0) as Siger;
        assert.equal(
            siger.qb64,
            'AABB3MJGmBXxSEryNHw3YwZZLRl_6Ws4Me2WFq8PrQ6WlluSOpPqbwXuiG9RvNWZkqeW8A_0VRjokGMVRZ3m-c0I'
        );

        const msg = messagize(serder0, [siger]);
        assert.equal(
            d(msg),
            '{"v":"KERI10JSON000125_","t":"icp","d":"EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL","i"' +
                ':"EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL","s":"0","kt":1,"k":["DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH"],' +
                '"nt":1,"n":["EIf-ENw7PrM52w4H-S7NGU2qVIfraXVIlV9hEAaMHg7W"],"bt":0,"b":[],"c":[],"a":[]}' +
                '-AABAABB3MJGmBXxSEryNHw3YwZZLRl_6Ws4Me2WFq8PrQ6WlluSOpPqbwXuiG9RvNWZkqeW8A_0VRjokGMVRZ3m-c0I'
        );
        const seal = [
            'SealEvent',
            {
                i: 'EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL',
                s: '0',
                d: 'EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL',
            },
        ];
        const msgseal = messagize(serder0, [siger], seal);
        assert.equal(
            d(msgseal),
            '{"v":"KERI10JSON000125_","t":"icp","d":"EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL","i"' +
                ':"EIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL","s":"0","kt":1,"k":["DFs8BBx86uytIM0D2BhsE5rrqVIT8ef8mflpNceHo4XH"]' +
                ',"nt":1,"n":["EIf-ENw7PrM52w4H-S7NGU2qVIfraXVIlV9hEAaMHg7W"],"bt":0,"b":[],"c":[],"a"' +
                ':[]}-FABEIflL4H4134zYoRM6ls6Q086RLC_BhfNFh5uk-WxvhsL0AAAAAAAAAAAAAAAAAAAAAAAEIflL4H4134zYoRM6ls6Q086RLC_' +
                'BhfNFh5uk-WxvhsL-AABAABB3MJGmBXxSEryNHw3YwZZLRl_6Ws4Me2WFq8PrQ6WlluSOpPqbwXuiG9RvNWZkqeW8A_0VRjokGMVRZ3m-c0I'
        );
    });

    it('Rotate should create rotation event with hex sequence number', async () => {
        await libsodium.ready;

        const signer0 = new Signer({ transferable: true });
        const signer1 = new Signer({ transferable: true });
        const keys0 = [signer0.verfer.qb64];
        const ndigs = [new Diger({}, signer1.verfer.qb64b).qb64];
        const serder = incept({ keys: keys0, ndigs });

        function createRotation(sn: number) {
            return rotate({
                keys: keys0,
                pre: serder.sad.i,
                ndigs: serder.sad.n,
                sn,
                isith: 1,
                nsith: 1,
            }).sad['s'];
        }

        assert.equal(createRotation(1), '1');
        assert.equal(createRotation(10), 'a');
        assert.equal(createRotation(14), 'e');
        assert.equal(createRotation(255), 'ff');
    });
});
