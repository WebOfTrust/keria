import { MtrDex } from '../../src/keri/core/matter.ts';
import libsodium from 'libsodium-wrappers-sumo';
import { assert, describe, it, expect, beforeAll } from 'vitest';
import { Verfer } from '../../src/keri/core/verfer.ts';
import { p256 } from '@noble/curves/p256';
import { b } from 'signify-ts';

beforeAll(async () => {
    await libsodium.ready;
});

describe('Verfer', () => {
    describe('Ed25519', () => {
        const seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
        const keypair = libsodium.crypto_sign_seed_keypair(seed);

        it('should create verfer', async () => {
            const verkey = keypair.publicKey;

            const verfer = new Verfer({
                raw: keypair.publicKey,
                code: MtrDex.Ed25519N,
            });

            assert.deepStrictEqual(verfer.raw, verkey);
            assert.deepStrictEqual(verfer.code, MtrDex.Ed25519N);
        });

        it('should verify signature', () => {
            const verfer = new Verfer({
                raw: keypair.publicKey,
                code: MtrDex.Ed25519N,
            });
            const ser = 'abcdefghijklmnopqrstuvwxyz0123456789';

            const sig = libsodium.crypto_sign_detached(ser, keypair.privateKey);

            assert.equal(verfer.verify(sig, ser), true);
        });

        it('should create verfer from qb64', async () => {
            const verfer = new Verfer({
                qb64: 'BGgVB5Aar1pOr70nRpJmRA_RP68HErflNovoEMP7b7mJ',
            });

            assert.deepStrictEqual(
                verfer.raw,
                new Uint8Array([
                    104, 21, 7, 144, 26, 175, 90, 78, 175, 189, 39, 70, 146,
                    102, 68, 15, 209, 63, 175, 7, 18, 183, 229, 54, 139, 232,
                    16, 195, 251, 111, 185, 137,
                ])
            );
        });
    });

    describe('secp256r1', () => {
        const privateKey = new Uint8Array([
            138, 17, 14, 173, 86, 68, 80, 39, 61, 52, 208, 154, 211, 190, 21,
            99, 156, 134, 184, 90, 166, 171, 226, 251, 239, 132, 127, 221, 144,
            51, 245, 71,
        ]);

        const publicKey = p256.getPublicKey(privateKey);

        it('should create verfer', async () => {
            const verfer = new Verfer({
                raw: publicKey,
                code: MtrDex.ECDSA_256r1,
            });

            assert.deepStrictEqual(verfer.raw, publicKey);
            assert.deepStrictEqual(verfer.code, MtrDex.ECDSA_256r1);
            assert.equal(
                verfer.qb64,
                '1AAJA-blKBTkTkEEOX_Yq3i3KxZJvcHarPfu_crKVwcfEwvQ'
            );
        });

        it('should verify secp256r1', async () => {
            const verfer = new Verfer({
                raw: publicKey,
                code: MtrDex.ECDSA_256r1,
            });

            const ser = 'abcdefghijklmnopqrstuvwxyz0123456789';

            const sig = p256.sign(b(ser), privateKey).toCompactRawBytes();

            assert.deepEqual(
                sig,
                new Uint8Array([
                    56, 81, 180, 93, 192, 44, 174, 128, 161, 173, 226, 227, 149,
                    26, 203, 255, 36, 189, 144, 110, 163, 51, 67, 138, 99, 130,
                    38, 189, 16, 170, 164, 77, 167, 254, 123, 220, 149, 72, 71,
                    28, 32, 66, 213, 177, 197, 158, 195, 234, 167, 109, 207,
                    174, 15, 221, 245, 85, 120, 226, 224, 33, 94, 89, 115, 49,
                ])
            );

            assert.equal(verfer.verify(sig, ser), true);
        });

        it('should parse qb64', () => {
            const verfer = new Verfer({
                qb64: '1AAJAwf0oSqmdjPud5gnK6bAPKkBLrXUMQZiOW4Vpc4XpOPf',
            });

            assert.deepStrictEqual(
                verfer.raw,
                new Uint8Array([
                    3, 7, 244, 161, 42, 166, 118, 51, 238, 119, 152, 39, 43,
                    166, 192, 60, 169, 1, 46, 181, 212, 49, 6, 98, 57, 110, 21,
                    165, 206, 23, 164, 227, 223,
                ])
            );
        });
    });

    it('should not verify secp256k1', async () => {
        const publicKey = new Uint8Array([
            2, 79, 93, 30, 107, 249, 254, 237, 205, 87, 8, 149, 203, 214, 36,
            187, 162, 251, 58, 206, 241, 203, 27, 76, 236, 37, 189, 148, 240,
            178, 204, 133, 31,
        ]);

        expect(() => {
            new Verfer({ raw: publicKey, code: MtrDex.ECDSA_256k1 });
        }).toThrow(new Error(`Unsupported code = 1AAB for verifier.`));
    });
});
