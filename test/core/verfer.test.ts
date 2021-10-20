const libsodium = require('libsodium-wrappers-sumo');
const Base64 = require('urlsafe-base64');
const derivationCodes = require('../../src/keri/core/derivationCodes');
const assert = require('assert').strict;


const { Verfer } = require('../../src/keri/core/verfer');

describe('Verfer', () => {
  it('should verify digests', async () => {
    await libsodium.ready;
    let seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
    const keypair = libsodium.crypto_sign_seed_keypair(seed);

    let verkey = keypair.publicKey;
    let sigkey = keypair.privateKey;
    let pkey = String.fromCharCode.apply(null, sigkey);
    let pkeyb = Buffer.from(pkey, 'binary');

    console.log("sigkey----> ", Base64.encode(pkeyb))
    verkey = String.fromCharCode.apply(null, verkey);
    verkey = Buffer.from(verkey, 'binary');
    console.log('verkey-------------->', Base64.encode(verkey));
    const verfer = new Verfer(
        Buffer.from(verkey, 'binary'),
        null,
        null,
        derivationCodes.oneCharCode.Ed25519N,
    );
    assert.deepStrictEqual(verfer.raw(), verkey);
    assert.deepStrictEqual(verfer.code(), derivationCodes.oneCharCode.Ed25519N);
  });
});


