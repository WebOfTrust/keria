import {b, Dict, Ident, Ilks, Serials, versify} from "../core/core";
import {Serder} from "../core/serder";
import {nowUTC} from "../core/utils";
import {Pather} from "../core/pather";
import {Counter, CtrDex} from "../core/counter";
import {Saider} from "../core/saider";


export function exchange(route: string,
                         payload: Dict<any>,
                         sender: string,
                         recipient?: string,
                         date?: string,
                         dig?: string,
                         modifiers?: Dict<any>,
                         embeds?: Dict<any>): [Serder, Uint8Array] {


    const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)
    const ilk = Ilks.exn
    const dt = date !== undefined ? date : nowUTC().toISOString()
    const p = dig !== undefined ? dig : ""
    const q = modifiers !== undefined ? modifiers : {}
    const ems = embeds != undefined ? embeds : {}

    let e = {} as Dict<any>
    let end = ""
    Object.entries(ems)
        .forEach(([key, value]) => {
            let serder = value[0];
            let atc = value[1]
            e[key] = serder.ked

            if (atc == undefined) {
                return
            }
            let pathed = ""
            let pather = new Pather({}, undefined, ["e", key])
            pathed += pather.qb64
            pathed += atc

            let counter = new Counter({
                code: CtrDex.PathedMaterialQuadlets,
                count: Math.floor(pathed.length / 4)
            })
            end += counter.qb64
            end += pathed
        })

    if (Object.keys(e).length > 0) {
        e["d"] = "";
        [, e] = Saider.saidify(e)
    }

    const attrs = {} as Dict<any>

    if (recipient !== undefined) {
        attrs['i'] = recipient
    }

    let a = {
        ...attrs,
        ...payload
    }

    let _ked = {
        v: vs,
        t: ilk,
        d: "",
        i: sender,
        p: p,
        dt: dt,
        r: route,
        q: q,
        a: a,
        e: e
    }
    let [, ked] = Saider.saidify(_ked)

    let exn = new Serder(ked)

    return [exn, b(end)]

}