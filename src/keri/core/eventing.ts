import { b, concat, Dict, Ident, Ilks, Serials, versify, Version, Versionage } from "./core";
import { Tholder } from "./tholder";
import { CesrNumber } from "./number";
import { Prefixer } from "./prefixer";
import { Serder } from "./serder";
import { MtrDex, NonTransDex } from "./matter";
import { Saider } from "./saider";
import { Siger } from "./siger";
import { Cigar } from "./cigar";
import { Counter, CtrDex } from "./counter";
import { Seqner } from "./seqner";
import { TextEncoder } from "util";

let MaxIntThold = 2 ** 32 - 1

export interface RotateArgs {
    pre?: string
    keys: Array<string>,
    dig?: string,
    ilk?: string,
    sn?: number,
    isith?: number | string | Array<string>,
    ndigs?: Array<string>,
    nsith?: number | string | Array<string>,
    toad?: number,
    wits?: Array<string>,
    cuts?: Array<string>,
    adds?: Array<string>,
    cnfg?: Array<string>,
    data?: Array<object>,
    version?: Version,
    kind?: Serials,
    size?: number,
    intive?: boolean
}

export function rotate({
    pre = undefined,
    keys,
    dig = undefined,
    ilk = Ilks.rot,
    sn = 1,
    isith = undefined,
    ndigs = undefined,
    nsith = undefined,
    wits = undefined,
    cuts = undefined,
    adds = undefined,
    toad = undefined,
    data = undefined,
    version = undefined,
    kind = undefined,
    intive = true }: RotateArgs) {
    let vs = versify(Ident.KERI, version, kind, 0)
    let _ilk = ilk
    if (_ilk != Ilks.rot && _ilk != Ilks.drt) {
        throw new Error(`Invalid ilk = ${ilk} for rot or drt.`)
    }

    let sner = Number(sn)
    if (sner < 1) {
        throw new Error(`Invalid sn = 0x${sner.toString()} for rot or drt.`)
    }
    let _isit: number

    if (isith == undefined) {
        _isit = Math.max(1, Math.ceil(keys.length / 2))
    }
    else {
        _isit = isith as number
    }

    let tholder = new Tholder({sith: _isit})
    if (tholder.num != undefined && tholder.num < 1) {
        throw new Error(`Invalid sith = ${tholder.num} less than 1.`)
    }
    if (tholder.size > keys.length) {
        throw new Error(`Invalid sith = ${tholder.num} for keys = ${keys}`)
    }

    let _ndigs: Array<string>

    if (ndigs === undefined) {
        _ndigs = []
    }
    else {
        _ndigs = ndigs
    }

    let _nsith
    if (nsith === undefined) {
        _nsith = Math.max(1, Math.ceil(_ndigs.length / 2))
    }
    else {
        _nsith = nsith
    }

    let ntholder = new Tholder({sith: _nsith})
    if (ntholder.num != undefined && ntholder.num < 1) {
        throw new Error(`Invalid sith = ${ntholder.num} less than 1.`)
    }
    if (ntholder.size > _ndigs.length) {
        throw new Error(`Invalid sith = ${ntholder.num} for ndigs = ${ndigs}`)
    }

    let _wits: Array<string>
    if (wits === undefined) {
        _wits = []
    }
    else {
        _wits = wits
    }
    let witset = new Set(_wits)
    if (witset.size != _wits.length) {
        throw new Error(`Invalid wits = ${wits}, has duplicates.`)
    }

    let _cuts: Array<string>
    if (cuts === undefined) {
        _cuts = []
    }
    else {
        _cuts = cuts
    }
    let cutset = new Set(_cuts)
    if (cutset.size != _cuts.length) {
        throw new Error(`Invalid cuts = ${cuts}, has duplicates.`)
    }

    let _adds: Array<string>
    if (adds === undefined) {
        _adds = []
    }
    else {
        _adds = adds
    }
    let addset = new Set(_adds)

    //non empty intersection of witset and addset
    let witaddset = new Set([...witset].filter(x => addset.has(x)))
    if (witaddset.size > 0) {
        throw new Error(`Invalid member combination among wits = ${wits}, and adds = ${adds}.`)
    }

    // non empty intersection of cutset and addset
    let cutaddset = new Set([...cutset].filter(x => addset.has(x)))
    if (cutaddset.size > 0) {
        throw new Error(`Invalid member combination among cuts = ${cuts}, and adds = ${adds}.`)
    }

    let newitsetdiff = new Set([...witset].filter(x => cutset.has(x)))
    let newitset = new Set()
    newitsetdiff.forEach(newitset.add, newitset)
    addset.forEach(newitset.add, newitset)

    if (newitset.size != (witset.size - cutset.size + addset.size)) {
        throw new Error(`Invalid member combination among wits = ${wits}, cuts = ${cuts}, and adds = ${adds}.`)
    }

    let _toad: number

    if (toad === undefined) {
        if (newitset.size == 0) {
            _toad = 0
        }
        else {
            _toad = ample(newitset.size)
        }
    }
    else {
        _toad = toad
    }

    if (newitset.size > 0) {
        if (_toad < 1 || _toad > newitset.size) {
            throw new Error(`Invalid toad = ${_toad} for wit = ${wits}`)
        }
    }
    else {
        if (_toad != 0) {
            throw new Error(`Invalid toad = ${_toad} for wit = ${wits}`)
        }
    }
    let _ked = {
        v: vs,
        t: _ilk,
        d: "",
        i: pre,
        s: sner.toString(16),
        p: dig,
        kt: tholder.num && intive && tholder.num !== undefined && tholder.num <= MaxIntThold ? tholder.num.toString(16) : tholder.sith,
        k: keys,
        nt: ntholder.num && intive && ntholder.num !== undefined && ntholder.num <= MaxIntThold ? ntholder.num.toString(16) : ntholder.sith,
        n: _ndigs,
        bt: _toad && intive && _toad !== undefined && _toad <= MaxIntThold ? _toad : _toad.toString(16),
        br: cuts,
        ba: adds,
        a: data!= undefined ? data  : []
    }
    let[ , ked] = Saider.saidify(_ked)
    return new Serder(ked)
}

