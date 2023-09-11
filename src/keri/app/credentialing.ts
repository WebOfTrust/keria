import { SignifyClient } from "./clienting"
import {Salter} from "../core/salter"
import { interact, messagize} from "../core/eventing"
import {b, Dict, Ident, Ilks, Serials, versify} from "../core/core"
import {MtrDex} from "../core/matter"
import {Saider} from "../core/saider"
import {Serder} from "../core/serder"
import {Siger} from "../core/siger"
import {Prefixer} from "../core/prefixer"
import {randomNonce} from "./coring"
import {TextDecoder} from "util"


/** Types of credentials */
export class CredentialTypes {
    static issued = "issued"
    static received = "received"
}

/** Credential filter parameters */
export interface CredentialFilter {
    filter?: object, 
    sort?: object[], 
    skip?: number, 
    limit?: number
}

/**
 * Credentials
 */
export class Credentials {
    public client: SignifyClient
    /**
     * Credentials
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * List credentials
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {CredentialFilter} [kargs] Optional parameters to filter the credentials
     * @returns {Promise<any>} A promise to the list of credentials
     */
    async list(name: string, kargs:CredentialFilter ={}): Promise<any> {
        let path = `/identifiers/${name}/credentials/query`
        let filtr = kargs.filter === undefined ? {} : kargs.filter;
        let sort = kargs.sort === undefined ? [] : kargs.sort;
        let limit = kargs.limit === undefined ? 25 : kargs.limit;
        let skip = kargs.skip === undefined ? 0 : kargs.skip;

        let data = {
            filter: filtr,
            sort: sort,
            skip: skip,
            limit: limit
        }
        let method = 'POST'

        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()
    }

    /**
     * Get a credential
     * @async
     * @param {string} name - Name or alias of the identifier
     * @param {string} said - SAID of the credential
     * @param {boolean} [includeCESR=false] - Optional flag export the credential in CESR format
     * @returns {Promise<any>} A promise to the credential
     */
    async get(name: string, said: string, includeCESR: boolean = false): Promise<any> {
        let path = `/identifiers/${name}/credentials/${said}`
        let method = 'GET'
        let headers = includeCESR? new Headers({'Accept': 'application/json+cesr'}) : new Headers({'Accept': 'application/json'})
        let res = await this.client.fetch(path, method, null, headers)

        return includeCESR? await res.text() : await res.json()
    }

