/* eslint-disable class-methods-use-this */
/* eslint-disable no-underscore-dangle */
export {};
const blake3 = require('blake3');
const libsodium = require('libsodium-wrappers-sumo');
const { Crymat } = require('./cryMat');
const { extractValues } = require('./utls');
const derivationCodes = require('./derivationCodes');
const { Verfer } = require('./verfer');

const { Sigver } = require('./sigver');
const { Ilks, IcpLabels, DipLabels, IcpExcludes } = require('./core');
const { Serder } = require('./serder');
const { Signer } = require('./signer');

/**
 * @description Prefixer is CryMat subclass for autonomic identifier prefix using basic derivation
    from public key
    inherited attributes and properties:
    Attributes:
    Properties:
    Methods:verify():  Verifies derivation of aid
 */

export class Prefixer extends Crymat {
  //        elements in digest or signature derivation from inception icp
  //  IcpLabels ["sith", "keys", "nxt", "toad", "wits", "cnfg"]

  //  elements in digest or signature derivation from delegated inception dip
  //  DipLabels  ["sith", "keys", "nxt", "toad", "wits", "perm", "seal"]

  /**
   * @description  // This constructor will assign
   *  ._verify to verify derivation of aid  = .qb64
   */
  constructor(
    raw?: Buffer,
    code = derivationCodes.oneCharCode.Ed25519N,
    ked = {},
    seed?:Uint8Array,
    secret = null,
    qb64 = null,
    qb2 = null,
  ) {
    let deriveFunc = null;

    try {
      super(raw, qb64, qb2, code);
    } catch (error) {
      if (!(ked || code)) throw error; // throw error if no ked found

      if (code === derivationCodes.oneCharCode.Ed25519N) {
        deriveFunc = DeriveBasicEd25519N;
      } else if (code === derivationCodes.oneCharCode.Ed25519) {
        deriveFunc = DeriveBasicEd25519;
      } else if (code === derivationCodes.oneCharCode.Blake3_256) {
        deriveFunc = DeriveDigBlake3_256;
      } else if (code === derivationCodes.twoCharCode.Ed25519) {
        deriveFunc = DeriveSigEd25519;
      } else throw new Error(`Unsupported code = ${code} for prefixer.`);

      const verfer = deriveFunc(ked, seed, secret); // else obtain AID using ked
      super(verfer.raw, null, null, verfer.code, 0);
    }

    if (this.getCode === derivationCodes.oneCharCode.Ed25519N) {
      this.verifyDerivation = this.VerifyBasicEd25519N;
    } else if (this.getCode === derivationCodes.oneCharCode.Ed25519) {
      this.verifyDerivation = this.VerifyBasicEd25519;
    } else if (this.getCode === derivationCodes.oneCharCode.Blake3_256) {
      this.verifyDerivation = this.verifyDigBlake3_256;
    } else if (this.getCode === derivationCodes.twoCharCode.Ed25519) {
      this.verifyDerivation = this.VerifySigEd25519;
    } else throw new Error(`Unsupported code = ${this.code()} for prefixer.`);
  }

  static async initLibsodium() {
    await libsodium.ready;
  }

  /**
   * @description   Returns tuple (raw, code) of basic nontransferable
   * Ed25519 prefix (qb64) as derived from key event dict ke
   * @param {*} ked  ked is inception key event dict
   * @param {*} seed seed is only used for sig derivation it is the secret key/secret
   * @param {*} secret secret or private key
   */
  // @ts-expect-error ts-migrate(7023) FIXME: 'derive' implicitly has return type 'any' because ... Remove this comment to see the full error message
  derive(ked: any, seed = null, secret = null) {
    return this.derive(ked, seed, secret);
  }

  /**
   * @description  This function will return TRUE if derivation from iked for .code matches .qb64
   * @param {*} ked inception key event dict
   */
  verify(ked: any) {
    return this.verifyDerivation(ked, this.qb64());
  }

  /**
     * @description This will return  True if verified raises exception otherwise
            Verify derivation of fully qualified Base64 pre from inception iked dict
     * @param {*} ked    ked is inception key event dict
     * @param {*} pre   pre is Base64 fully qualified prefix
     */
  // eslint-disable-next-line class-methods-use-this
  VerifyBasicEd25519N(ked: any, pre: any) {
    let keys = null;

    try {
      keys = ked.keys;
      if (keys.length !== 1) {
        return false;
      }
      if (keys[0] !== pre) { return false; }
      if (ked.nxt) {
        return false; }
    } catch (e) {
      return false;
    }
    return true;
  }

