import { Controller, Agent } from "./controller"
import { Tier } from "../core/salter"
import { Authenticater } from "../core/authing"
import { KeyManager } from "../core/keeping"
import { Algos } from '../core/manager';
import { incept, rotate, interact, reply } from "../core/eventing"
import { b, Serials, Versionage } from "../core/core";
import { Tholder } from "../core/tholder";
import { MtrDex } from "../core/matter";
import { TraitDex } from "./habery";

const KERIA_BOOT_URL = "http://localhost:3903"

export class CredentialTypes {
    static issued = "issued"
    static received = "received"
}

class State {
    agent: any | null
    controller: any | null
    ridx: number
    pidx: number

    constructor() {
        this.agent = null
        this.controller = null
        this.pidx = 0
        this.ridx = 0
    }
}

export class SignifyClient {
    public controller: Controller
    public url: string
    public bran: string
    public pidx: number
    public agent: Agent | null
    public authn: any
    public session: any
    public manager: KeyManager | null
    public tier: Tier

    constructor(url: string, bran: string, tier: Tier = Tier.low) {
        this.url = url;
        if (bran.length < 21) {
            throw Error("bran must be 21 characters")
        }
        this.bran = bran;
        this.pidx = 0;
        this.controller = new Controller(bran, tier)
        this.authn = null
        this.agent = null
        this.manager = null
        this.tier = tier

    }

    get data() {
        return [this.url, this.bran, this.pidx, this.authn]
    }

    async boot() {
        const [evt, sign] = this.controller?.event ?? [];
        const data = {
            icp: evt.ked,
            sig: sign.qb64,
            stem: this.controller?.stem,
            pidx: 1,
            tier: this.controller?.tier
        };
        let _url = this.url.includes("localhost") ? KERIA_BOOT_URL : this.url;
        const res = await fetch(_url + "/boot", {
            method: "POST",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        });

        return res;
    }

    async state(): Promise<State> {
        let caid = this.controller?.pre;
        let res = await fetch(this.url + `/agent/${caid}`);
        if (res.status == 404) {
            throw new Error(`agent does not exist for controller ${caid}`);
        }
        let data = await res.json();
        let state = new State();
        state.agent = data["agent"] ?? {};
        state.controller = data["controller"] ?? {};
        state.ridx = data["ridx"] ?? 0;
        state.pidx = data["pidx"] ?? 0;
        return state;
    }

    async connect() {
        let state = await this.state()
        this.pidx = state.pidx
        //Create controller representing local auth AID
        this.controller = new Controller(this.bran, this.tier, 0, state.controller)
        this.controller.ridx = state.ridx !== undefined ? state.ridx : 0
        // Create agent representing the AID of the cloud agent
        this.agent = new Agent(state.agent)
        if (this.agent.anchor != this.controller.pre) {
            throw Error("commitment to controller AID missing in agent inception event")
        }
        if (this.controller.serder.ked.s == 0) {
            await this.approveDelegation()
        }
        this.manager = new KeyManager(this.controller.salter, null)
        this.authn = new Authenticater(this.controller.signer, this.agent.verfer!)
    }

    async fetch(path: string, method: string, data: any, _headers: any) {
        //BEGIN Headers
        let headers = new Headers()
        headers.set('Signify-Resource', this.controller.pre)
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z', '000+00:00'))
        headers.set('Content-Type', 'application/json')

        if (data !== null) {
            headers.set('Content-Length', data.length)
        }
        else {
            headers.set('Content-Length', '0')
        }
        let signed_headers = this.authn.sign(headers, method, path.split('?')[0])
        //END Headers
        let _body = method == 'GET' ? null : JSON.stringify(data)

        //add _headers to signed_headers
        let final_headers = new Headers()
        for (let [key, value] of signed_headers.entries()) {
            final_headers.set(key, value)
        }
        if (_headers !== undefined) {
            for (let [key, value] of _headers.entries()) {
                final_headers.set(key, value)
            }
        }

        let res = await fetch(this.url + path, {
            method: method,
            body: _body,
            headers: final_headers
        });


        //BEGIN Verification
        if (!(res.status == 200 || res.status == 202)) {
            throw new Error('Response status is not 200');
        }
        const isSameAgent = this.agent?.pre === res.headers.get('signify-resource');
        if (!isSameAgent) {
            throw new Error('Message from a different remote agent');
        }

        const verification = this.authn.verify(res.headers, method, path.split('?')[0]);
        if (verification) {
            return res;
        } else {
            throw new Error('Response verification failed');
        }
    }

