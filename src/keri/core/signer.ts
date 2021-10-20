export {};
const libsodium = require('libsodium-wrappers-sumo');
const { Crymat } = require('./cryMat');
const derivationCodes = require('./derivationCodes');
const { Verfer } = require('./verfer');
const { Sigver } = require('./sigver');
const { Siger } = require('./siger');
const { range } = require('./utls');

/**
 * @description Signer is CryMat subclass with method to create signature of serialization
 * It will use .raw as signing (private) key seed
 * .code as cipher suite for signing and new property .verfer whose property
 *  .raw is public key for signing.
 *  If not provided .verfer is generated from private key seed using .code
    as cipher suite for creating key-pair.
 */

class Signer extends Crymat {
  constructor(
    raw = null,
    code = derivationCodes.oneCharCode.Ed25519_Seed,
    transferable = true,
    // lib = null,
    qb64 = null,
  ) {
    let setVerfer;
    let seedKeypair;
    try {
   
      super(raw, qb64, null, code);
    } catch (error) {
      if (code === derivationCodes.oneCharCode.Ed25519_Seed) {
        raw = libsodium.randombytes_buf(libsodium.crypto_sign_SEEDBYTES);
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'Buffer' is not assignable to type 'null'.
        raw = Buffer.from(raw, 'binary');
        super(raw, null, null, code);
      } else {
        throw new Error(`Unsupported signer code = ${code}.`);
      }
    }
    if (code === derivationCodes.oneCharCode.Ed25519_Seed) {
      this.getSign = this.ed25519;
      if (raw == null) {
        raw = this.raw();
      }
      seedKeypair = libsodium.crypto_sign_seed_keypair(raw);
      const verkey = Buffer.from(seedKeypair.publicKey, 'binary');

      this.sigkey = Buffer.from(seedKeypair.privateKey, 'binary');
      if (transferable) {
        setVerfer = new Verfer(
          verkey,
          null,
          null,
          derivationCodes.oneCharCode.Ed25519,
        );
      } else {
        setVerfer = new Verfer(
          verkey,
          null,
          null,
          derivationCodes.oneCharCode.Ed25519N,
        );
      }
    } else {
      throw new Error(
        `Unsupported signer code = ${derivationCodes.oneCharCode.Ed25519N}.`,
      );
    }
    this.getVerfer = setVerfer;
  }

  static async initLibsodium() {
    await libsodium.ready;
  }

  /**
 * @description Property verfer:
        Returns Verfer instance
        Assumes ._verfer is correctly assigned
 */
  verfer() {
    return this.getVerfer;
  }

  /**
 * @description Returns either Sigver or Siger (indexed) instance of cryptographic
        signature material on bytes serialization ser

         If index is None
            return Sigver instance
        Else
            return Siger instance

             ser is bytes serialization
            index is int index of associated verifier key in event keys
 * @param {*} ser
 * @param {*} index
 */
  sign(ser: any, index = null) {
    return this.getSign(ser, this.raw(), this.verfer(), index);
  }

  /**
   * @description Returns signature
   * @param {*} ser ser is bytes serialization
   * @param {*} seed seed is bytes seed (private key)
   * @param {*} verfer verfer is Verfer instance. verfer.raw is public key
   * @param {*} index index is index of offset into signers list or None
   */
  // eslint-disable-next-line class-methods-use-this
  ed25519(ser: any, seed: any, verfer: any, index: any) {
    let sig = libsodium.crypto_sign_detached(
      ser,
      Buffer.concat([seed, verfer.raw()]),
    );
    sig = Buffer.from(sig, 'binary');
    if (index == null) {
      const response = new Sigver(
        sig,
        derivationCodes.twoCharCode.Ed25519,
        verfer,
      );
      response.setVerfer(verfer);
      return response;
    }
    const args = [sig, null, null, derivationCodes.SigTwoCodex.Ed25519];
    return new Siger(verfer, ...args);
  }
}

/**
     * @description Returns list of Signers for Ed25519
     * @param {*} root          root is bytes 16 byte long root key (salt/seed) from
     *                          which seeds for Signers
                                in list are derived
                                 random root created if not provided
     * @param {*} count          count is number of signers in list
     * @param {*} transferable transferable is boolean true means signer.verfer code is transferable
                                non-transferable otherwise
     */
async function generateSigners(root = null, count = 8) {
  await libsodium.ready;
  if (!root) {
    root = libsodium.randombytes_buf(libsodium.crypto_pwhash_SALTBYTES);
  }
  const signers = [];
  // @ts-expect-error ts-migrate(2461) FIXME: Type 'null' is not an array type.
  let [path, seed] = null;
  for (const i in range(count)) {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 0 arguments, but got 1.
    path = i.toString(16);
    seed = libsodium.crypto_pwhash(
      32,
      path,
      root,
      libsodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,
      libsodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,
      // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'alg'.
      (alg = libsodium.crypto_pwhash_ALG_DEFAULT),
    );
    signers.push(new Signer(seed));
  }
  return signers;
}

/**
     * @description  Returns list of fully qualified Base64 secret seeds for Ed25519 private keys
     * @param {*} root root is bytes 16 byte long root key (salt/seed) from which seeds for Signers
            in list are derived
            random root created if not provided
     * @param {*} count count is number of signers in list
     */
function generateSecrets(root = null, count = 8) {
  const signrs: any = [];
  const signers = generateSigners(root, count);

  for (const signer in signers) {
    signrs.push[(signer as any).qb64()];
  }

  return signrs;
}

module.exports = { Signer, generateSigners, generateSecrets };