  /**
     * @description  Returns True if verified raises exception otherwise
                     Verify derivation of fully qualified Base64 prefix from
                     inception key event dict (ked)
     * @param {*} ked    ked is inception key event dict
     * @param {*} pre   pre is Base64 fully qualified prefix
     */
  // eslint-disable-next-line class-methods-use-this
  VerifyBasicEd25519(ked: any, pre: any) {
    const { keys } = ked;
    try {
      if (keys.length !== 1) return false;
      if (keys[0] !== pre) {
        return false;
      }
    } catch (e) {
      return false;
    }
    return true;
  }

  /**
     * @description : Verify derivation of fully qualified Base64 prefix from
                      inception key event dict (ked). returns TRUE if verified else raise exception
             * @param {*} ked    ked is inception key event dict
             * @param {*} pre   pre is Base64 fully qualified prefix
     */
  // eslint-disable-next-line camelcase
  verifyDigBlake3_256(ked: any, pre: any) {
    // @ts-expect-error ts-migrate(2569) FIXME: Type 'string' is not an array type or a string typ... Remove this comment to see the full error message
    let [raw, code, response, crymat] = '';
    try {
      response = DeriveDigBlake3_256(ked);
      raw = response.raw;
      code = response.code;

      crymat = new Crymat(raw, null, null, code);
      if (crymat.qb64() !== pre) return false;
    } catch (error) {
      return false;
    }
    return true;
  }

  /**
* @description : Verify derivation of fully qualified Base64 prefix from
    inception key event dict (ked). returns TRUE if verified else raise exception
     * @param {*} ked    ked is inception key event dict
     * @param {*} pre   pre is Base64 fully qualified prefix
     */
  // eslint-disable-next-line no-underscore-dangle
  // eslint-disable-next-line class-methods-use-this
  VerifySigEd25519(ked: any, pre: any) {
    let ilk = null;
    let labels;
    let values;
    let ser;
    const keys = ked.keys;
    let verfer;
    let sigver = null;
    try {
      ilk = ked.ilk;
      if (ilk === Ilks.icp) labels = IcpLabels;
      if (ilk === Ilks.icp) labels = DipLabels;
      else throw new Error(`Invalid ilk = ${ilk} to derive pre.`);

      for (const l in labels) {
        if (!Object.values(ked).includes(l)) {
          throw new Error(`Missing element = ${l} from ked.`);
        }
      }


      values = extractValues(ked, labels);
      ser = Buffer.from(''.concat(values), 'utf-8');
      try {
        if (keys.length !== 1) throw new Error(`Basic derivation needs at most 1 key got ${keys.length} keys instead`);
        verfer = new Verfer(null, keys[0]);
      } catch (e) {
        throw new Error(`Error extracting public key = ${e}`);
      }
      if (
        !Object.values(derivationCodes.oneCharCode.Ed25519).includes(
          verfer.code(),
        )
      ) {
        throw new Error(`Invalid derivation code = ${verfer.code()}`);
      }

      sigver = new Sigver(
        null,
        derivationCodes.twoCharCode.Ed25519,
        verfer,
        0,
        pre,
      );
      const result = sigver.verfer().verify(sigver.raw(), ser);
      return result;
    } catch (exception) {
      return false;
    }
  }
}

/**
 * @description  Returns tuple raw, code of basic Ed25519 prefix (qb64)
 as derived from key event dict ked
 * @param {*} ked
 * @param {*} _seed
 * @param {*} _secret
 * @param _code
 */
function DeriveBasicEd25519(
  ked: any,
  _seed?: Uint8Array,
  _secret = null,
  _code = derivationCodes.oneCharCode.Ed25519,
) {
  let verfer = null;
  let keys;
  try {
    keys = ked.keys;
    if (keys.length !== 1) throw new Error(`Basic derivation needs at most 1 key got ${keys.length} keys instead`);

    verfer = new Verfer(null, keys[0]);
  } catch (e) {
    throw new Error(`Error extracting public key = ${e}`);
  }

  if (
    !Object.values(derivationCodes.oneCharCode.Ed25519).includes(verfer.code())
  ) {
    throw new Error(`Invalid derivation code = ${verfer.code()}.`);
  }

  return { raw: verfer.raw(), code: verfer.code() };
}

/**
 * @descriptionReturns return  (raw, code) of basic nontransferable Ed25519 prefix (qb64)
 * @param {*} ked  ked is inception key event dict
 * @param {*} seed seed is only used for sig derivation it is the secret key/secret
 * @param {*} secret secret or private key
 */

