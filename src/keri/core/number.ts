import {Matter, MatterArgs, NumDex} from "./matter";
import {intToBytes} from "./utils";

export class CesrNumber extends Matter {
    private readonly _num: number = 0;
    constructor({raw, code, qb64b, qb64, qb2}: MatterArgs, num?: number | string, numh?: string) {
        let _num;
        if(raw == undefined && qb64 == undefined && qb64b == undefined && qb2 == undefined) {
            if (typeof (num) == "number") {
                _num = num
            } else if (numh != undefined) {
                _num = parseInt(numh, 16)
            }
            else {
                _num = 0
            }
        }

        if (_num == undefined) {
            throw new Error("Invalid whole number")
        }

        if (_num <= (256 ** 2 - 1)) {  // make short version of code
            code = NumDex.Short;
        }
        else if (_num <= (256 ** 4 - 1)) {  // make long version of code
            code = code = NumDex.Long;
        }
        else if (_num <= (256 ** 8 - 1)) {  // make big version of code
            code = code = NumDex.Big;
        }
        else if (_num <= (256 ** 16 - 1)) {  // make huge version of code
            code = code = NumDex.Huge;
        }
        else {
            throw new Error("Invalid num = {num}, too large to encode.");
        }

        raw = intToBytes(_num, Matter._rawSize(code));

        super({raw, code, qb64b, qb64, qb2});

        if (!NumDex.has(this.code)) {
            throw new Error("Invalid code " + code + " for Number");
        }
    }

    get num(): number {
        return this._num;
    }

    get numh(): string {
        return this._num.toString(16)
    }

    get positive(): boolean {
        return this.num > 0
    }
}