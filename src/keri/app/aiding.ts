import { Tier } from '../core/salter';
import { Algos } from '../core/manager';
import { incept, interact, reply, rotate } from '../core/eventing';
import { b, Ilks, Serials, Versionage } from '../core/core';
import { Tholder } from '../core/tholder';
import { MtrDex } from '../core/matter';
import { Serder } from '../core/serder';
import { parseRangeHeaders } from '../core/httping';
import { KeyManager } from '../core/keeping';
import { HabState } from '../core/state';

/** Arguments required to create an identfier */
export interface CreateIdentiferArgs {
    transferable?: boolean;
    isith?: string | number | string[];
    nsith?: string | number | string[];
    wits?: string[];
    toad?: number;
    proxy?: string;
    delpre?: string;
    dcode?: string;
    data?: any;
    algo?: Algos;
    pre?: string;
    states?: any[];
    rstates?: any[];
    prxs?: any[];
    nxts?: any[];
    mhab?: HabState;
    keys?: string[];
    ndigs?: string[];
    bran?: string;
    count?: number;
    ncount?: number;
    tier?: Tier;
    extern_type?: string;
    extern?: any;
}

/** Arguments required to rotate an identfier */
export interface RotateIdentifierArgs {
    transferable?: boolean;
    nsith?: string | number | string[];
    toad?: number;
    cuts?: string[];
    adds?: string[];
    data?: Array<object>;
    ncode?: string;
    ncount?: number;
    ncodes?: string[];
    states?: any[];
    rstates?: any[];
}

/**
 * Reducing the SignifyClient dependencies used by Identifier class
 */
export interface IdentifierDeps {
    fetch(
        pathname: string,
        method: string,
        body: unknown,
        headers?: Headers
    ): Promise<Response>;
    pidx: number;
    manager: KeyManager | null;
}

/** Identifier */
export class Identifier {
    public client: IdentifierDeps;

    /**
     * Identifier
     * @param {IdentifierDeps} client
     */
    constructor(client: IdentifierDeps) {
        this.client = client;
    }

    /**
     * List managed identifiers
     * @async
     * @param {number} [start=0] Start index of list of notifications, defaults to 0
     * @param {number} [end=24] End index of list of notifications, defaults to 24
     * @returns {Promise<any>} A promise to the list of managed identifiers
     */
    async list(start: number = 0, end: number = 24): Promise<any> {
        const extraHeaders = new Headers();
        extraHeaders.append('Range', `aids=${start}-${end}`);

        const path = `/identifiers`;
        const data = null;
        const method = 'GET';
        const res = await this.client.fetch(path, method, data, extraHeaders);

        const cr = res.headers.get('content-range');
        const range = parseRangeHeaders(cr, 'aids');
        const aids = await res.json();

        return {
            start: range.start,
            end: range.end,
            total: range.total,
            aids: aids,
        };
    }

    /**
     * Get information for a managed identifier
     * @async
     * @param {string} name Name or alias of the identifier
     * @returns {Promise<any>} A promise to the identifier information
     */
    async get(name: string): Promise<HabState> {
        const path = `/identifiers/${encodeURIComponent(name)}`;
        const data = null;
        const method = 'GET';
        const res = await this.client.fetch(path, method, data);
        return await res.json();
    }

