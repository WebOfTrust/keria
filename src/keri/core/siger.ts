export {};
const { SigMat } = require('./sigmat');

/**
 * Siger is subclass of SigMat, indexed signature material,
    Adds .verfer property which is instance of Verfer that provides
          associated signature verifier.

    See SigMat for inherited attributes and properties:

    Attributes:

    Properties:
        .verfer is Verfer object instance

    Methods:
 */

class Siger extends SigMat {
  constructor(verfer = null, ...args: any[]) {
    super(...args);
    this.getVerfer = verfer;
  }

  verfer() {
    return this.getVerfer;
  }

  setVerfer(verfer: any) {
    this.getVerfer = verfer;
  }
}

module.exports = { Siger };
