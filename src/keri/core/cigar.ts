import {Verfer} from "./verfer";
import {Matter, MatterArgs} from "./matter";


export class Cigar extends Matter {
    private _verfer: Verfer
    constructor({raw, code, qb64, qb64b, qb2}:MatterArgs, verfer: Verfer) {
        super({raw, code, qb64, qb64b, qb2});
        this._verfer = verfer
    }

    get verfer(): Verfer {
        return this._verfer
    }

    set verfer(verfer:Verfer) {
        this._verfer = verfer
    }
}