function DeriveBasicEd25519N(ked: any) {
  let verfer = null;
  let keys;
  try {
    keys = ked.keys;
    if (keys.length !== 1) throw new Error(`Basic derivation needs at most 1 key got ${keys.length} keys instead`);
    verfer = new Verfer(null, keys[0]);
  } catch (e) {
    throw new Error(`Error extracting public key = ${e}`);
  }

  if (
    !Object.values(derivationCodes.oneCharCode.Ed25519N).includes(
      verfer.code(),
    )
  ) {
    throw new Error(`Invalid derivation code = ${verfer.code()}.`);
  }

  try {
    if (
      Object.values(derivationCodes.oneCharCode.Ed25519N).includes(
        verfer.code(),
      )
      && ked.nxt
    ) {
      throw new Error(`Non-empty nxt = ${
        ked.nxt
      } for non-transferable code = ${verfer.code()}`);
    }
  } catch (e) {
    throw new Error(`Error checking nxt = ${e}`);
  }

  return { raw: verfer.raw(), code: verfer.code() };
}

/**
* @description Returns raw, code of basic Ed25519 pre (qb64)
             as derived from key event dict ked
* @param {*} ked  ked is inception key event dict
* @param {*} seed seed is only used for sig derivation it is the secret key/secret
* @param {*} secret secret or private key
*/
function DeriveDigBlake3_256(ked: any) {
  let labels = [];
  let objKeys = [];
  let values = null;
  let ser = null;
  let dig = null;
  const { ilk } = ked;

  if (ilk === Ilks.icp) {
    objKeys = Object.keys(ked);
    for(let keys in objKeys){
      if(!(IcpExcludes.includes(objKeys[keys]))){
        labels.push(objKeys[keys]);
      }
    }
    // labels = IcpLabels;
  } 
  // if (ilk === Ilks.icp) labels = IcpLabels;
  else if (ilk === Ilks.dip) labels = DipLabels;
  else throw new Error(`Invalid ilk = ${ilk} to derive pre.`);

  ked.pre = 'a'.repeat(
    derivationCodes.CryOneSizes[derivationCodes.oneCharCode.Blake3_256],
  );
  const serder = new Serder(null, ked);
  // serder.set_raw(serder.getRaw);
  ked = serder.ked();
  serder.set_ked(ked);
  // serder.set_kind()
//  serder.set_raw(serder.getRaw);
  // # put in dummy pre to get size correct
  for (let l in labels) {
    if (Object.values(ked).includes(labels[l])) {
      throw new Error(`Missing element = ${l} from ked.`);
    }
  }

  values = extractValues(ked, labels);
  ser = Buffer.from(''.concat(values), 'utf-8');
  const hasher = blake3.createHash();
  dig = hasher.update(ser).digest({length: 64 });

  return { raw: dig, code: derivationCodes.oneCharCode.Blake3_256 };
}

/**
 * @description   Returns  raw, code of basic Ed25519 pre (qb64)
            as derived from key event dict ked
 * @param {*} ked  ked is inception key event dict
 * @param {*} seed seed is only used for sig derivation it is the secret key/secret
 * @param {*} secret secret or private key
 *
 *
 */
function DeriveSigEd25519(ked: any, seed?:Uint8Array, secret = null) {
  let labels = null;
  let values = null;
  let ser = null;
  let keys = null;
  let verfer = null;
  let signer = null;
  let sigver = null;
  const { ilk } = ked;
  if (ilk === Ilks.icp) {
    labels = IcpLabels;
  } else if (ilk === Ilks.dip) {
    labels = DipLabels;
  } else throw new Error(`Invalid ilk = ${ilk} to derive pre.`);

  for (let l in labels) {
    if (!Object.keys(ked).includes(labels[l])) {
      throw new Error(`Missing element = ${labels[l]} from ked.`);
    }
  }
  values = extractValues(ked, labels);
  ser = Buffer.from(''.concat(values), 'utf-8');

  try {
    keys = ked.keys;
    if (keys.length !== 1) throw new Error(`Basic derivation needs at most 1 key  got ${keys.length} keys instead`);
    verfer = new Verfer(null, keys[0]);
  } catch (exception) {
    throw new Error(`extracting public key = ${exception}`);
  }

  if (verfer.code() !== derivationCodes.oneCharCode.Ed25519) throw new Error(`Invalid derivation code = ${verfer.code()}`);
  if (!(seed || secret)) throw new Error('Missing seed or secret.');

  signer = new Signer(seed, derivationCodes.oneCharCode.Ed25519_Seed, true, libsodium, secret);
  if (verfer.raw().toString() !== (signer.verfer().raw()).toString()) throw new Error('Key in ked not match seed.');

  sigver = signer.sign(ser);
  return { raw: sigver.raw(), code: derivationCodes.twoCharCode.Ed25519 };
}
