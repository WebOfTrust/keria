import {BexDex, Matter, NumDex} from "./matter";
import {CesrNumber} from "./number";


export class Tholder {
    private _weighted: boolean = false
    private _thold: number = 0
    private _size: number = 0
    private _sith: string = ""
    private _limen: Array<string> = new Array<string>()
    private _bexter: any
    private _number: CesrNumber | undefined = undefined
    private _satisfy: any = undefined

    constructor(thold?:any, limen?:any, sith?: any) {
        if (thold !== undefined) {
            this._processThold(thold);
        }
        else if (limen != undefined) {
            this._processLimen(limen);
        }
        else if (sith !== undefined) {
            this._processSith(sith);
        }
        else {
            throw new Error("Missing threshold expression");
        }
    }

    get weighted(): boolean {
        return this._weighted;
    }

    get thold(): number {
        return this._thold;
    }

    get size(): number {
        return this._size;
    }

    get limen(): any {
        return 0;
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

    get json(): string {
        return JSON.stringify(this._sith);
    }

    get num(): number | undefined {
        return this._weighted ? undefined : this._thold;
    }

    private _processThold(thold:number | Array<string>) {
        if (typeof(thold) === "number") {
            this._processUnweighted(thold);
        }
        else {
            this._processWeighted(thold)
        }

    }

    private _processLimen(limen: string) {
        let matter = new Matter({qb64: limen})
        if (NumDex.has(matter.code)) {
            let number = new CesrNumber({raw: matter.raw, code:matter.code})
            this._processUnweighted(number.num);
        } else if(BexDex.has(matter.code)) {
            // TODO: Implement Bexter
        } else {
            throw new Error("Invalid code for limen=" + matter.code)
        }
    }

    private _processSith(sith: string | number | Array<string>) {
        if (typeof(sith) == "number") {
            this._processUnweighted(sith);
        } else if (typeof(sith) == "string" && sith.indexOf('[') != -1) {
            this._processUnweighted(parseInt(sith, 16))
        } else {
            let _sith;
            if (typeof(sith) == "string") {
                _sith = JSON.parse(sith);
            }

            if (_sith.length == 0) {
                throw new Error("Empty weight list")
            }

            // TODO:  Implement this check:
            // # because all([]) == True  have to also test for emply mask
            //  # is it non str iterable of non str iterable of strs
            //  mask = [nonStringIterable(c) for c in sith]
            //  if mask and not all(mask):  # not empty and not iterable of iterables
            //      sith = [sith]  # attempt to make Iterable of Iterables
            //
            //  for c in sith:  # get each clause
            //      mask = [isinstance(w, str) for w in c]  # must be all strs
            //      if mask and not all(mask):  # not empty and not iterable of strs?
            //          raise ValueError(f"Invalid sith = {sith} some weights in"
            //                           f"clause {c} are non string.")

            let thold = this._processClauses(_sith);
            this._processWeighted(thold)
        }
    }

    private _processClauses(sith: Array<string | Array<string>>) {
        let thold: any[] = [];
        sith.forEach((clause) => {
            if (typeof(clause) =="string") {
                thold.push([this.weight(clause)])
            } else {
                thold.push(
                    clause.map((w) => {
                        return this.weight(w)
                    })
                )
            }
        })
        return thold
    }

    private _processUnweighted(thold: number) {
        if (thold < 0) {
            throw new Error("Non-positive int threshold = {thold}.")
        }
        this._thold = thold
        this._weighted = false
        this._size = this._thold  // used to verify that keys list size is at least size
        this._satisfy = this._satisfy_numeric
        this._number = new CesrNumber({},thold)
        this._bexter = undefined

    }

    private _processWeighted(thold: Array<string>) {

    }

    private weight(w:string) {
        return w
    }

    private _satisfy_numeric(indices: any) {

    }

}