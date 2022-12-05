export {};
const _ = require('lodash');
const { Diger } = require('./diger');
const codeAndLength = require('./derivationCodes');

let getSer;
let getSith: any;
let getKeys: any;
/**
 * @description  Nexter is Diger subclass with support to create itself from
                    next sith and next keys
 */

export class Nexter extends Diger {
  /**
     *
 Assign digest verification function to ._verify

        See CryMat for inherited parameters

        Parameters:
           ser is bytes serialization from which raw is computed if not raw
           sith is int threshold or lowercase hex str no leading zeros
           keys is list of keys each is qb64 public key str

           Raises error if not any of raw, ser, keys, ked

           if not raw and not ser
               If keys not provided
                  get keys from ked

           If sith not provided
               get sith from ked
               but if not ked then compute sith as simple majority of keys
     */
  constructor(
    ser = null,
    sith?:number,
    keys?: any[],
    ked?: {},
    qb64 = null,
    code = codeAndLength.oneCharCode.Blake3_256,
  ) {
    try {
      super(null, ser, code, qb64);
    } catch (error) {
      if (!keys && !ked) {
        throw error;
      }
      [getSer, getSith, getKeys] = deriveSer(sith, keys, ked);

      super(null, getSer);
    }
    if (getSith) {
      this.getSith = _.cloneDeep(getSith);
    } else this.getSith = null;
    if (getKeys) this.getKeys = _.cloneDeep(getKeys);
    else this.getKeys = null;
  }

  /**
   * """ Property ._sith getter """
   */
  sith() {
    return this.getSith;
  }

  /**
   * """ Property ._keys getter """
   */
  keys() {
    return this.getKeys;
  }

  // eslint-disable-next-line class-methods-use-this
  derive(sith = null, keys = null, ked = null) {
    return deriveSer(sith, keys, ked);
  }

  /**
     * @description    Returns True if digest of bytes serialization ser matches .raw
        using .raw as reference digest for ._verify digest algorithm determined
        by .code  If ser not provided then extract ser from either (sith, keys) or ked
     * @param {*} ser
     * @param {*} sith
     * @param {*} keys
     * @param {*} ked
     */
  verify(
    ser = Buffer.from('', 'binary'),
    sith = null,
    keys = null,
    ked = null,
  ) {
    let derivedSer;
    // let derivedSith;
    // let derivedKeys;
    if (!ser) {
      [derivedSer, , ] = this.derive(sith, keys, ked);
    }

    return this.verifyFunc(derivedSer, this.raw());
  }
}

/**
*
@description Returns serialization derived from sith, keys, or ked
*/
function deriveSer(sith: any, keys: any, ked: any) {
  let nxts = [];
  if (!keys) {
    try {
      keys = ked.keys;
    } catch (error) {
      throw new Error(`Error extracting keys from ked = ${error}`);
    }
  }
  if (!keys) throw new Error('"Keys not found"');
  if (!sith) {
    try {
      sith = ked.sith;
    } catch (error) {
      sith = Math.max(1, Math.ceil(keys.length / 2));
    }
  }
  if (sith instanceof Array) {
    throw new Error(`List form of sith = ${sith} not yet supporte`);
  } else {
    try {
      sith = parseInt(sith, 16);
    } catch (error:any) { throw new Error(error); }
    sith = Math.max(1, sith);
    sith = sith.toString(16);
  }

  nxts = [Buffer.from(sith, 'binary')]; // create list to concatenate for hashing   sith.toString("utf-8")
  keys.forEach((key: any) => {
    nxts.push(Buffer.from(key, 'binary'));
  });
  getSer = Buffer.from(nxts.join(''), 'binary');

  return [getSer, sith, keys];
}
