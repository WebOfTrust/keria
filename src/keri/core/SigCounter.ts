export {};
const codeAndLength = require('./derivationCodes');
const { SigMat } = require('./sigmat');
/**
 *  """
    SigCounter is subclass of SigMat, indexed signature material,
    That provides count of following number of attached signatures.
    Useful when parsing attached signatures from stream where SigCounter
    instance qb64 is inserted after Serder of event and before attached signatures.

    Changes default initialization code = SigCntDex.Base64
    Raises error on init if code not in SigCntDex

    See SigMat for inherited attributes and properties:

    Attributes:

    Properties:
        .count is int count of attached signatures (same as .index)
 */
class Sigcounter extends SigMat {
  constructor(raw = null, qb64b = null, qb64 = null, qb2 = null, code = codeAndLength.SigCntCodex.Base64, index = null, count = null) {
    if (raw) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'Buffer' is not assignable to type 'null'.
      raw = Buffer.from('', 'binary');
    }

    if (raw == null && qb64b == null && qb64 == null && qb2 == null) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'Buffer' is not assignable to type 'null'.
      raw = Buffer.from('', 'binary');
    }
    // # accept either index or count to init index

    if (count) index = count;
    // @ts-expect-error ts-migrate(2322) FIXME: Type '1' is not assignable to type 'null'.
    if (!index) index = 1;

    super(raw, qb64, qb2, code, index, qb64b);

    if (!(Object.values(codeAndLength.SigCntCodex).includes(this.code()))) {
      throw new Error(`Invalid code = ${this.code()} for SigCounter.`);
    }
  }

  count() {
    return this.index();
  }
}

module.exports = { Sigcounter };
