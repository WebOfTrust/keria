import { Matter } from '../../src/keri/core/matter.ts';
import { assert, describe, it } from 'vitest';
import { blake3 } from '@noble/hashes/blake3';

import { Diger } from '../../src/keri/core/diger.ts';
import { MtrDex } from '../../src/keri/core/matter.ts';
import { concat } from '../../src/keri/core/core.ts';

function encodeText(text: string) {
    return new TextEncoder().encode(text);
}

describe('Diger', () => {
    it('should generate digests', () => {
        // Create something to digest and verify
        const ser = encodeText('abcdefghijklmnopqrstuvwxyz0123456789');

        const digest = blake3.create({ dkLen: 32 }).update(ser).digest();

        let diger = new Diger({ raw: digest });
        assert.deepStrictEqual(diger.code, MtrDex.Blake3_256);

        let sizage = Matter.Sizes.get(diger.code);
        assert.deepStrictEqual(diger.qb64.length, sizage!.fs);
        let result = diger.verify(ser);
        assert.equal(result, true);

        result = diger.verify(concat(ser, encodeText('2j2idjpwjfepjtgi')));
        assert.equal(result, false);
        diger = new Diger({ raw: digest, code: MtrDex.Blake3_256 });
        assert.deepStrictEqual(diger.code, MtrDex.Blake3_256);

        assert.equal(
            diger.qb64,
            'ELC5L3iBVD77d_MYbYGGCUQgqQBju1o4x1Ud-z2sL-ux'
        );
        sizage = Matter.Sizes.get(diger.code);
        assert.deepStrictEqual(diger.qb64.length, sizage!.fs);

        result = diger.verify(ser);
        assert.equal(result, true);

        diger = new Diger({}, ser);
        assert.equal(
            diger.qb64,
            'ELC5L3iBVD77d_MYbYGGCUQgqQBju1o4x1Ud-z2sL-ux'
        );
        sizage = Matter.Sizes.get(diger.code);
        assert.deepStrictEqual(diger.qb64.length, sizage!.fs);
        result = diger.verify(ser);
        assert.equal(result, true);
    });
});
