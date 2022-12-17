import libsodium from "libsodium-wrappers-sumo";
import {Signer} from "../../src/keri/core/signer";
import {Matter, MtrDex} from "../../src/keri/core/matter";
import {strict as assert} from "assert";
import {Salter} from "../../src/keri/core/salter";
import {Decrypter} from "../../src/keri/core/decrypter";
import {Encrypter} from "../../src/keri/core/encrypter";
import {TextEncoder} from 'util'


describe('Decrypter', () => {
    it('should decrypt stuff', async () => {
        await libsodium.ready;

        // (b'\x18;0\xc4\x0f*vF\xfa\xe3\xa2Eee\x1f\x96o\xce)G\x85\xe3X\x86\xda\x04\xf0\xdc\xde\x06\xc0+')
        let seed = new Uint8Array([24, 59, 48, 196, 15, 42, 118, 70, 250, 227, 162, 69, 101, 101, 31, 150, 111, 206, 41, 71, 133, 227, 88, 134, 218, 4, 240, 220, 222, 6, 192, 43])

        let signer = new Signer({raw: seed, code: MtrDex.Ed25519_Seed})
        assert.equal(signer.verfer.code, MtrDex.Ed25519)
        assert.equal(signer.verfer.transferable, true)  // default
        let seedqb64 = signer.qb64
        let seedqb64b = signer.qb64b
        assert.equal(seedqb64, 'ABg7MMQPKnZG-uOiRWVlH5ZvzilHheNYhtoE8NzeBsAr')

        // also works for Matter
        assert.deepStrictEqual(seedqb64b, new Matter({raw: seed, code: MtrDex.Ed25519_Seed}).qb64b)

        // raw = b'6\x08d\r\xa1\xbb9\x8dp\x8d\xa0\xc0\x13J\x87r'
        let raw = new Uint8Array([54, 8, 100, 13, 161, 187, 57, 141, 112, 141, 160, 192, 19, 74, 135, 114])
        let salter = new Salter({raw: raw, code: MtrDex.Salt_128})
        assert.equal(salter.code, MtrDex.Salt_128)
        let saltqb64 = salter.qb64
        let saltqb64b = salter.qb64b
        assert.deepStrictEqual(saltqb64, '0AA2CGQNobs5jXCNoMATSody')

        // also works for Matter
        assert.deepStrictEqual(saltqb64b, new Matter({raw: raw, code: MtrDex.Salt_128}).qb64b)

        // cryptseed = b'h,#|\x8ap"\x12\xc43t2\xa6\xe1\x18\x19\xf0f2,y\xc4\xc21@\xf5@\x15.\xa2\x1a\xcf'
        let cryptseed = new Uint8Array([104, 44, 35, 124, 138, 112, 34, 18, 196, 51, 116, 50, 166, 225, 24, 25, 240, 102, 50, 44, 121, 196, 194, 49, 64, 245, 64, 21, 46, 162, 26, 207])
        let cryptsigner = new Signer({raw: cryptseed, code: MtrDex.Ed25519_Seed, transferable: true})
        let keypair = libsodium.crypto_sign_seed_keypair(cryptseed)  // raw
        let pubkey = libsodium.crypto_sign_ed25519_pk_to_curve25519(keypair.publicKey)
        let prikey = libsodium.crypto_sign_ed25519_sk_to_curve25519(keypair.privateKey)

        assert.throws(function() {
            new Decrypter({})
        });

        // create encrypter
        let encrypter = new Encrypter({raw: pubkey})
        assert.equal(encrypter.code, MtrDex.X25519)
        assert.equal(encrypter.qb64, 'CAF7Wr3XNq5hArcOuBJzaY6Nd23jgtUVI6KDfb3VngkR')
        assert.deepStrictEqual(encrypter.raw, pubkey)

        // create cipher of seed
        let seedcipher = encrypter.encrypt(seedqb64b)
        assert.equal(seedcipher.code, MtrDex.X25519_Cipher_Seed)
        // each encryption uses a nonce so not a stable representation for testing

        // create decrypter from prikey
        let decrypter = new Decrypter({raw: prikey})
        assert.equal(decrypter.code, MtrDex.X25519_Private)
        assert.equal(decrypter.qb64, 'OLCFxqMz1z1UUS0TEJnvZP_zXHcuYdQsSGBWdOZeY5VQ')
        assert.deepStrictEqual(decrypter.raw, prikey)

       // decrypt seed cipher using ser
        let designer = decrypter.decrypt(seedcipher.qb64b, null, signer.verfer.transferable)
        assert.deepStrictEqual(designer.qb64b, seedqb64b)
        assert.equal(designer.code, MtrDex.Ed25519_Seed)
        assert.equal(designer.verfer.code, MtrDex.Ed25519)
        assert.equal(signer.verfer.transferable, true)

        // decrypt seed cipher using cipher
        designer = decrypter.decrypt(null, seedcipher, signer.verfer.transferable)
        assert.deepStrictEqual(designer.qb64b, seedqb64b)
        assert.equal(designer.code, MtrDex.Ed25519_Seed)
        assert.equal(designer.verfer.code, MtrDex.Ed25519)
        assert.equal(signer.verfer.transferable, true)

        // create cipher of salt
        let saltcipher = encrypter.encrypt(saltqb64b)
        assert.equal(saltcipher.code, MtrDex.X25519_Cipher_Salt)
        // each encryption uses a nonce so not a stable representation for testing

        // decrypt salt cipher using ser
        let desalter = decrypter.decrypt(saltcipher.qb64b)
        assert.deepStrictEqual(desalter.qb64b, saltqb64b)
        assert.equal(desalter.code, MtrDex.Salt_128)

        // decrypt salt cipher using cipher
        desalter = decrypter.decrypt(null, saltcipher)
        assert.deepStrictEqual(desalter.qb64b, saltqb64b)
        assert.equal(desalter.code, MtrDex.Salt_128)

        // use previously stored fully qualified seed cipher with different nonce
        // get from seedcipher above
        let cipherseed = 'PM9jOGWNYfjM_oLXJNaQ8UlFSAV5ACjsUY7J16xfzrlpc9Ve3A5WYrZ4o_NHtP5lhp78Usspl9fyFdnCdItNd5JyqZ6dt8SXOt6TOqOCs-gy0obrwFkPPqBvVkEw'
        designer = decrypter.decrypt(new TextEncoder().encode(cipherseed), null, signer.verfer.transferable)
        assert.deepStrictEqual(designer.qb64b, seedqb64b)
        assert.equal(designer.code, MtrDex.Ed25519_Seed)
        assert.equal(designer.verfer.code, MtrDex.Ed25519)

        // use previously stored fully qualified salt cipher with different nonce
        // get from saltcipher above
        let ciphersalt = '1AAHjlR2QR9J5Et67Wy-ZaVdTryN6T6ohg44r73GLRPnHw-5S3ABFkhWyIwLOI6TXUB_5CT13S8JvknxLxBaF8ANPK9FSOPD8tYu'
        desalter = decrypter.decrypt(new TextEncoder().encode(ciphersalt))
        assert.deepStrictEqual(desalter.qb64b, saltqb64b)
        assert.equal(desalter.code, MtrDex.Salt_128)

        // Create new decrypter but use seed parameter to init prikey
        decrypter = new Decrypter({}, cryptsigner.qb64b)
        assert.equal(decrypter.code, MtrDex.X25519_Private)
        assert.equal(decrypter.qb64, 'OLCFxqMz1z1UUS0TEJnvZP_zXHcuYdQsSGBWdOZeY5VQ')
        assert.deepStrictEqual(decrypter.raw, prikey)

        // decrypt ciphersalt
        desalter = decrypter.decrypt(saltcipher.qb64b)
        assert.deepStrictEqual(desalter.qb64b, saltqb64b)
        assert.equal(desalter.code, MtrDex.Salt_128)
    });
});