import { SignifyClient } from "./clienting"
import { Tier} from "../core/salter"
import {Algos} from '../core/manager'
import {incept, interact, reply, rotate} from "../core/eventing"
import {b,Serials, Versionage} from "../core/core"
import {Tholder} from "../core/tholder"
import {MtrDex} from "../core/matter"
import {Serder} from "../core/serder"
import {parseRangeHeaders} from "../core/httping"

/** Arguments required to create an identfier */
export interface CreateIdentiferArgs {
    transferable?: boolean,
    isith?: string | number | string[],
    nsith?: string | number | string[],
    wits?: string[],
    toad?: number,
    proxy?: string,
    delpre?: string,
    dcode?: string,
    data?: any,
    algo?: Algos,
    pre?: string,
    states?: any[],
    rstates?: any[]
    prxs?: any[],
    nxts?: any[],
    mhab?: any,
    keys?: any[],
    ndigs?: any[],
    bran?: string,
    count?: number,
    ncount?: number,
    tier?: Tier
}

/** Arguments required to rotate an identfier */
export interface RotateIdentifierArgs {
    transferable?: boolean,
    nsith?: string | number | string[],
    toad?: number,
    cuts?: string[],
    adds?: string[],
    data?: Array<object>,
    ncode?: string,
    ncount?: number,
    ncodes?: string[],
    states?: any[],
    rstates?: any[]
}

/** Identifier */
export class Identifier {
    public client: SignifyClient
    /**
     * Identifier
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * List managed identifiers
     * @async
     * @param {number} [start=0] Start index of list of notifications, defaults to 0
     * @param {number} [end=24] End index of list of notifications, defaults to 24
     * @returns {Promise<any>} A promise to the list of managed identifiers
     */
    async list(start:number=0, end:number=24): Promise<any> {
        let extraHeaders = new Headers()
        extraHeaders.append('Range', `aids=${start}-${end}`)
        
        let path = `/identifiers`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, extraHeaders)

        let cr = res.headers.get('content-range')
        let range = parseRangeHeaders(cr,"aids")
        let aids = await res.json()

