import {DigiDex, Matter, MatterArgs, MtrDex} from "./matter";
import {deversify, Dict, Serials} from "./core";
import {EmptyMaterialError} from "./kering";
import {dumps, sizeify} from "./serder";

import {createHash} from "blake3"

const Dummy = "#"

export enum Ids {
    d = "d"
}

class Digestage {
    public klas: any = undefined
    public size: number | undefined = 0
    public length: number | undefined = 0
    constructor(klas: any, size?: number, length?: number) {
        this.klas = klas
        this.size = size
        this.length = length
    }
}



export class Saider extends Matter {
    static Digests = new Map<string, Digestage>([
        [MtrDex.Blake3_256, new Digestage(Saider._derive_blake3_256, undefined, undefined)]
    ])

    constructor({raw, code, qb64b, qb64, qb2}: MatterArgs, sad?: Dict<any>, kind?: Serials, label: string = Ids.d) {
        try {
            super({raw, code, qb64b, qb64, qb2});
        } catch (e) {
            if (e instanceof EmptyMaterialError) {
                if (sad == undefined || !(label in sad)) {
                    throw e
                }

                if (code == undefined) {
                    if (sad[label] != "") {
                        super({qb64: sad[label], code: code})
                        code = this.code
                    } else {
                        code = MtrDex.Blake3_256
                    }
                }

                if (!DigiDex.has(code)) {
                    throw new Error(`Unsupported digest code = ${code}`)
                }

                [raw] = Saider._derive({...sad}, code, kind, label)
                super({raw: raw, code: code})
            } else {
                throw e
            }
        }

        if (!this.digestive) {
            throw new Error(`Unsupported digest code = ${this.code}.`)
        }

    }

    static _derive_blake3_256(ser: Uint8Array, _digest_size: number, _length: number) {
        const hasher = createHash();
        return hasher.update(ser).digest('');
    }


    private static _derive(sad: Dict<any>, code: string, kind: Serials | undefined, label: string): [Uint8Array, Dict<any>] {
        if (!DigiDex.has(code) || !Saider.Digests.has(code)) {
            throw new Error(`Unsupported digest code = ${code}.`)
        }

        sad = {...sad}
        sad[label] = "".padStart(Matter.Sizes.get(code)!.fs, Dummy)
        if ('v' in sad) {
            [, , kind, sad, ] = sizeify(sad, kind)
        }

        let ser = {...sad}

        let digestage = Saider.Digests.get(code)

        let cpa = Saider._serialze(ser, kind)
        let args: any[] = []
        if (digestage!.size != undefined) {
            args.push(digestage!.size)
        }

        if (digestage!.length != undefined) {
            args.push(digestage!.length)
        }

        return [digestage!.klas(cpa, ...args), sad]
    }

    public derive(sad: Dict<any>, code: string, kind: Serials | undefined, label: string) : [Uint8Array, Dict<any>]{
        code = code != undefined ? code : this.code
        return Saider._derive(sad, code, kind, label)
    }

    public verify(sad: Dict<any>, prefixed: boolean = false, versioned: boolean = false, kind?: Serials,
                  label: string = Ids.d): boolean {
        try {
            let [raw, dsad] = Saider._derive(sad, this.code, kind, label)
            let saider = new Saider({raw: raw, code: this.code})
            if (this.qb64 != saider.qb64) {
                return false
            }

            if ("v" in sad && versioned) {
                if (sad['v'] != dsad["v"]) {
                    return false
                }
            }

            if (prefixed && sad[label] != this.qb64) {
                return false
            }

        } catch (e) {
            return false
        }

        return true
    }

    private static _serialze(sad: Dict<any>, kind?: Serials): string {
        let knd = Serials.JSON
        if ('v' in sad) {
            [knd] = deversify(sad['v'])
        }

        if (kind == undefined) {
            kind = knd
        }

        return dumps(sad, kind)
    }

    public static saidify(sad: Dict<any>, code: string = MtrDex.Blake3_256, kind: Serials = Serials.JSON,
                          label: string = Ids.d): [Saider, Dict<any>] {
        if (!(label in sad)) {
            throw new Error(`Missing id field labeled=${label} in sad.`)
        }
        let raw
        [raw, sad]= Saider._derive(sad, code, kind, label)
        let saider = new Saider({raw: raw, code: code}, undefined, kind, label)
        sad[label] = saider.qb64
        return [saider, sad]
    }


}