function ample(n: number, f?: number, weak = true) {
    n = Math.max(0, n)  // no negatives
    let f1
    if (f == undefined) {
        f1 = Math.max(1, Math.floor(Math.max(0, n - 1) / 3))  // least floor f subject to n >= 3*f+1

        let f2 = Math.max(1, Math.ceil(Math.max(0, n - 1) / 3))  // most Math.ceil f subject to n >= 3*f+1
        if (weak) {  // try both fs to see which one has lowest m
            return Math.min(n, Math.ceil((n + f1 + 1) / 2), Math.ceil((n + f2 + 1) / 2))
        } else {
            return Math.min(n, Math.max(0, n - f1, Math.ceil((n + f1 + 1) / 2)))
        }
    } else {
        f = Math.max(0, f)
        let m1 = Math.ceil((n + f + 1) / 2)
        let m2 = Math.max(0, n - f)
        if (m2 < m1 && n > 0) {
            throw new Error(`Invalid f=${f} is too big for n=${n}.`)
        }
        if (weak) {
            return Math.min(n, m1, m2)
        } else {
            return Math.min(n, Math.max(m1, m2))
        }
    }
}

export interface InceptArgs {
    keys: Array<string>,
    isith?: number | string | Array<string>,
    ndigs?: Array<string>,
    nsith?: number | string | Array<string>,
    toad?: number | string,
    wits?: Array<string>,
    cnfg?: Array<string>,
    data?: Array<object>,
    version?: Version,
    kind?: Serials,
    code?: string,
    intive?: boolean
    delpre?: string
}

