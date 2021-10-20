export {};
const { Crymat } = require('./cryMat');
const { CryCntCodex } = require('./derivationCode&Length');

/**
 * @description : CryCounter is subclass of CryMat, cryptographic material,
                  CryCrount provides count of following number of attached cryptographic
                  material items in its .count property.
                  Useful when parsing attached receipt couplets from stream where CryCounter
                  instance qb64 is inserted after Serder of receipt statement and
                  before attached receipt couplets.
 */
class CryCounter extends Crymat {
  constructor(
    raw = null,
    qb64b = null,
    qb64 = null,
    qb2 = null,
    code = CryCntCodex.Base64,
    index = null,
    count = null,
    ...kwf: any[]
  ) {
    // @ts-expect-error ts-migrate(2322) FIXME: Type 'Buffer' is not assignable to type 'null'.
    if (raw != null) raw = Buffer.from('', 'binary');
    if (raw == null && qb64 == null && qb64b == null && qb2 == null) {
      // @ts-expect-error ts-migrate(2322) FIXME: Type 'Buffer' is not assignable to type 'null'.
      raw = Buffer.from('', 'binary');
    }

    if (count != null) index = count;
    // @ts-expect-error ts-migrate(2322) FIXME: Type '1' is not assignable to type 'null'.
    if (index == null) index = 1;

    super(raw, qb64, qb2, code, index, count, ...kwf);
    if (!Object.values(CryCntCodex).includes(this.code())) {
      throw new Error(`Invalid code = ${this.code()} for CryCounter.`);
    }
  }

  /**
         * @description  Property counter:
                Returns .index as count
                Assumes ._index is correctly assigned
         */
  count() {
    return this.index();
  }
}

module.exports = { CryCounter };
