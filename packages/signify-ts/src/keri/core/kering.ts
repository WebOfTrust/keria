export class EmptyMaterialError {
    private readonly _err: Error;
    constructor(err: string) {
        this._err = new Error(err);
    }

    get err() {
        return this._err;
    }
}