    /**
     * Issue a credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} registy qb64 AID of credential registry
     * @param {string} schema SAID of the schema
     * @param {string} [recipient] Optional prefix of recipient identifier
     * @param {any} [credentialData] Optional credential data
     * @param {any} [rules] Optional credential rules
     * @param {any} [source] Optional credential sources
     * @param {boolean} [priv=false] Flag to issue a credential with privacy preserving features
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async issue(name: string, registy: string, schema: string, recipient?: string, credentialData?: any, rules?: any, source?: any, priv: boolean=false): Promise<any> {
        // Create Credential
        let hab = await this.client.identifiers().get(name)
        let pre: string = hab.prefix
        const dt = new Date().toISOString().replace('Z', '000+00:00')

        const vsacdc = versify(Ident.ACDC, undefined, Serials.JSON, 0)
        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)

        let cred: any = {
            v: vsacdc,
            d: ""
        }
        let subject: any = {
            d: "",
        }
        if (priv) {
            cred.u = new Salter({})
            subject.u = new Salter({})
        }
        if (recipient != undefined) {
            subject.i = recipient
        }
        subject.dt = dt
        subject = {...subject, ...credentialData}

        const [, a] = Saider.saidify(subject,undefined,undefined,"d")

        cred = {...cred, i:pre}
        cred.ri = registy
        cred = {...cred,...{s: schema}, ...{a: a}}

        if (source !== undefined ) {
            cred.e = source
        }
        if (rules !== undefined) {
            cred.r = rules
        }
        const [, vc] = Saider.saidify(cred)

        // Create iss
        let _iss = {
            v: vs,
            t: Ilks.iss,
            d: "",
            i: vc.d,
            s: "0",
            ri: registy,
            dt: dt

        }

        let [, iss] = Saider.saidify(_iss)

        // Create paths and sign
        let cpath = '6AABAAA-'
        let keeper = this.client!.manager!.get(hab)
        let csigs = keeper.sign(b(JSON.stringify(vc)))

        // Create ixn
        let ixn = {}
        let sigs = []

        let state = hab.state
        if (state.c !== undefined && state.c.includes("EO")) {
            var estOnly = true
        }
        else {
            var estOnly = false
        }
        let sn = Number(state.s)
        let dig = state.d

        let data:any = [{
            i: iss.i,
            s: iss.s,
            d: iss.d
        }]

        if (estOnly) {
            // TODO implement rotation event
            throw new Error("Establishment only not implemented")

        } else {
            let serder = interact({ pre: pre, sn: sn + 1, data: data, dig: dig, version: undefined, kind: undefined })
            sigs = keeper.sign(b(serder.raw))
            ixn = serder.ked
        }

        let body = {
            cred: vc,
            csigs: csigs,
            path: cpath,
            iss: iss,
            ixn: ixn,
            sigs: sigs
        }

        let path = `/identifiers/${name}/credentials`
        let method = 'POST'
        let headers = new Headers({
            'Accept': 'application/json+cesr'

        })
        let res = await this.client.fetch(path, method, body, headers)
        return await res.json()

    }

    /**
     * Revoke credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} said SAID of the credential
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async revoke(name: string, said: string): Promise<any> {
        let hab = await this.client.identifiers().get(name)
        let pre: string = hab.prefix

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)
        const dt = new Date().toISOString().replace('Z', '000+00:00')

        let cred = await this.get(name, said)

        // Create rev
        let _rev = {
            v: vs,
            t: Ilks.rev,
            d: "",
            i: said,
            s: "1",
            p: cred.status.d,
            ri: cred.sad.ri,
            dt: dt
        }

        let [, rev] = Saider.saidify(_rev)

        // create ixn
        let ixn = {}
        let sigs = []

        let state = hab.state
        if (state.c !== undefined && state.c.includes("EO")) {
            var estOnly = true
        }
        else {
            var estOnly = false
        }

        let sn = Number(state.s)
        let dig = state.d

        let data:any = [{
            i: rev.i,
            s: rev.s,
            d: rev.d
        }]
        if (estOnly) {
            // TODO implement rotation event
            throw new Error("Establishment only not implemented")

        } else {
            let serder = interact({ pre: pre, sn: sn + 1, data: data, dig: dig, version: undefined, kind: undefined })
            let keeper = this.client!.manager!.get(hab)
            sigs = keeper.sign(b(serder.raw))
            ixn = serder.ked
        }

        let body = {
            rev: rev,
            ixn: ixn,
            sigs: sigs
        }

        let path = `/identifiers/${name}/credentials/${said}`
        let method = 'DELETE'
        let headers = new Headers({
            'Accept': 'application/json+cesr'

        })
        let res = await this.client.fetch(path, method, body, headers)
        return await res.json()

    }

    /**
     * Present a credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} said SAID of the credential
     * @param {string} recipient Identifier prefix of the receiver of the presentation
     * @param {boolean} [include=true] Flag to indicate whether to stream credential alongside presentation exchange message
     * @returns {Promise<string>} A promise to the long-running operation
     */
    async present(name: string, said: string, recipient: string, include: boolean=true): Promise<string> {

        let hab = await this.client.identifiers().get(name)
        let pre: string = hab.prefix

        let cred = await this.get(name, said)
        let data = {
            i: cred.sad.i,
            s: cred.sad.s,
            n: said
        }

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)

        const _sad = {
            v: vs,
            t: Ilks.exn,
            d: "",
            dt: new Date().toISOString().replace("Z","000+00:00"),
            r: "/presentation",
            q: {},
            a: data
        }
        const [, sad] = Saider.saidify(_sad)
        const exn = new Serder(sad)

        let keeper = this.client!.manager!.get(hab)

        let sig = keeper.sign(b(exn.raw),true)

        let siger = new Siger({qb64:sig[0]})
        let seal = ["SealLast" , {i:pre}]
        let ims = messagize(exn,[siger],seal, undefined, undefined, true)
        ims = ims.slice(JSON.stringify(exn.ked).length)


        let body = {
            exn: exn.ked,
            sig: new TextDecoder().decode(ims),
            recipient: recipient,
            include: include
        }

