import libsodium from 'libsodium-wrappers-sumo';
import { assert, describe, it } from 'vitest';
import { IdrDex, Indexer } from '../../src/keri/core/indexer.ts';
import { b, intToB64 } from '../../src/keri/core/core.ts';
import {
    decodeBase64Url,
    encodeBase64Url,
} from '../../src/keri/core/base64.ts';

describe('Indexer', () => {
    it('should encode and decode dual indexed signatures', async () => {
        await libsodium.ready;

        assert.equal(Indexer.Sizes.get('A')!.hs, 1); // hard size
        assert.equal(Indexer.Sizes.get('A')!.ss, 1); // soft size
        assert.equal(Indexer.Sizes.get('A')!.os, 0); // other size
        assert.equal(Indexer.Sizes.get('A')!.fs, 88); // full size
        assert.equal(Indexer.Sizes.get('A')!.ls, 0); // lead size

        Indexer.Sizes.forEach((_, key) => {
            assert.equal(
                Indexer.Hards.get(key[0]),
                Indexer.Sizes.get(key)!.hs,
                `${key} hs not set`
            );
        });

        Indexer.Sizes.forEach((val, key) => {
            assert.equal(val.hs > 0, true, `${key} hs incorrect`);
            assert.equal(val.ss > 0, true);
            assert.equal(val.os >= 0, true);
            if (val.os > 0) {
                assert.equal(
                    val.os == Math.floor(val.ss / 2),
                    true,
                    `${key} os/ss incorrect`
                );
            }
            if (val.fs != undefined) {
                assert.equal(
                    val.fs >= val.hs + val.ss,
                    true,
                    `${key} fs incorrect`
                );
                assert.equal(val.fs % 4 == 0, true, `${key} fs mod incorrect`);
            }
        });

        assert.throws(() => {
            new Indexer({});
        });

        // sig = (b"\x99\xd2<9$$0\x9fk\xfb\x18\xa0\x8c@r\x122.k\xb2\xc7\x1fp\x0e'm\x8f@"
        //            b'\xaa\xa5\x8c\xc8n\x85\xc8!\xf6q\x91p\xa9\xec\xcf\x92\xaf)\xde\xca'
        //            b'\xfc\x7f~\xd7o|\x17\x82\x1d\xd4<o"\x81&\t')
        const sig = new Uint8Array([
            153, 210, 60, 57, 36, 36, 48, 159, 107, 251, 24, 160, 140, 64, 114,
            18, 50, 46, 107, 178, 199, 31, 112, 14, 39, 109, 143, 64, 170, 165,
            140, 200, 110, 133, 200, 33, 246, 113, 145, 112, 169, 236, 207, 146,
            175, 41, 222, 202, 252, 127, 126, 215, 111, 124, 23, 130, 29, 212,
            60, 111, 34, 129, 38, 9,
        ]);
        assert.equal(sig.length, 64);
        const ps = (3 - (sig.length % 3)) % 3;
        const bytes = new Uint8Array(ps + sig.length);
        for (let i = 0; i < ps; i++) {
            bytes[i] = 0;
        }
        for (let i = 0; i < sig.length; i++) {
            const odx = i + ps;
            bytes[odx] = sig[i];
        }
        const sig64 = encodeBase64Url(bytes);
        assert.equal(sig64.length, 88);
        assert.equal(
            sig64,
            'AACZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ'
        );

        const qsc = IdrDex.Ed25519_Sig + intToB64(0, 1);
        assert.equal(qsc, 'AA');
        let qsig64 = qsc + sig64.slice(ps); // replace prepad chars with clause
        assert.equal(
            qsig64,
            'AACZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ'
        );
        assert.equal(qsig64.length, 88);
        let qsig64b = b(qsig64);

        let qsig2b = decodeBase64Url(qsig64);
        assert.equal(qsig2b.length, 66);
        // assert qsig2b == (b"\x00\x00\x99\xd2<9$$0\x9fk\xfb\x18\xa0\x8c@r\x122.k\xb2\xc7\x1fp\x0e'm"
        // b'\x8f@\xaa\xa5\x8c\xc8n\x85\xc8!\xf6q\x91p\xa9\xec\xcf\x92\xaf)'
        // b'\xde\xca\xfc\x7f~\xd7o|\x17\x82\x1d\xd4<o"\x81&\t')
        assert.deepStrictEqual(
            qsig2b,
            new Uint8Array([
                0, 0, 153, 210, 60, 57, 36, 36, 48, 159, 107, 251, 24, 160, 140,
                64, 114, 18, 50, 46, 107, 178, 199, 31, 112, 14, 39, 109, 143,
                64, 170, 165, 140, 200, 110, 133, 200, 33, 246, 113, 145, 112,
                169, 236, 207, 146, 175, 41, 222, 202, 252, 127, 126, 215, 111,
                124, 23, 130, 29, 212, 60, 111, 34, 129, 38, 9,
            ])
        );

        let indexer = new Indexer({ raw: sig });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.index, 0);
        assert.equal(indexer.ondex, 0);
        assert.equal(indexer.qb64, qsig64);

        indexer._exfil(qsig64);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.index, 0);
        assert.equal(indexer.ondex, 0);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);

        const longsig = new Uint8Array(sig.length + 3);
        longsig.set(sig);
        longsig.set(new Uint8Array([10, 11, 12]), sig.length);
        indexer = new Indexer({ raw: longsig });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.index, 0);
        assert.equal(indexer.ondex, 0);

        const shortsig = sig.slice(0, sig.length - 3);
        assert.throws(() => {
            new Indexer({ raw: shortsig });
        });

        indexer = new Indexer({ qb64b: qsig64b });
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.index, 0);
        assert.equal(indexer.ondex, 0);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);
        assert.deepStrictEqual(indexer.qb64, qsig64);

        indexer = new Indexer({ qb64: qsig64 });
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.index, 0);
        assert.equal(indexer.ondex, 0);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);
        assert.deepStrictEqual(indexer.qb64, qsig64);

        const badq64sig2 =
            'AA_Z0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ';
        assert.throws(() => {
            new Indexer({ qb64: badq64sig2 });
        });

        const longqsig64 = qsig64 + 'ABCD';
        indexer = new Indexer({ qb64: longqsig64 });
        assert.equal(indexer.qb64.length, Indexer.Sizes.get(indexer.code)!.fs);

        const shortqsig64 = qsig64.slice(0, -4);
        assert.throws(() => {
            new Indexer({ qb64: shortqsig64 });
        });

        qsig64 =
            'AFCZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ';
        qsig64b = b(qsig64);
        qsig2b = decodeBase64Url(qsig64);
        assert.equal(qsig2b.length, 66);

        indexer = new Indexer({ raw: sig, code: IdrDex.Ed25519_Sig, index: 5 });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.index, 5);
        assert.equal(indexer.ondex, 5);
        assert.equal(indexer.qb64, qsig64);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);
        indexer._exfil(qsig64);
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.qb64, qsig64);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);

        indexer = new Indexer({
            raw: sig,
            code: IdrDex.Ed25519_Sig,
            index: 5,
            ondex: 5,
        });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.index, 5);
        assert.equal(indexer.ondex, 5);
        assert.equal(indexer.qb64, qsig64);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);

        assert.throws(() => {
            new Indexer({
                raw: sig,
                code: IdrDex.Ed25519_Sig,
                index: 5,
                ondex: 0,
            });
        });

        assert.throws(() => {
            new Indexer({
                raw: sig,
                code: IdrDex.Ed25519_Sig,
                index: 5,
                ondex: 64,
            });
        });

        indexer = new Indexer({ raw: sig });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.index, 0);
        assert.equal(indexer.ondex, 0);
        assert.notEqual(indexer.qb64, qsig64);
        assert.notDeepEqual(indexer.qb64b, qsig64b);

        indexer = new Indexer({ qb64: qsig64 });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Sig);
        assert.equal(indexer.index, 5);
        assert.equal(indexer.ondex, 5);
        assert.equal(indexer.qb64, qsig64);
        assert.deepStrictEqual(indexer.qb64b, qsig64b);

        // test index too big
        assert.throws(() => {
            new Indexer({ raw: sig, code: IdrDex.Ed25519_Sig, index: 65 });
        });

        // test negative index
        assert.throws(() => {
            new Indexer({ raw: sig, code: IdrDex.Ed25519_Sig, index: -1 });
        });

        // test non integer index
        assert.throws(() => {
            new Indexer({ raw: sig, code: IdrDex.Ed25519_Sig, index: 3.5 });
        });

        let index = 67;
        let qb64 =
            '2ABDBDCZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ';
        let qb64b = b(qb64);

        indexer = new Indexer({
            raw: sig,
            code: IdrDex.Ed25519_Big_Sig,
            index: index,
        });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Big_Sig);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, index);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        indexer = new Indexer({
            raw: sig,
            code: IdrDex.Ed25519_Big_Sig,
            index: index,
            ondex: index,
        });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Big_Sig);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, index);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        indexer = new Indexer({ qb64: qb64 });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Big_Sig);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, index);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        index = 90;
        const ondex = 65;
        qb64 =
            '2ABaBBCZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ';
        qb64b = b(qb64);

        indexer = new Indexer({
            raw: sig,
            code: IdrDex.Ed25519_Big_Sig,
            index: index,
            ondex: ondex,
        });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Big_Sig);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, ondex);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        indexer = new Indexer({ qb64: qb64 });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, IdrDex.Ed25519_Big_Sig);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, ondex);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        index = 3;
        let code = IdrDex.Ed25519_Crt_Sig;
        qb64 =
            'BDCZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ';
        qb64b = b(qb64);

        indexer = new Indexer({ raw: sig, code: code, index: index });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, code);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, undefined);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        indexer = new Indexer({ qb64: qb64 });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, code);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, undefined);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        assert.throws(() => {
            new Indexer({ raw: sig, code: code, index: index, ondex: index });
        });

        // test negative index
        assert.throws(() => {
            new Indexer({
                raw: sig,
                code: code,
                index: index,
                ondex: index + 2,
            });
        });

        index = 68;
        code = IdrDex.Ed25519_Big_Crt_Sig;
        qb64 =
            '2BBEAACZ0jw5JCQwn2v7GKCMQHISMi5rsscfcA4nbY9AqqWMyG6FyCH2cZFwqezPkq8p3sr8f37Xb3wXgh3UPG8igSYJ';
        qb64b = b(qb64);

        indexer = new Indexer({ raw: sig, code: code, index: index });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, code);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, undefined);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        indexer = new Indexer({ qb64: qb64 });
        assert.deepStrictEqual(indexer.raw, sig);
        assert.equal(indexer.code, code);
        assert.equal(indexer.index, index);
        assert.equal(indexer.ondex, undefined);
        assert.equal(indexer.qb64, qb64);
        assert.deepStrictEqual(indexer.qb64b, qb64b);

        assert.throws(() => {
            new Indexer({ raw: sig, code: code, index: index, ondex: index });
        });

        // test negative index
        assert.throws(() => {
            new Indexer({
                raw: sig,
                code: code,
                index: index,
                ondex: index + 2,
            });
        });
    });
});
