
export class PNumber  {
    private readonly _num: number = 0;
    constructor(num?: number | string, numh?: string) {
        // TODO: Implelment logic
        if (typeof(num) == "number") {
            this._num = num
        } else if (numh != undefined) {
            this._num = parseInt(numh, 16)
        }

    }

    get num(): number {
        return this._num;
    }

    get numh(): string {
        return this._num.toString(16)
    }
}