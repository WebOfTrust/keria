
export {};
const { Matter } = require('./matter');


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

export class Siger extends Matter {
  constructor({}) {
    super();
  }

  verfer() {
    return this.getVerfer;
  }

  setVerfer(verfer: any) {
    this.getVerfer = verfer;
  }
}