    async signedFetch(url: string, path: string, method: string, data: any, aidName: string) {
        const hab = await this.identifiers().get_identifier(aidName)
        const keeper = this.manager!.get(hab)

        const authenticator = new Authenticater(keeper.signers[0], keeper.signers[0].verfer)

        let headers = new Headers()
        headers.set('Signify-Resource', hab["prefix"])
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z', '000+00:00'))
        headers.set('Content-Type', 'application/json')

        if (data !== null) {
            headers.set('Content-Length', data.length)
        }
        else {
            headers.set('Content-Length', '0')
        }
        let signed_headers = authenticator.sign(headers, method, path.split('?')[0])
        let _body = method == 'GET' ? null : JSON.stringify(data)

        console.log(signed_headers)
        return await fetch(url + path, {
            method: method,
            body: _body,
            headers: signed_headers
        });

    }

    async approveDelegation() {
        let sigs = this.controller.approveDelegation(this.agent!)

        let data = {
            ixn: this.controller.serder.ked,
            sigs: sigs
        }

        await fetch(this.url + "/agent/" + this.controller.pre + "?type=ixn", {
            method: "PUT",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        })
    }

    identifiers() {
        return new Identifier(this)
    }

    oobis() {
        return new Oobis(this)
    }

    operations() {
        return new Operations(this)
    }

    key_events() {
        return new KeyEvents(this)
    }

    key_states() {
        return new KeyStates(this)
    }

    credentials() {
        return new Credentials(this)
    }

    registries() {
        return new Registries(this)
    }

    schemas() {
        return new Schemas(this)
    }

    challenges() {
        return new Challenges(this)
    }
}

