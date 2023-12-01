import { Counter, CtrDex } from '../../src/keri/core/counter';
import { strict as assert } from 'assert';
import { b, b64ToInt, intToB64 } from '../../src/keri/core/core';

describe('int to b64 and back', () => {
    it('should encode and decode stuff', async () => {
        assert.equal(Counter.Sizes.get('-A')!.hs, 2); // hard size
        assert.equal(Counter.Sizes.get('-A')!.ss, 2); // soft size
        assert.equal(Counter.Sizes.get('-A')!.fs, 4); // full size
        assert.equal(Counter.Sizes.get('-A')!.ls, 0); // lead size

        // verify first hs Sizes matches hs in Codes for same first char
        Counter.Sizes.forEach((_, ckey) => {
            const key = ckey.slice(0, 2);
            assert.equal(Counter.Hards.get(key), Counter.Sizes.get(ckey)!.hs);
        });

        // verify all Codes have hs > 0 and ss > 0 and fs = hs + ss and not fs % 4
        Counter.Sizes.forEach((val, _) => {
            assert.equal(
                val.hs > 0 &&
                    val.ss > 0 &&
                    val.hs + val.ss == val.fs &&
                    !(val.fs % 4),
                true
            );
        });
        // Bizes maps bytes of sextet of decoded first character of code with hard size of code
        // verify equivalents of items for Sizes and Bizes
        // Counter.Hards.forEach((sval, skey) => {
        //     let ckey = codeB64ToB2(skey)
        //     assert.equal(Counter.Bards[ckey], sval)
        // })

        assert.throws(() => {
            new Counter({});
        });

        let count = 1;
        let qsc = CtrDex.ControllerIdxSigs + intToB64(count, 2);
        assert.equal(qsc, '-AAB');
        let qscb = b(qsc);

        let counter = new Counter({ code: CtrDex.ControllerIdxSigs }); // default count = 1
        assert.equal(counter.code, CtrDex.ControllerIdxSigs);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        counter = new Counter({ qb64: qsc }); // default count = 1
        assert.equal(counter.code, CtrDex.ControllerIdxSigs);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        counter = new Counter({ qb64b: qscb }); // default count = 1
        assert.equal(counter.code, CtrDex.ControllerIdxSigs);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        const longqs64 = `${qsc}ABCD`;
        counter = new Counter({ qb64: longqs64 });
        assert.equal(counter.qb64.length, Counter.Sizes.get(counter.code)!.fs);

        const shortqcs = qsc.slice(0, -1);
        assert.throws(() => {
            new Counter({ qb64: shortqcs });
        });

        count = 5;
        qsc = CtrDex.ControllerIdxSigs + intToB64(count, 2);
        assert.equal(qsc, '-AAF');
        qscb = b(qsc);

        counter = new Counter({ code: CtrDex.ControllerIdxSigs, count: count });
        assert.equal(counter.code, CtrDex.ControllerIdxSigs);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        counter = new Counter({ qb64: qsc }); // default count = 1
        assert.equal(counter.code, CtrDex.ControllerIdxSigs);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        counter = new Counter({ qb64b: qscb }); // default count = 1
        assert.equal(counter.code, CtrDex.ControllerIdxSigs);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        // test with big codes index=1024
        count = 1024;
        qsc = CtrDex.BigAttachedMaterialQuadlets + intToB64(count, 5);
        assert.equal(qsc, '-0VAAAQA');
        qscb = b(qsc);

        counter = new Counter({
            code: CtrDex.BigAttachedMaterialQuadlets,
            count: count,
        });
        assert.equal(counter.code, CtrDex.BigAttachedMaterialQuadlets);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        counter = new Counter({ qb64: qsc }); // default count = 1
        assert.equal(counter.code, CtrDex.BigAttachedMaterialQuadlets);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        counter = new Counter({ qb64b: qscb }); // default count = 1
        assert.equal(counter.code, CtrDex.BigAttachedMaterialQuadlets);
        assert.equal(counter.count, count);
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        const verint = 0;
        const version = intToB64(verint, 3);
        assert.equal(version, 'AAA');
        assert.equal(verint, b64ToInt(version));
        qsc = CtrDex.KERIProtocolStack + version;
        assert.equal(qsc, '--AAAAAA'); // keri Cesr version 0.0.0
        qscb = b(qsc);

        counter = new Counter({
            code: CtrDex.KERIProtocolStack,
            count: verint,
        });
        assert.equal(counter.code, CtrDex.KERIProtocolStack);
        assert.equal(counter.count, verint);
        assert.equal(counter.countToB64(3), version);
        assert.equal(counter.countToB64(), version); // default length
        assert.deepStrictEqual(counter.qb64b, qscb);
        assert.equal(counter.qb64, qsc);

        assert.equal(Counter.semVerToB64('1.2.3'), 'BCD');
        assert.equal(Counter.semVerToB64(), 'AAA');
        assert.equal(Counter.semVerToB64('', 1), 'BAA');
        assert.equal(Counter.semVerToB64('', 0, 1), 'ABA');
        assert.equal(Counter.semVerToB64('', 0, 0, 1), 'AAB');
        assert.equal(Counter.semVerToB64('', 3, 4, 5), 'DEF');

        assert.equal(Counter.semVerToB64('1.1'), 'BBA');
        assert.equal(Counter.semVerToB64('1.'), 'BAA');
        assert.equal(Counter.semVerToB64('1'), 'BAA');
        assert.equal(Counter.semVerToB64('1.2.'), 'BCA');
        assert.equal(Counter.semVerToB64('..'), 'AAA');
        assert.equal(Counter.semVerToB64('1..3'), 'BAD');
        assert.equal(Counter.semVerToB64('4', 1, 2, 3), 'ECD');
    });
});