export function incept({ keys, isith, ndigs, nsith, toad, wits, cnfg, data, version = Versionage, kind = Serials.JSON, code,
    intive = false, delpre }: InceptArgs) {


    let vs = versify(Ident.KERI, version, kind, 0)
    let ilk = delpre == undefined ? Ilks.icp : Ilks.dip
    let sner = new CesrNumber({}, 0)

    if (isith == undefined) {
        isith = Math.max(1, Math.ceil(keys.length / 2))
    }

    let tholder = new Tholder({sith: isith})
    if (tholder.num != undefined && tholder.num < 1) {
        throw new Error(`Invalid sith = ${tholder.num} less than 1.`)
    }
    if (tholder.size > keys.length) {
        throw new Error(`Invalid sith = ${tholder.num} for keys ${keys}`)
    }

    if (ndigs == undefined) {
        ndigs = new Array<string>()
    }

    if (nsith == undefined) {
        nsith = Math.max(0, Math.ceil(ndigs.length / 2))
    }

    let ntholder = new Tholder({sith: nsith})
    if (ntholder.num != undefined && ntholder.num < 0) {
        throw new Error(`Invalid nsith = ${ntholder.num} less than 0.`)
    }
    if (ntholder.size > keys.length) {
        throw new Error(`Invalid nsith = ${ntholder.num} for keys ${ndigs}`)
    }

    wits = wits == undefined ? [] : wits
    if (new Set(wits).size != wits.length) {
        throw new Error(`Invalid wits = ${wits}, has duplicates.`)
    }

    if (toad == undefined) {
        if (wits.length == 0) {
            toad = 0
        } else {
            toad = ample(wits.length)
        }
    }

    let toader = new CesrNumber({}, toad)
    if (wits.length > 0) {
        if (toader.num < 1 || toader.num > wits.length) {
            throw new Error(`Invalid toad = ${toader.num} for wits = ${wits}`)
        }
    } else {
        if (toader.num != 0) {
            throw new Error(`Invalid toad = ${toader.num} for wits = ${wits}`)
        }
    }

    cnfg = cnfg == undefined ? new Array<string>() : cnfg
    data = data == undefined ? new Array<object>() : data

    let ked = {
        v: vs,
        t: ilk,
        d: "",
        i: "",
        s: sner.numh,
        kt: (intive && tholder.num != undefined) ? tholder.num : tholder.sith,
        k: keys,
        nt: (intive && tholder.num != undefined) ? ntholder.num : ntholder.sith,
        n: ndigs,
        bt: intive ? toader.num : toader.numh,
        b: wits,
        c: cnfg,
        a: data
    } as Dict<any>

    if (delpre != undefined) {
        ked["di"] = delpre
        if (code == undefined) {
            code = MtrDex.Blake3_256
        }
    }

    let prefixer
    if (delpre == undefined && code == undefined && keys.length == 1) {
        prefixer = new Prefixer({ qb64: keys[0] })
        if (prefixer.digestive) {
            throw new Error(`Invalid code, digestive=${prefixer.code}, must be derived from ked.`)
        }
    } else {
        prefixer = new Prefixer({ code: code }, ked)
        if (delpre != undefined) {
            if (!prefixer.digestive) {
                throw new Error(`Invalid derivation code = ${prefixer.code} for delegation. Must be digestive`)
            }
        }
    }

    ked["i"] = prefixer.qb64
    if (prefixer.digestive) {
        ked["d"] = prefixer.qb64
    }
    else {
        [, ked] = Saider.saidify(ked)
    }

    return new Serder(ked)
}