    /**
     * Create a managed identifier
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {CreateIdentiferArgs} [kargs] Optional parameters to create the identifier
     * @returns {EventResult} The inception result
     */
    async create(
        name: string,
        kargs: CreateIdentiferArgs = {}
    ): Promise<EventResult> {
        const algo = kargs.algo == undefined ? Algos.salty : kargs.algo;

        const transferable = kargs.transferable ?? true;
        const isith = kargs.isith ?? '1';
        const nsith = kargs.nsith ?? '1';
        let wits = kargs.wits ?? [];
        const toad = kargs.toad ?? 0;
        const dcode = kargs.dcode ?? MtrDex.Blake3_256;
        const proxy = kargs.proxy;
        const delpre = kargs.delpre;
        const data = kargs.data != undefined ? [kargs.data] : [];
        const pre = kargs.pre;
        const states = kargs.states;
        const rstates = kargs.rstates;
        const prxs = kargs.prxs;
        const nxts = kargs.nxts;
        const mhab = kargs.mhab;
        const _keys = kargs.keys;
        const _ndigs = kargs.ndigs;
        const bran = kargs.bran;
        const count = kargs.count;
        const ncount = kargs.ncount;
        const tier = kargs.tier;
        const extern_type = kargs.extern_type;
        const extern = kargs.extern;

        const xargs = {
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
            tier: tier,
            extern_type: extern_type,
            extern: extern,
        };

        const keeper = this.client.manager!.new(algo, this.client.pidx, xargs);
        const [keys, ndigs] = await keeper!.incept(transferable);
        wits = wits !== undefined ? wits : [];
        let serder: Serder | undefined = undefined;
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
                intive: false,
            });
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
                delpre: delpre,
            });
        }

        const sigs = await keeper!.sign(b(serder.raw));
        const jsondata: any = {
            name: name,
            icp: serder.ked,
            sigs: sigs,
            proxy: proxy,
            smids:
                states != undefined
                    ? states.map((state) => state.i)
                    : undefined,
            rmids:
                rstates != undefined
                    ? rstates.map((state) => state.i)
                    : undefined,
        };
        jsondata[algo] = keeper.params();

        this.client.pidx = this.client.pidx + 1;
        const res = this.client.fetch('/identifiers', 'POST', jsondata);
        return new EventResult(serder, sigs, res);
    }

    /**
     * Generate an interaction event in a managed identifier
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {any} [data] Option data to be anchored in the interaction event
     * @returns {Promise<EventResult>} A promise to the interaction event result
     */
    async interact(name: string, data?: any): Promise<EventResult> {
        const hab = await this.get(name);
        const pre: string = hab.prefix;

        const state = hab.state;
        const sn = parseInt(state.s, 16);
        const dig = state.d;

        data = Array.isArray(data) ? data : [data];

        const serder = interact({
            pre: pre,
            sn: sn + 1,
            data: data,
            dig: dig,
            version: undefined,
            kind: undefined,
        });
        const keeper = this.client!.manager!.get(hab);
        const sigs = await keeper.sign(b(serder.raw));

        const jsondata: any = {
            ixn: serder.ked,
            sigs: sigs,
        };
        jsondata[keeper.algo] = keeper.params();

        const res = await this.client.fetch(
            '/identifiers/' + name + '?type=ixn',
            'PUT',
            jsondata
        );
        return new EventResult(serder, sigs, res);
    }

    /**
     * Generate a rotation event in a managed identifier
     * @param {string} name Name or alias of the identifier
     * @param {RotateIdentifierArgs} [kargs] Optional parameters requiered to generate the rotation event
     * @returns {Promise<EventResult>} A promise to the rotation event result
     */
    async rotate(
        name: string,
        kargs: RotateIdentifierArgs = {}
    ): Promise<EventResult> {
        const transferable = kargs.transferable ?? true;
        const ncode = kargs.ncode ?? MtrDex.Ed25519_Seed;
        const ncount = kargs.ncount ?? 1;

        const hab = await this.get(name);
        const pre = hab.prefix;
        const delegated = hab.state.di !== '';

        const state = hab.state;
        const count = state.k.length;
        const dig = state.d;
        const ridx = parseInt(state.s, 16) + 1;
        const wits = state.b;
        let isith = state.nt;

        let nsith = kargs.nsith ?? isith;

        // if isith is None:  # compute default from newly rotated verfers above
        if (isith == undefined)
            isith = `${Math.max(1, Math.ceil(count / 2)).toString(16)}`;

        // if nsith is None:  # compute default from newly rotated digers above
        if (nsith == undefined)
            nsith = `${Math.max(1, Math.ceil(ncount / 2)).toString(16)}`;

        const cst = new Tholder({ sith: isith }).sith; // current signing threshold
        const nst = new Tholder({ sith: nsith }).sith; // next signing threshold

        // Regenerate next keys to sign rotation event
        const keeper = this.client.manager!.get(hab);
        // Create new keys for next digests
        const ncodes = kargs.ncodes ?? new Array(ncount).fill(ncode);

        const states = kargs.states == undefined ? [] : kargs.states;
        const rstates = kargs.rstates == undefined ? [] : kargs.rstates;
        const [keys, ndigs] = await keeper!.rotate(
            ncodes,
            transferable,
            states,
            rstates
        );

        const cuts = kargs.cuts ?? [];
        const adds = kargs.adds ?? [];
        const data = kargs.data != undefined ? [kargs.data] : [];
        const toad = kargs.toad;
        const ilk = delegated ? Ilks.drt : Ilks.rot;

        const serder = rotate({
            pre: pre,
            ilk: ilk,
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
            data: data,
        });

        const sigs = await keeper.sign(b(serder.raw));

        const jsondata: any = {
            rot: serder.ked,
            sigs: sigs,
            smids:
                states != undefined
                    ? states.map((state) => state.i)
                    : undefined,
            rmids:
                rstates != undefined
                    ? rstates.map((state) => state.i)
                    : undefined,
        };
        jsondata[keeper.algo] = keeper.params();

        const res = await this.client.fetch(
            '/identifiers/' + name,
            'PUT',
            jsondata
        );
        return new EventResult(serder, sigs, res);
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
     * @returns {Promise<EventResult>} A promise to the result of the authorization
     */
    async addEndRole(
        name: string,
        role: string,
        eid?: string,
        stamp?: string
    ): Promise<EventResult> {
        const hab = await this.get(name);
        const pre = hab.prefix;

        const rpy = this.makeEndRole(pre, role, eid, stamp);
        const keeper = this.client.manager!.get(hab);
        const sigs = await keeper.sign(b(rpy.raw));

        const jsondata = {
            rpy: rpy.ked,
            sigs: sigs,
        };

        const res = this.client.fetch(
            '/identifiers/' + name + '/endroles',
            'POST',
            jsondata
        );
        return new EventResult(rpy, sigs, res);
    }

    /**
     * Generate an /end/role/add reply message
     * @param {string} pre Prefix of the identifier
     * @param {string} role Authorized role for eid
     * @param {string} [eid] Optional qb64 of endpoint provider to be authorized
     * @param {string} [stamp=now] Optional date-time-stamp RFC-3339 profile of iso8601 datetime. Now is the default if not provided
     * @returns {Serder} The reply message
     */
    private makeEndRole(
        pre: string,
        role: string,
        eid?: string,
        stamp?: string
    ): Serder {
        const data: any = {
            cid: pre,
            role: role,
        };
        if (eid != undefined) {
            data.eid = eid;
        }
        const route = '/end/role/add';
        return reply(route, data, stamp, undefined, Serials.JSON);
    }

    /**
     * Get the members of a group identifier
     * @async
     * @param {string} name - Name or alias of the identifier
     * @returns {Promise<any>} - A promise to the list of members
     */
    async members(name: string): Promise<any> {
        const res = await this.client.fetch(
            '/identifiers/' + name + '/members',
            'GET',
            undefined
        );
        return await res.json();
    }
}

/** Event Result */
export class EventResult {
    private readonly _serder: Serder;
    private readonly _sigs: string[];
    private readonly promise: Promise<Response> | Response;

    constructor(
        serder: Serder,
        sigs: string[],
        promise: Promise<Response> | Response
    ) {
        this._serder = serder;
        this._sigs = sigs;
        this.promise = promise;
    }

    get serder() {
        return this._serder;
    }

    get sigs() {
        return this._sigs;
    }

    async op(): Promise<any> {
        const res = await this.promise;
        return await res.json();
    }
}
