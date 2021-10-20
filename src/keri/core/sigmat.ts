/* eslint-disable max-len */
export {};
const Base64 = require('urlsafe-base64');
const codeAndLength = require('./derivationCodes');
const intToB64 = require('../help/stringToBinary');
const { MINSIGSIZE } = require('./core');

/**
 *   SigMat is fully qualified attached signature crypto material base class
    Sub classes are derivation code specific.

    Includes the following attributes and properites.

    Attributes:

    Properties:
        .code  str derivation code of cipher suite for signature
        .index int zero based offset into signing key list
               or if from SigCntDex then its count of attached signatures
        .raw   bytes crypto material only without code
        .pad  int number of pad chars given .raw
        .qb64 str in Base64 with derivation code and signature crypto material
        .qb2  bytes in binary with derivation code and signature crypto material
 */
class SigMat {
  getCode: any;
  getIndex: any;
  getQb64: any;
  getRaw: any;
  //   pad = ""
  //     BASE64_PAD = '='

  constructor(raw = null, qb64 = null, qb2 = null, code = codeAndLength.SigTwoCodex.Ed25519, index = 0, qb64b = null) {
    /*
         Validate as fully qualified
        Parameters:
            raw is bytes of unqualified crypto material usable for crypto operations
            qb64 is str of fully qualified crypto material
            qb2 is bytes of fully qualified crypto material
            code is str of derivation code cipher suite
            index is int of offset index into current signing key list
                   or if from SigCntDex then its count of attached signatures
            qb64b is bytes of fully qualified crypto material

        When raw provided then validate that code is correct for length of raw
            and assign .raw .code and .index
        Else when either qb64 or qb2 provided then extract and assign .raw and .code

        */

    if (raw) {
      if (!(Buffer.isBuffer(raw) || Array.isArray(raw))) {
        throw new Error(`Not a bytes or bytearray, raw= ${raw}.`);
      }
      const pad = this.getPad(raw);

      if (!((pad === 2 && Object.values(JSON.stringify(codeAndLength.SigTwoCodex)).includes(code))
                || (pad === 0 && Object.values(JSON.stringify(codeAndLength.SigCntCodex).includes(code))
                    || (pad === 0 && Object.values(JSON.stringify(codeAndLength.SigFourCodex).includes(code))
                        || (pad === 1 && Object.values(JSON.stringify(codeAndLength.SigFiveCodex).includes(code))))))) {
        throw new Error(`Wrong code= ${code} for raw= ${raw} .`);
      }
      if ((Object.values(codeAndLength.SigTwoCodex).includes(code)
                && (index < 0) || (index > codeAndLength.SIGTWOMAX))
                || (Object.values(codeAndLength.SigCntCodex).includes(code) && ((index < 0) || (index > codeAndLength.SIGFOURMAX)))
                || (Object.values(codeAndLength.SigFourCodex).includes(code) && ((index < 0) || (index > codeAndLength.SIGFOURMAX)))
                || (Object.values(codeAndLength.SigFiveCodex).includes(code) && ((index < 0) || (index > codeAndLength.SIGFIVEMAX)))) {
        throw new Error(`Invalid index=${index} for code=${code}.`);
      }

      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      raw = raw.slice(0, codeAndLength.SigRawSizes[code]);
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      if (raw.length !== codeAndLength.SigRawSizes[code]) {
        // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
        throw new Error(`Unexpected raw size= ${raw.length} for code= ${code}
        not size= ${codeAndLength.cryAllRawSizes[code]}.`);
      }
      this.getCode = code;
      this.getIndex = index;
      // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
      this.getRaw = Buffer.from(raw, 'binary'); // crypto ops require bytes not bytearray
    } else if (qb64b != null) {
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      qb64b = qb64b.toString('utf-8');
      this.exfil(qb64b);
    } else if (qb64 != null) {
      // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
      qb64 = qb64.toString('utf-8');
      this.exfil(qb64);
    } else if (qb2 != null) {
      //  encodeB64(qb2).decode("utf-8")
      this.exfil(Base64.encode(qb2));
    } else {
      throw new Error('Improper initialization need raw or b64 or b2.');
    }
  }

  // eslint-disable-next-line class-methods-use-this
  getPad(raw: any) {
    const reminder = Buffer.byteLength(raw, 'binary') % 3;
    if (reminder === 0) return 0;
    return 3 - reminder;
  }