        return {
            start: range.start,
            end: range.end,
            total: range.total,
            aids: aids
        }
    }

    /** 
     * Get information for a managed identifier
     * @async
     * @param {string} name Name or alias of the identifier
     * @returns {Promise<any>} A promise to the identifier information
    */
    async get(name: string): Promise<any> {
        let path = `/identifiers/${name}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()
    }

    /**
     * Create a managed identifier
     * @async
     * @param {string} name Name or alias of the identifier 
     * @param {CreateIdentiferArgs} [kargs] Optional parameters to create the identifier
     * @returns {EventResult} The inception result
     */
    create(name: string, kargs:CreateIdentiferArgs={}): EventResult {

        const algo = kargs.algo == undefined ? Algos.salty : kargs.algo

        let transferable = kargs.transferable ?? true
        let isith = kargs.isith ?? "1"
        let nsith = kargs.nsith ?? "1"
        let wits = kargs.wits ?? []
        let toad = kargs.toad ?? 0
        let dcode = kargs.dcode ?? MtrDex.Blake3_256
        let proxy = kargs.proxy
        let delpre = kargs.delpre
        let data = kargs.data != undefined ? [kargs.data] : []
        let pre = kargs.pre
        let states = kargs.states
        let rstates = kargs.rstates
        let prxs = kargs.prxs
        let nxts = kargs.nxts
        let mhab = kargs.mhab
        let _keys = kargs.keys
        let _ndigs = kargs.ndigs
        let bran = kargs.bran
        let count = kargs.count
        let ncount = kargs.ncount
        let tier = kargs.tier

        let xargs = {
            transferable: transferable,
            isith: isith,
            nsith: nsith,
            wits: wits,
            toad: toad,
            proxy: proxy,
            delpre: delpre,
            dcode: dcode,
            data: data,
            algo: algo,
            pre: pre,
            prxs: prxs,
            nxts: nxts,
            mhab: mhab,
            states: states,
            rstates: rstates,
            keys: _keys,
            ndigs: _ndigs,
            bran: bran,
            count: count,
            ncount: ncount,
            tier: tier
        }

        let keeper = this.client.manager!.new(algo, this.client.pidx, xargs)
        let [keys, ndigs] = keeper!.incept(transferable)
        wits = wits !== undefined ? wits : []
        let serder: Serder|undefined = undefined
        if (delpre == undefined) {
            serder = incept({
                keys: keys!,
                isith: isith,
                ndigs: ndigs,
                nsith: nsith,
                toad: toad,
                wits: wits,
                cnfg: [],
                data: data,
                version: Versionage,
                kind: Serials.JSON,
                code: dcode,
                intive: false
            })

        } else {
            serder = incept({
                keys: keys!,
                isith: isith,
                ndigs: ndigs,
                nsith: nsith,
                toad: toad,
                wits: wits,
                cnfg: [],
                data: data,
                version: Versionage,
                kind: Serials.JSON,
                code: dcode,
                intive: false,
                delpre: delpre
            })
        }

        let sigs = keeper!.sign(b(serder.raw))
        var jsondata: any = {
            name: name,
            icp: serder.ked,
            sigs: sigs,
            proxy: proxy,
            smids: states != undefined ? states.map(state => state.i) : undefined,
            rmids: rstates != undefined ? rstates.map(state => state.i) : undefined
        }
        jsondata[algo] = keeper.params()

            this.client.pidx = this.client.pidx + 1
        let res = this.client.fetch("/identifiers", "POST", jsondata)
        return new EventResult(serder, sigs, res)
    }

    /**
     * Generate an interaction event in a managed identifier
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {any} [data] Option data to be anchored in the interaction event
     * @returns {Promise<EventResult>} A promise to the interaction event result
     */
    async interact(name: string, data?: any): Promise<EventResult> {

        let hab = await this.get(name)
        let pre: string = hab.prefix

        let state = hab.state
        let sn = Number(state.s)
        let dig = state.d

        data = Array.isArray(data) ? data : [data]

        let serder = interact({ pre: pre, sn: sn + 1, data: data, dig: dig, version: undefined, kind: undefined })
        let keeper = this.client!.manager!.get(hab)
        let sigs = keeper.sign(b(serder.raw))

        let jsondata: any = {
            ixn: serder.ked,
            sigs: sigs,
        }
        jsondata[keeper.algo] = keeper.params()

        let res = this.client.fetch("/identifiers/" + name + "?type=ixn", "PUT", jsondata)
        return new EventResult(serder, sigs, res)
    }


    /**
     * Generate a rotation event in a managed identifier
     * @param {string} name Name or alias of the identifier
     * @param {RotateIdentifierArgs} [kargs] Optional parameters requiered to generate the rotation event
     * @returns {Promise<EventResult>} A promise to the rotation event result
     */
    async rotate(name: string, kargs: RotateIdentifierArgs={}): Promise<EventResult> {

        let transferable = kargs.transferable ?? true
        let ncode = kargs.ncode ?? MtrDex.Ed25519_Seed
        let ncount = kargs.ncount ?? 1

        let hab = await this.get(name)
        let pre = hab.prefix

        let state = hab.state
        let count = state.k.length
        let dig = state.d
        let ridx = (Number(state.s) + 1)
        let wits = state.b
        let isith = state.kt

        let nsith = kargs.nsith ?? isith

        // if isith is None:  # compute default from newly rotated verfers above
        if (isith == undefined) isith = `${Math.max(1, Math.ceil(count / 2)).toString(16)}`

        // if nsith is None:  # compute default from newly rotated digers above
        if (nsith == undefined) nsith = `${Math.max(1, Math.ceil(ncount / 2)).toString(16)}`

        let cst = new Tholder({sith: isith}).sith  // current signing threshold
        let nst = new Tholder({sith: nsith}).sith  // next signing threshold

        // Regenerate next keys to sign rotation event
        let keeper = this.client.manager!.get(hab)
        // Create new keys for next digests
        let ncodes = kargs.ncodes ?? new Array(ncount).fill(ncode)

        let states = kargs.states == undefined? [] : kargs.states
        let rstates = kargs.rstates == undefined? [] : kargs.rstates
        let [keys, ndigs] = keeper!.rotate(ncodes, transferable, states, rstates)

        let cuts = kargs.cuts ?? []
        let adds = kargs.adds ?? []
        let data = kargs.data != undefined ? [kargs.data] : []
        let toad = kargs.toad
        let serder = rotate({
            pre: pre,
            keys: keys,
            dig: dig,
            sn: ridx,
            isith: cst,
            nsith: nst,
            ndigs: ndigs,
            toad: toad,
            wits: wits,
            cuts: cuts,
            adds: adds,
            data: data
        })

        let sigs = keeper.sign(b(serder.raw))

        var jsondata: any = {
            rot: serder.ked,
            sigs: sigs,
            smids: states != undefined ? states.map(state => state.i) : undefined,
            rmids: rstates != undefined ? rstates.map(state => state.i) : undefined
        }
        jsondata[keeper.algo] = keeper.params()

        let res = this.client.fetch("/identifiers/" + name, "PUT", jsondata)
        return new EventResult(serder, sigs, res)
    }

    /**
     * Authorize an endpoint provider in a given role for a managed identifier
     * @remarks
     * Typically used to authorize the agent to be the endpoint provider for the identifier in the role of `agent`
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} role Authorized role for eid
     * @param {string} [eid] Optional qb64 of endpoint provider to be authorized
     * @param {string} [stamp=now] Optional date-time-stamp RFC-3339 profile of iso8601 datetime. Now is the default if not provided
     * @returns {Promise<any>} A promise to the result of the authorization
     */
    async addEndRole(name: string, role: string, eid?: string, stamp?: string): Promise<any> {
        const hab = await this.get(name)
        const pre = hab.prefix

        const rpy = this.makeEndRole(pre, role, eid, stamp)
        const keeper = this.client.manager!.get(hab)
        const sigs = keeper.sign(b(rpy.raw))

        const jsondata = {
            rpy: rpy.ked,
            sigs: sigs
        }

        let res = await this.client.fetch("/identifiers/" + name + "/endroles", "POST", jsondata)
        return await res.json()

    }

    /**
     * Generate an /end/role/add reply message
     * @param {string} pre Prefix of the identifier
     * @param {string} role Authorized role for eid
     * @param {string} [eid] Optional qb64 of endpoint provider to be authorized
     * @param {string} [stamp=now] Optional date-time-stamp RFC-3339 profile of iso8601 datetime. Now is the default if not provided
     * @returns {Serder} The reply message
     */
    private makeEndRole(pre: string, role: string, eid?: string, stamp?: string): Serder {
        const data: any = {
            cid: pre,
            role: role
        }
        if (eid != undefined) {
            data.eid = eid
        }
        const route = "/end/role/add"
        return reply(route, data, stamp, undefined, Serials.JSON)
    }

    /**
     * Get the members of a group identifier
     * @async
     * @param {string} name - Name or alias of the identifier
     * @returns {Promise<any>} - A promise to the list of members
     */
    async members(name: string): Promise<any> {
        let res = await this.client.fetch("/identifiers/" + name + "/members", "GET", undefined)
        return await res.json()
    }
}

/** Event Result */
export class EventResult {
    private readonly _serder: Serder
    private readonly _sigs: string[]
    private readonly promise: Promise<Response>

    constructor(serder: Serder, sigs: string[], promise: Promise<Response>) {
        this._serder = serder
        this._sigs = sigs
        this.promise = promise
    }

    get serder() {
        return this._serder
    }

    get sigs() {
        return this._sigs
    }

    async op(): Promise<any> {
        let res = await this.promise
        return await res.json()
    }
}