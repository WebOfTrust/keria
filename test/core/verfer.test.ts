import {MtrDex} from "../../src/keri/core/matter";
import libsodium from "libsodium-wrappers-sumo"
import {strict as assert} from "assert";
import { Verfer } from '../../src/keri/core/verfer';
import secp256r1 from "ecdsa-secp256r1"

function base64ToUint8Array(base64:string) {
  var binaryString = atob(base64);
  var bytes = new Uint8Array(binaryString.length);
  for (var i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
  }
  return new Uint8Array(bytes.buffer);
}


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
  it('should verify secp256r1', async () => {
    await libsodium.ready;
    // let seed = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
    // const keypair = libsodium.crypto_sign_seed_keypair(seed);

    const privateKey = secp256r1.generateKey()
    const publicKey = base64ToUint8Array(privateKey.toCompressedPublicKey())
    let verfer = new Verfer({raw: publicKey, code: MtrDex.ECDSA_256r1})
    assert.notEqual(verfer, null)

    assert.deepStrictEqual(verfer.raw, publicKey);
    assert.deepStrictEqual(verfer.code, MtrDex.ECDSA_256r1);

    let ser = 'abcdefghijklmnopqrstuvwxyz0123456789'

    let sig = privateKey.sign(ser)

    assert.equal(verfer.verify(sig, ser), true)

    verfer = new Verfer({qb64: "1AAJAwf0oSqmdjPud5gnK6bAPKkBLrXUMQZiOW4Vpc4XpOPf"})
    assert.deepStrictEqual(verfer.raw, new Uint8Array([
          3,   7, 244, 161,  42, 166, 118,  51,
        238, 119, 152,  39,  43, 166, 192,  60,
        169,   1,  46, 181, 212,  49,   6,  98,
        57, 110,  21, 165, 206,  23, 164, 227,
        223
      ]))
  });
});


