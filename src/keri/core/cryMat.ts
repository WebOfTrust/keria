/* eslint-disable no-underscore-dangle */
const Base64 = require('urlsafe-base64');
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'codeAndLen... Remove this comment to see the full error message
const codeAndLength = require('./derivationCodes');
const { b64ToInt, intToB64 } = require('../help/stringToBinary');
// const util = require("util");
// const encoder = new util.TextEncoder("utf-8");
/**
 * @description CRYPTOGRAPHC MATERIAL BASE CLASS
 * @subclasses  provides derivation codes and key event element context specific
 * @Properties
 *         .code  str derivation code to indicate cypher suite
        .raw   bytes crypto material only without code
        .pad  int number of pad chars given raw
        .qb64 str in Base64 with derivation code and crypto material
        .qb2  bytes in binary with derivation code and crypto material
 */
// @ts-expect-error ts-migrate(2451) FIXME: Cannot redeclare block-scoped variable 'Crymat'.
class Crymat {
  getCode: any;
  getIndex: any;
  getRaw: any;
  getqb64: any;
  constructor(
    raw = null,
    qb64 = null,
    qb2 = null,
    code = codeAndLength.oneCharCode.Ed25519N,
    index = 0
  ) {
    /*
          Validate as fully qualified
        Parameters:
            raw is bytes of unqualified crypto material usable for crypto operations
            qb64 is str of fully qualified crypto material
            qb2 is bytes of fully qualified crypto material
            code is str of derivation code

        When raw provided then validate that code is correct for length of raw
            and assign .raw
        Else when qb64 or qb2 provided extract and assign .raw and .code
        */
    if (raw) {
      if (!(Buffer.isBuffer(raw) || Array.isArray(raw))) {
        throw new Error(`Not a bytes or bytearray, raw= ${raw}.`);
      }

      const pad = this._pad(raw);
      if (
        !(
          (pad === 1 &&
            Object.values(JSON.stringify(codeAndLength.CryOneSizes)).includes(
              code
            )) ||
          (pad === 2 &&
            Object.values(
              JSON.stringify(codeAndLength.CryTwoSizes).includes(code)
            )) ||
          (pad === 0 &&
            Object.values(
              JSON.stringify(codeAndLength.CryFourSizes).includes(code)
            ))
        )
      ) {
        throw new Error(`Wrong code= ${code} for raw= ${raw} .`);
      }
      if (
        (Object.values(codeAndLength.CryCntCodex).includes(code) &&
          index < 0) ||
        index > codeAndLength.CRYCNTMAX
      ) {
        throw new Error(`Invalid index=${index} for code=${code}.`);
      }

      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      raw = raw.slice(0, codeAndLength.cryAllRawSizes[code]);

      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      if (raw.length !== codeAndLength.cryAllRawSizes[code]) {
        // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
        throw new Error(`Unexpected raw size= ${raw.length} for code= ${code}"
        " not size= ${codeAndLength.cryAllRawSizes[code]}.`);
      }
      this.getCode = code;
      this.getIndex = index;
      this.getRaw = raw; // crypto ops require bytes not bytearray
    } else if (qb64 != null) {
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      qb64 = qb64.toString('utf-8');
      this.exfil(qb64);
    } else if (qb2 != null) {
      this.exfil(Base64.encode(qb2));
    } else {
      throw new Error('Improper initialization need raw or b64 or b2.');
    }
  }

  // eslint-disable-next-line no-underscore-dangle
  // eslint-disable-next-line class-methods-use-this
  _pad(raw: any) {
    const reminder = Buffer.byteLength(raw, 'binary') % 3; // length for bytes
    if (reminder === 0) {
      return 0;
    }
    return 3 - reminder;
  }

