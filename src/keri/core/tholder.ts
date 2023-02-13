

export class Tholder {
    private _weighted: boolean = false
    private _thold: number = 0
    private _size: number = 0
    private _sith: string = ""
    private _limen: Array<string> = new Array<string>()

    constructor(sith: string | number | Array<string>) {
        this.processSith(sith)
    }

    get num(): number | undefined {
        return this._weighted ? undefined : this._thold
    }

    get size(): number {
        return this._size
    }

    get thold(): number {
        return this._thold;
    }
    get weighted(): boolean {
        return this._weighted;
    }

    get sith(): string {
        if (this.weighted) {
            if (this._sith == "") {
                return `${this._limen}`
            }
            return this._sith
        } else {
            return this.thold.toString(16)
        }
    }

    private processSith(sith: string | number | Array<string>) {
        if (typeof(sith) == "string") {
            this._sith = sith
            this._thold = parseInt(sith)
        } else if (typeof(sith) == "number") {
            this._thold = sith
            this._size = this._thold
        } else {
            this._limen = sith
            this._size = this._limen.length
        }
    }
}