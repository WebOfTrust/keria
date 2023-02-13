import {MtrDex} from "../../src/keri/core/matter";

import libsodium from "libsodium-wrappers-sumo"

import {strict as assert} from "assert";


import { Verfer } from '../../src/keri/core/verfer';

describe('Verfer', () => {
  it('should verify digests', async () => {
    await libsodium.ready;
    let seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
    const keypair = libsodium.crypto_sign_seed_keypair(seed);

    let verkey = keypair.publicKey;
    let sigkey = keypair.privateKey;

    let verfer = new Verfer({raw: verkey, code: MtrDex.Ed25519N})
    assert.notEqual(verfer, null)

    assert.deepStrictEqual(verfer.raw, verkey);
    assert.deepStrictEqual(verfer.code, MtrDex.Ed25519N);

    let ser = 'abcdefghijklmnopqrstuvwxyz0123456789'

    let sig = libsodium.crypto_sign_detached(ser, sigkey)

    assert.equal(verfer.verify(sig, ser), true)

    verfer = new Verfer({qb64: "BGgVB5Aar1pOr70nRpJmRA_RP68HErflNovoEMP7b7mJ"})
    assert.deepStrictEqual(verfer.raw, new Uint8Array([104, 21, 7, 144, 26, 175, 90, 78, 175, 189, 39, 70, 146,
      102, 68, 15, 209, 63, 175, 7, 18, 183, 229, 54, 139, 232, 16, 195, 251, 111, 185, 137]))
  });
});