class Identifier {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }
    //GET IdentifierCollectionEnd
    async list_identifiers() {
        let path = `/identifiers`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()
    }
    //GET  
    async get_identifier(name: string) {
        let path = `/identifiers/${name}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()
    }
    //POST
    async create(name: string,
        kargs: {
            transferable: boolean,
            isith: string,
            nsith: string,
            wits: string[],
            toad: string,
            proxy: string,
            delpre: string,
            dcode: string,
            data: any,
            algo: string,
            pre: string,
            states: any[],
            rstates: any[]
            prxs: any[],
            nxts: any[],
            mhab: any,
            keys: any[],
            ndigs: any[],
            bran: string,
            count: number,
            ncount: number
        }) {

        let algo = Algos.salty
        switch (kargs["algo"]) {
            case "salty":
                algo = Algos.salty
                break;
            case "randy":
                algo = Algos.randy
                break;
            case "group":
                algo = Algos.group
                break;
            default:
                algo = Algos.salty
                break;
        }

        let transferable = kargs["transferable"] ?? true
        let isith = kargs["isith"] ?? "1"
        let nsith = kargs["nsith"] ?? "1"
        let wits = kargs["wits"] ?? []
        let toad = kargs["toad"] ?? "0"
        let dcode = kargs["dcode"] ?? MtrDex.Blake3_256
        let proxy = kargs["proxy"]
        let delpre = kargs["delpre"]
        let data = kargs["data"] != undefined ? [kargs["data"]] : []
        let pre = kargs["pre"]
        let states = kargs["states"]
        let rstates = kargs["rstates"]
        let prxs = kargs["prxs"]
        let nxts = kargs["nxts"]
        let mhab = kargs["mhab"]
        let _keys = kargs["keys"]
        let _ndigs = kargs["ndigs"]
        let bran = kargs["bran"]
        let count = kargs["count"]
        let ncount = kargs["ncount"]

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
            ncount: ncount
        }

        let keeper = this.client.manager!.new(algo, this.client.pidx, xargs)
        let [keys, ndigs] = keeper!.incept(transferable)
        wits = wits !== undefined ? wits : []
        if (delpre == undefined) {
            var serder = incept({
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
            var serder = incept({
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
            smids: states != undefined ? states.map(state => state['i']) : undefined,
            rmids: rstates != undefined ? rstates.map(state => state['i']) : undefined
        }
        jsondata[algo] = keeper.params(),

        this.client.pidx = this.client.pidx + 1
        let res = await this.client.fetch("/identifiers", "POST", jsondata, undefined)
        return res.json()
    }
    //PUT IdentifierResourceEnd
    async interact(name: string, data: any | undefined = undefined) {

        let hab = await this.get_identifier(name)
        let pre: string = hab["prefix"]

        let state = hab["state"]
        let sn = Number(state["s"])
        let dig = state["d"]

        data = Array.isArray(data) ? data : [data]

        let serder = interact({ pre: pre, sn: sn + 1, data: data, dig: dig, version: undefined, kind: undefined })
        let keeper = this.client!.manager!.get(hab)
        let sigs = keeper.sign(b(serder.raw))

        let jsondata: any = {
            ixn: serder.ked,
            sigs: sigs,
        }
        jsondata[keeper.algo] = keeper.params()

        let res = await this.client.fetch("/identifiers/" + name + "?type=ixn", "PUT", jsondata, undefined)
        return res.json()

    }
    //PUT IdentifierResourceEnd
    async rotate(
        name: string,
        kargs: {
            transferable: boolean,
            nsith: string,
            toad: number,
            cuts: string[],
            adds: string[],
            data: Array<object>,
            ncode: string,
            ncount: number,
            ncodes: string[],
            states: any[],
            rstates: any[]
        }) {

        let transferable = kargs["transferable"] ?? true
        let ncode = kargs["ncode"] ?? MtrDex.Ed25519_Seed
        let ncount = kargs["ncount"] ?? 1


        let hab = await this.get_identifier(name)
        let pre = hab["prefix"]

        let state = hab["state"]
        let count = state['k'].length
        let dig = state["d"]
        let ridx = (Number(state["s"]) + 1)
        let wits = state['b']
        let isith = state["kt"]

        let nsith = kargs["nsith"] ?? isith


        // if isith is None:  # compute default from newly rotated verfers above
        if (isith == undefined) isith = `${Math.max(1, Math.ceil(count / 2)).toString(16)}`

        // if nsith is None:  # compute default from newly rotated digers above
        if (nsith == undefined) nsith = `${Math.max(1, Math.ceil(ncount / 2)).toString(16)}`

        let cst = new Tholder(isith).sith  // current signing threshold
        let nst = new Tholder(nsith).sith  // next signing threshold

        // Regenerate next keys to sign rotation event
        let keeper = this.client.manager!.get(hab)
        // Create new keys for next digests
        let ncodes = kargs["ncodes"] ?? new Array(ncount).fill(ncode)

        let states = kargs["states"]
        let rstates = kargs["rstates"]
        let [keys, ndigs] = keeper!.rotate(ncodes, transferable, states, rstates)

        let cuts = kargs["cuts"] ?? []
        let adds = kargs["adds"] ?? []
        let data = kargs["data"] != undefined ? [kargs["data"]] : []
        let toad = kargs["toad"]
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
            smids: states != undefined ? states.map(state => state['i']) : undefined,
            rmids: rstates != undefined ? rstates.map(state => state['i']) : undefined
        }
        jsondata[keeper.algo] = keeper.params()

        let res = await this.client.fetch("/identifiers/" + name, "PUT", jsondata, undefined)
        return res.json()
    }
    //POST EndRoleCollectionEnd
    async addEndRole(name: string, role: string, eid: string | undefined) {
        const hab = await this.get_identifier(name)
        const pre = hab["prefix"]

        const rpy = this.makeEndRole(pre, role, eid)
        const keeper = this.client.manager!.get(hab)
        const sigs = keeper.sign(b(rpy.raw))

        const jsondata = {
            rpy: rpy.ked,
            sigs: sigs
        }

        let res = await this.client.fetch("/identifiers/" + name + "/endroles", "POST", jsondata, undefined)
        return res.json()

    }
    //POST /end/role/add
    makeEndRole(pre: string, role: string, eid: string | undefined) {
        const data: any = {
            cid: pre,
            role: role
        }
        if (eid != undefined) {
            data["eid"] = eid
        }
        const route = "/end/role/add"
        return reply(route, data, undefined, undefined, Serials.JSON)

    }

}

class Oobis {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }

    async get(name: string, role: string = 'agent') {
        let path = `/identifiers/${name}/oobis?role=${role}`
        let data = null
        let method = 'GET'
        console.log('this.client', this.client)
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }

    async resolve(oobi: string, alias?: string) {
        let path = `/oobis`
        let data: any = {
            url: oobi
        }
        if (alias !== undefined) {
            data['alias'] = alias
        }
        let method = 'POST'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }
}

class Operations {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }

    async get(name: string) {
        let path = `/operations/${name}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }
}