  exfil(qb64: any) {
    const base64Pad = '=';
    let cs = 1; // code size
    let codeSlice = qb64.slice(0, cs);
    let index;

    if (Object.values(codeAndLength.oneCharCode).includes(codeSlice)) {
      qb64 = qb64.slice(0, codeAndLength.CryOneSizes[codeSlice]);
    } else if (codeSlice === codeAndLength.crySelectCodex.two) {
      cs += 1;
      codeSlice = qb64.slice(0, cs);

      if (!Object.values(codeAndLength.twoCharCode).includes(codeSlice)) {
        throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);
      }

      qb64 = qb64.slice(0, codeAndLength.CryTwoSizes[codeSlice]);
    } else if (codeSlice === codeAndLength.crySelectCodex.four) {
      cs += 3;
      codeSlice = qb64.slice(0, cs);

      if (!Object.values(codeAndLength.fourCharCode).includes(codeSlice)) {
        throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);
      }
      qb64 = qb64.slice(0, codeAndLength.CryFourSizes[codeSlice]);
    } else if (codeSlice === codeAndLength.crySelectCodex.dash) {
      cs += 1;
      codeSlice = qb64.slice(0, cs);

      if (!Object.values(codeAndLength.CryCntCodex).includes(codeSlice)) {
        throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);
      }

      qb64 = qb64.slice(0, codeAndLength.CryCntSizes[codeSlice]);
      cs += 2; // increase code size
      index = b64ToInt(qb64.slice(cs - 2, cs));
      //  index = Object.keys(codeAndLength.b64ChrByIdx).find(key =>
      // codeAndLength.b64ChrByIdx[key] === qb64.slice(cs - 2, cs)) // last two characters for index
    } else {
      throw new Error(`Improperly coded material = ${qb64}`);
    }

    if (qb64.length !== codeAndLength.cryAllSizes[codeSlice]) {
      throw new Error(
        `Unexpected qb64 size= ${qb64.length} for code= ${codeSlice} not size= ${codeAndLength.cryAllSizes[codeSlice]}.`
      );
    }
    const derivedRaw = Base64.decode(
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 0 arguments, but got 1.
      qb64.slice(cs, qb64.length) + base64Pad.repeat(cs % 4).toString('utf-8')
    );

    if (derivedRaw.length !== Math.floor(((qb64.length - cs) * 3) / 4)) {
      throw new Error(`Improperly qualified material = ${qb64}`);
    }
    this.getCode = codeSlice;
    this.getRaw = Buffer.from(derivedRaw, 'binary'); // encode
    // eslint-disable-next-line radix
    this.getIndex = parseInt(index);
    this.getqb64 = qb64;
  }

  infil() {
    let l = null;
    let full = this.getCode;
    if (Object.values(codeAndLength.CryCntCodex).includes(this.getCode)) {
      l = codeAndLength.CryCntIdxSizes[this.getCode];
      full = `${this.getCode}${intToB64(this.getIndex, l)}`;
    }

    const pad = this.pad();
    // Validate pad for code length
    if (full.length % 4 !== pad) {
      throw new Error(
        `Invalid code = ${this.getCode} for converted raw pad = ${this.pad()}.`
      );
    }
    return full + Base64.encode(this.getRaw);
  }

  /**
         *  qb64 = Qualified Base64 version,this will return qualified base64 version assuming
             self.raw and self.code are correctly populated
         */
  qb64() {
    return this.infil();
  }

  /**
     * """
        Property qb64b:
        Returns Fully Qualified Base64 Version encoded as bytes
        Assumes self.raw and self.code are correctly populated
        """
     */
  qb64b() {
    return Buffer.from(this.qb64(), 'binary'); // encode
  }

  qb2() {
    /* Property qb2:
         Returns Fully Qualified Binary Version Bytes
         redo to use b64 to binary decode table since faster
         """
         # rewrite to do direct binary infiltration by
         # decode self.code as bits and prepend to self.raw
         */

    return Base64.decode(Buffer.from(this.infil(), 'binary')).toString();
    // check here
  }

  raw() {
    return this.getRaw;
  }

  pad() {
    // eslint-disable-next-line no-underscore-dangle
    return this._pad(this.getRaw);
  }

  code() {
    return this.getCode;
  }

  index() {
    return this.getIndex;
  }
}

module.exports = { Crymat };
