/* eslint-disable no-underscore-dangle */
import Base64 from "urlsafe-base64";
import {
  oneCharCode, CryOneSizes, CryTwoSizes, CryFourSizes, CryCntCodex, cryAllRawSizes, cryAllSizes,
  CryCntSizes, crySelectCodex, CRYCNTMAX, fourCharCode, CryCntIdxSizes, twoCharCode
} from "./derivationCodes";

import { b64ToInt, intToB64 } from '../help/stringToBinary';

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
export class Crymat {
  getCode: any;
  getIndex: any;
  getRaw: any;
  getqb64: any;
  constructor(
    raw: Buffer,
    qb64 = null,
    qb2 = null,
    code = oneCharCode.Ed25519N,
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
            Object.values(JSON.stringify(CryOneSizes)).includes(
              code
            )) ||
          (pad === 2 &&
            Object.values(
              JSON.stringify(CryTwoSizes).includes(code)
            )) ||
          (pad === 0 &&
            Object.values(
              JSON.stringify(CryFourSizes).includes(code)
            ))
        )
      ) {
        throw new Error(`Wrong code= ${code} for raw= ${raw} .`);
      }
      if (
        (Object.values(CryCntCodex).includes(code) &&
          index < 0) ||
        index > CRYCNTMAX
      ) {
        throw new Error(`Invalid index=${index} for code=${code}.`);
      }

      raw = raw.slice(0, cryAllRawSizes[code]);

      if (raw.length !== cryAllRawSizes[code]) {
        throw new Error(`Unexpected raw size= ${raw.length} for code= ${code}"
        " not size= ${cryAllRawSizes[code]}.`);
      }
      this.getCode = code;
      this.getIndex = index;
      this.getRaw = raw; // crypto ops require bytes not bytearray
    } else if (qb64 != null) {
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      let x = qb64.toString('utf-8');
      this.exfil(x);
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

  exfil(qb64: string) {
    const base64Pad = '=';
    let cs = 1; // code size
    let codeSlice = qb64.slice(0, cs);
    let index;

    if (Object.values(oneCharCode).includes(codeSlice)) {
      qb64 = qb64.slice(0, CryOneSizes[codeSlice]);
    } else if (codeSlice === crySelectCodex.two) {
      cs += 1;
      codeSlice = qb64.slice(0, cs);

      if (!Object.values(twoCharCode).includes(codeSlice)) {
        throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);
      }

      qb64 = qb64.slice(0, CryTwoSizes[codeSlice]);
    } else if (codeSlice === crySelectCodex.four) {
      cs += 3;
      codeSlice = qb64.slice(0, cs);

      if (!Object.values(fourCharCode).includes(codeSlice)) {
        throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);
      }
      qb64 = qb64.slice(0, CryFourSizes[codeSlice]);
    } else if (codeSlice === crySelectCodex.dash) {
      cs += 1;
      codeSlice = qb64.slice(0, cs);

      if (!Object.values(CryCntCodex).includes(codeSlice)) {
        throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);
      }

      qb64 = qb64.slice(0, CryCntSizes[codeSlice]);
      cs += 2; // increase code size
      index = b64ToInt(qb64.slice(cs - 2, cs));
      //  index = Object.keys(b64ChrByIdx).find(key =>
      // b64ChrByIdx[key] === qb64.slice(cs - 2, cs)) // last two characters for index
    } else {
      throw new Error(`Improperly coded material = ${qb64}`);
    }

    if (qb64.length !== cryAllSizes[codeSlice]) {
      throw new Error(
        `Unexpected qb64 size= ${qb64.length} for code= ${codeSlice} not size= ${cryAllSizes[codeSlice]}.`
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
    this.getRaw = Buffer.from(derivedRaw); // encode
    // eslint-disable-next-line radix
    this.getIndex = index;
    this.getqb64 = qb64;
  }

  infil() {
    let l = null;
    let full = this.getCode;
    if (Object.values(CryCntCodex).includes(this.getCode)) {
      l = CryCntIdxSizes[this.getCode];
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

    return Base64.decode(Buffer.from(this.infil()).toString());
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