class KeyEvents {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }

    async get(pre: string) {
        let path = `/events?pre=${pre}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }
}

class KeyStates {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }

    async get(pre: string) {
        let path = `/states?pre=${pre}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }

    async list(pres: [string]) {
        let path = `/states?${pres.map(pre => `pre=${pre}`).join('&')}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }

    async query(pre: string, sn?: number, anchor?: string) {
        let path = `/queries`
        let data: any = {
            pre: pre
        }
        if (sn !== undefined) {
            data['sn'] = sn
        }
        if (anchor !== undefined) {
            data['anchor'] = anchor
        }

        let method = 'POST'
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()

    }
}

class Credentials {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }
    //CredentialCollectionEnd
    //todo rename to list_credentials
    async list(aid: string, typ: CredentialTypes, schema: string) {
        let path = `/aids/${aid}/credentials`
        //if type is not in the credential types, throw an error
        if (!Object.values(CredentialTypes).includes(typ)) {
            throw new Error("Invalid Credential Type")
        }
        //add typ and schema as query params
        let params = new URLSearchParams()
        params.append('type', typ.toString())
        if (schema !== '') {
            params.append('schema', schema)
        }
        path = path + '?' + params.toString()

        let method = 'GET'

        let res = await this.client.fetch(path, method, null, undefined)
        return await res.json()
    }
    //CredentialResourceEnd
    //rename get_credential 
    async export(aid: string, said: string) {
        let path = `/aids/${aid}/credentials/${said}`
        let method = 'GET'
        let headers = new Headers({
            'Accept': 'application/json+cesr'
            
        })
        let res = await this.client.fetch(path, method, null, headers)
        return await res.text()

    }


}

class Registries {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }

    async list() {
        let path = `/registries`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null, undefined)
        return await res.json()

    }
    async create(name : string, alias : string, toad : number, nonce : string, baks : [string], estOnly : boolean, noBackers : string = TraitDex.NoBackers) {
        let path = `/registries`
        let method = 'POST'
        let data = {
            name: name,
            alias: alias,
            toad: toad,
            nonce: nonce,
            noBackers: noBackers,
            baks: baks,
            estOnly: estOnly
        }
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()
    }
    
}

class Schemas {
    client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }
    //SchemaResourceEnd 
    async get_schema(said:string) {
        let path = `/schemas/${said}`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null, undefined)
        return await res.json()
    }

    //SchemaCollectionEnd

    async list_all_schemas() {
        let path = `/schemas`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null, undefined)
        return await res.json()
    }


        
}

class Challenges {
    client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }
    //ChallengeCollectionEnd
    async get_challenge(strength:number) {
        let path = `/challenges/${strength.toString()}`
        let method = 'GET'
        let res = await this.client.fetch(path, method, null, undefined)
        return await res.json()
    }
    //ChallengeResourceEnd
    async send_challenge(name:string, recipient: string, words: [string], exn: string, sig: string) {
        let path = `/challenges/${name}`
        let method = 'POST'
        let data = {
            recipient: recipient,
            words: words,
            exn: exn,
            sig: sig
        }
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()
    }
    //ChallengeResourceEnd
    async accept_challenge(name:string, aid: string, saids: [string]) {
        let path = `/challenges/${name}`
        let method = 'PUT'
        let data = {
            aid: aid,
            saids: saids
        }
        let res = await this.client.fetch(path, method, data, undefined)
        return await res.json()
    }

}