        let path = `/identifiers/${name}/credentials/${said}/presentations`
        let method = 'POST'
        let headers = new Headers({
            'Accept': 'application/json+cesr'

        })
        let res = await this.client.fetch(path, method, body, headers)
        return await res.text()

    }

    /**
     * Request a presentation of a credential
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} recipient Identifier prefix of the receiver of the presentation
     * @param {string} schema SAID of the schema
     * @param {string} [issuer] Optional prefix of the issuer of the credential
     * @returns {Promise<string>} A promise to the long-running operation
     */
    async request(name: string, recipient: string, schema: string, issuer?: string): Promise<string> {
        let hab = await this.client.identifiers().get(name)
        let pre: string = hab.prefix

        let data:any = {
            s: schema
        }
        if (issuer !== undefined) {
            data["i"] = issuer
        }

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)

        const _sad = {
            v: vs,
            t: Ilks.exn,
            d: "",
            dt: new Date().toISOString().replace("Z","000+00:00"),
            r: "/presentation/request",
            q: {},
            a: data
        }
        const [, sad] = Saider.saidify(_sad)
        const exn = new Serder(sad)

        let keeper = this.client!.manager!.get(hab)

        let sig = keeper.sign(b(exn.raw),true)

        let siger = new Siger({qb64:sig[0]})
        let seal = ["SealLast" , {i:pre}]
        let ims = messagize(exn,[siger],seal, undefined, undefined, true)
        ims = ims.slice(JSON.stringify(exn.ked).length)


        let body = {
            exn: exn.ked,
            sig: new TextDecoder().decode(ims),
            recipient: recipient,
        }

        let path = `/identifiers/${name}/requests`
        let method = 'POST'
        let headers = new Headers({
            'Accept': 'application/json+cesr'

        })
        let res = await this.client.fetch(path, method, body, headers)
        return await res.text()

    }
}

/**
 * Registries
 */
export class Registries {
    public client: SignifyClient
    /**
     * Registries
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * List registries
     * @async
     * @param {string} name Name or alias of the identifier
     * @returns {Promise<any>} A promise to the list of registries
     */
    async list(name:string): Promise<any> {
        let path = `/identifiers/${name}/registries`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()

    }

    /**
     * Create a registry
     * @async
     * @param {string} name Name or alias of the identifier
     * @param {string} registryName Name for the registry
     * @param {string} [nonce] Nonce used to generate the registry. If not provided a random nonce will be generated
     * @returns {Promise<any>} A promise to the long-running operation
     */
    async create(name: string, registryName: string, nonce?:string): Promise<any> {
        // TODO add backers option
        // TODO get estOnly from get_identifier ?

        let hab = await this.client.identifiers().get(name)
        let pre: string = hab.prefix

        nonce = nonce !== undefined ? nonce : randomNonce()

        const vs = versify(Ident.KERI, undefined, Serials.JSON, 0)
        let vcp = {
            v: vs,
            t: Ilks.vcp,
            d: "",
            i: "",
            ii: pre,
            s: "0",
            c: ['NB'],
            bt: "0",
            b: [],
            n: nonce
        }

        let prefixer = new Prefixer({code: MtrDex.Blake3_256}, vcp)
        vcp.i = prefixer.qb64
        vcp.d = prefixer.qb64

        let ixn = {}
        let sigs = []

        let state = hab.state
        let estOnly = false
        if (state.c !== undefined && state.c.includes("EO")) {
            estOnly = true
        }

        if (estOnly) {
            // TODO implement rotation event
            throw new Error("establishment only not implemented")

        } else {
            let state = hab.state
            let sn = Number(state.s)
            let dig = state.d

            let data: any = [{
                i: prefixer.qb64,
                s: "0",
                d: prefixer.qb64
            }]

            let serder = interact({pre: pre, sn: sn + 1, data: data, dig: dig, version: undefined, kind: undefined})
            let keeper = this.client!.manager!.get(hab)
            sigs = keeper.sign(b(serder.raw))
            ixn = serder.ked
        }

        return await this.createFromEvents(hab, name, registryName, vcp, ixn, sigs)
    }

    async createFromEvents(hab: Dict<any>, name: string, registryName: string, vcp: Dict<any>, ixn: Dict<any>, sigs: any[]) {

        let path = `/identifiers/${name}/registries`
        let method = 'POST'

        let data: any = {
            name: registryName,
            vcp: vcp,
            ixn: ixn!,
            sigs: sigs
        }
        let keeper = this.client!.manager!.get(hab)
        data[keeper.algo] = keeper.params()

        let res = await this.client.fetch(path, method, data)
        return await res.json()
    }

}
/**
 * Schemas
 */
export class Schemas {
    client: SignifyClient
    /**
     * Schemas
     * @param {SignifyClient} client 
     */
    constructor(client: SignifyClient) {
        this.client = client
    }

    /**
     * Get a schema
     * @async
     * @param {string} said SAID of the schema
     * @returns {Promise<any>} A promise to the schema
     */
    async get(said: string): Promise<any> {
        let path = `/schema/${said}`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()
    }

    /**
     * List schemas
     * @async
     * @returns {Promise<any>} A promise to the list of schemas
     */
    async list(): Promise<any> {
        let path = `/schema`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null)
        return await res.json()
    }
}