export function messagize(serder: Serder, sigers?: Array<Siger>, seal?: any, wigers?: Array<Cigar>, cigars?: Array<Cigar>,
    pipelined: boolean = false): Uint8Array {
    let msg = new Uint8Array(b(serder.raw))
    let atc = new Uint8Array()

    if (sigers == undefined && wigers == undefined && cigars == undefined) {
        throw new Error(`Missing attached signatures on message = ${serder.ked}.`)
    }

    if (sigers != undefined) {
        if (seal != undefined) {
            if (seal[0]=="SealEvent") {
                atc = concat(atc, new Counter({ code: CtrDex.TransIdxSigGroups, count: 1 }).qb64b)
                atc = concat(atc, seal.i.encode("utf-8"))
                atc = concat(atc, new Seqner(seal[1].s).qb64b)
                atc = concat(atc, seal.d.encode("utf-8"))

            } else if (seal[0] == "SealLast") {
                atc = concat(atc, new Counter({ code: CtrDex.TransLastIdxSigGroups, count: 1 }).qb64b)
                atc = concat(atc, new TextEncoder().encode(seal[1].i))
            }

        }

        atc = concat(atc, new Counter({ code: CtrDex.ControllerIdxSigs, count: sigers.length }).qb64b)
        sigers.forEach((siger) => {
            atc = concat(atc, siger.qb64b)
        })
    }

    if (wigers != undefined) {
        atc = concat(atc, new Counter({ code: CtrDex.ControllerIdxSigs, count: wigers.length }).qb64b)

        wigers.forEach((wiger) => {
            if (wiger.verfer && !(wiger.verfer.code in NonTransDex)) {
                throw new Error(`Attempt to use tranferable prefix=${wiger.verfer.qb64} for receipt.`)
            }
            atc = concat(atc, wiger.qb64b)
        })
    }

    if (cigars != undefined) {
        atc = concat(atc, new Counter({ code: CtrDex.ControllerIdxSigs, count: cigars.length }).qb64b)

        cigars.forEach((cigar) => {
            if (cigar.verfer && !(cigar.verfer.code in NonTransDex)) {
                throw new Error(`Attempt to use tranferable prefix=${cigar.verfer.qb64} for receipt.`)
            }
            atc = concat(atc, cigar.qb64b)
        })
    }

    if (pipelined) {
        if (atc.length % 4 != 0) {
            throw new Error(`Invalid attachments size=${atc.length}, nonintegral quadlets.`)
        }
        msg = concat(msg, new Counter({ code: CtrDex.AttachedMaterialQuadlets, count: (Math.floor(atc.length / 4)) }).qb64b)
    }
    msg = concat(msg, atc)
    return msg
}

interface InteractArgs  {
    pre: String,
    dig: String,
    sn: number,
    data: Array<any>,
    version: Version | undefined,
    kind: Serials | undefined
}

export function interact(args: InteractArgs): Serder {
    let { pre, dig, sn, data, version, kind } = args
    let vs = versify(Ident.KERI, version, kind, 0)
    let ilk = Ilks.ixn
    let sner = new CesrNumber({}, sn)

    if (sner.num < 1) {
        throw new Error(`Invalid sn = 0x${sner.numh} for ixn.`)
    }

    data = data == undefined ? new Array<any>() : data

    let ked = {
        v: vs,
        t: ilk,
        d: "",
        i: pre,
        s: sner.numh,
        p: dig,
        a: data
    } as Dict<any>

    [, ked] = Saider.saidify(ked)

    return new Serder(ked)
}

export function reply(route: string="", data: any|undefined, stamp:string|undefined, version: Version|undefined, kind:Serials= Serials.JSON){
    const vs = versify(Ident.KERI, version, kind, 0)
    if (data == undefined) {
        data = {}
    }
    const _sad = {
        v: vs,
        t: Ilks.rpy,
        d: "",
        dt: stamp?? new Date().toISOString().replace("Z","000+00:00"),
        r: route,
        a: data
    }
    const [, sad] = Saider.saidify(_sad)
    const saider = new Saider({qb64: sad['d']})

    if ( !(saider.verify(sad,true, true, kind, 'd' )))
        throw new Error(`Invalid said = ${saider.qb64} for reply msg=${sad}.`)
    return new Serder(sad)
}
    