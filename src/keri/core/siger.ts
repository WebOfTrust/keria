import { IdxSigDex, Indexer, IndexerArgs } from './indexer';
import { Verfer } from './verfer';

/**
   Siger is subclass of Indexer, indexed signature material,
    Adds .verfer property which is instance of Verfer that provides
          associated signature verifier.

    See Indexer for inherited attributes and properties:

    Attributes:

    Properties:
        .verfer is Verfer object instance

    Methods:
 **/

export class Siger extends Indexer {
    private _verfer?: Verfer;
    constructor(
        { raw, code, index, ondex, qb64, qb64b, qb2 }: IndexerArgs,
        verfer?: Verfer
    ) {
        super({ raw, code, index, ondex, qb64, qb64b, qb2 });

        if (!IdxSigDex.has(this.code)) {
            throw new Error(`Invalid code = ${this.code} for Siger.`);
        }
        this._verfer = verfer;
    }

    get verfer(): Verfer | undefined {
        return this._verfer;
    }

    set verfer(verfer: Verfer | undefined) {
        this._verfer = verfer;
    }
}
