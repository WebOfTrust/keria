export {};

const { Crymat } = require('./cryMat');
const derivationCode = require('./derivationCodes');


/**
 * @description  A Crymat subclass holding signature with verfer property
 * Verfer verify signature of serialization
 * .raw is signature and .code is signature cipher suite
 * .verfer property to hold Verfer instance of associated verifier public key
 */
class Sigver extends Crymat {
  constructor(
    raw = null,
    code = derivationCode.twoCharCode.Ed25519,
    verfer = null,
    index = 0,
    qb64 = null,
  ) {
    // Assign verfer to .verfer attribute
    super(raw, qb64, null, code, index);
    this.getVerfer = verfer;
  }

  /**
   * @description  this will return verfer instance
   */
  verfer() {
    return this.getVerfer;
  }

  setVerfer(verfer: any) {
    this.getVerfer = verfer;
  }
}

module.exports = { Sigver };
