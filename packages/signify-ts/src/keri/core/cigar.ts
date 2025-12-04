import { Verfer } from './verfer.ts';
import { Matter, MatterArgs } from './matter.ts';

export class Cigar extends Matter {
    private _verfer: Verfer | undefined;
    constructor({ raw, code, qb64, qb64b, qb2 }: MatterArgs, verfer?: Verfer) {
        super({ raw, code, qb64, qb64b, qb2 });
        this._verfer = verfer;
    }

    get verfer(): Verfer | undefined {
        return this._verfer;
    }

    set verfer(verfer: Verfer | undefined) {
        this._verfer = verfer;
    }
}