  exfil(qb64: any) {
    const BASE64_PAD = '=';
    if (qb64.length < MINSIGSIZE) // # Need more bytes
    { throw new Error('Need more bytes.'); }
    let cs = 1; // code size
    let codeSlice = qb64.slice(0, cs);
    codeSlice = codeSlice.toString();
    let index = 0;

    if (Object.values(codeAndLength.SigTwoCodex).includes(codeSlice)) {
      qb64 = qb64.slice(0, codeAndLength.SigTwoSizes[codeSlice]);
      cs += 1;
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'string | undefined' is not assignable to typ... Remove this comment to see the full error message
      index = Object.keys(codeAndLength.b64ChrByIdx).find((key) => codeAndLength.b64ChrByIdx[key] === qb64.slice(cs - 1, cs));
    } else if (codeSlice === codeAndLength.SigSelectCodex.four) {
      cs += 1;
      codeSlice = qb64.slice(0, cs);
      if (!Object.values(codeAndLength.SigFourCodex).includes(codeSlice)) throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);

      qb64 = qb64.slice(0, codeAndLength.SigFourSizes[codeSlice]);

      cs += 2;
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'string | undefined' is not assignable to typ... Remove this comment to see the full error message
      index = Object.keys(codeAndLength.b64ChrByIdx).find((key) => codeAndLength.b64ChrByIdx[key] === qb64.slice(cs - 2, cs));
    } else if (codeSlice === codeAndLength.SigSelectCodex.dash) {
      cs += 1;
      codeSlice = qb64.slice(0, cs);
      if (!Object.values(codeAndLength.SigCntCodex).includes(codeSlice)) throw new Error(`Invalid derivation code = ${codeSlice} in ${qb64}.`);

      qb64 = qb64.slice(0, codeAndLength.SigCntSizes[codeSlice]);
      cs += 2;
      index = intToB64.b64ToInt(qb64.slice(cs - 2, cs));
      // Object.keys(codeAndLength.b64ChrByIdx).find(key => codeAndLength.b64ChrByIdx[key] === qb64.slice(cs - 2, cs))
    } else {
      throw new Error(`Improperly coded material = ${qb64}`);
    }

    if (qb64.length !== codeAndLength.SigSizes[codeSlice]) throw new Error(`Unexpected qb64 size= ${qb64.length} for code= ${codeSlice} not size= ${codeAndLength.cryAllSizes[codeSlice]}.`);

    const pad = cs % 4;
    const base = qb64.slice(cs, qb64.length) + BASE64_PAD.repeat(pad);
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 0 arguments, but got 1.
    const decodedBase = Base64.decode(base.toString('utf-8')); // Buffer.from(base, "utf-8")
    if (decodedBase.length !== Math.floor(((qb64.length - cs) * 3) / 4)) {
      throw new Error(`Improperly qualified material = ${qb64}`);
    }
    this.getCode = codeSlice;
    this.getRaw = Buffer.from(decodedBase, 'binary');
    // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'number' is not assignable to par... Remove this comment to see the full error message
    this.getIndex = parseInt(index);
    this.getQb64 = qb64; // this.getQb64
  }

  infil() {
    const l = codeAndLength.SigIdxSizes[this.getCode];
    const full = `${this.getCode}${intToB64.intToB64(this.getIndex, l)}`;
    const pad = this.pad();
    // Validate pad for code length
    if ((full).length % 4 !== pad) {
      // Here pad is not the reminder of code length
      throw new Error(`Invalid code = ${this.code()} for converted raw pad = ${this.pad()}.`);
    }
    // encodeURIComponent(Base64.encode(this._raw))

    return (full + decodeURIComponent(Base64.encode(this.raw())));
    // .slice(0, -pad))
  }

  qb64() {
    // qb64 = Qualified Base64 version,this will return qualified base64 version assuming
    // self.raw and self.code are correctly populated

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
    return Buffer.from(this.qb64(), 'utf-8');
  }

  qb2() {
    /* Property qb2:
         Returns Fully Qualified Binary Version Bytes
         redo to use b64 to binary decode table since faster
         """
         # rewrite to do direct binary infiltration by
         # decode self.code as bits and prepend to self.raw
         */
    //  Buffer.from(this.infil(), 'utf-8')

    return Base64.decode(Buffer.from(this.infil(), 'binary')).toString('utf-8');
  }

  raw() {
    return this.getRaw;
  }

  pad() {
    return this.getPad(this.getRaw);
  }

  code() {
    return this.getCode;
  }

  index() {
    return this.getIndex;
  }
}

module.exports = { SigMat };
