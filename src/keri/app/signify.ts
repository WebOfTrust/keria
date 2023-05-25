import { Controller, Agent } from "./controller"
import { Tier } from "../core/salter"
import { Authenticater } from "../core/authing"
import { Manager } from "../core/keeping"
import { Algos } from '../core/manager';
import { incept } from "../core/eventing"
import { b, Serials, Versionage } from "../core/core";

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
    public manager: Manager | null
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
        let _url = this.url.includes("3903") ? this.url : "http://localhost:3903";
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

        if (this.controller.serder.ked.s == 0 ) {
            await this.approveDelegation()
        }
        this.manager = new Manager(this.controller.salter, null)
        this.authn = new Authenticater(this.controller.signer, this.agent.verfer!)
    }

    async fetch(path: string, method: string, data: any) {
        //BEGIN Headers
        let headers = new Headers()
        headers.set('Signify-Resource', this.controller.pre)
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z','000+00:00'))
        headers.set('Content-Type', 'application/json')

        if (data !== null) {
            headers.set('Content-Length', data.length)
        }
        else {
            headers.set('Content-Length', '0')
        }
        let signed_headers = this.authn.sign(headers, method, path)
        //END Headers
        let _body = method == 'GET' ? null : JSON.stringify(data)
        let res = await fetch(this.url + path, {
            method: method,
            body: _body,
            headers: signed_headers
        });
        //BEGIN Verification
        if (res.status !== 200) {
            throw new Error('Response status is not 200');
        }
        const isSameAgent = this.agent?.pre === res.headers.get('signify-resource');
        if (!isSameAgent) {
            throw new Error('Message from a different remote agent');
        }

        const verification = this.authn.verify(res.headers, method, path);
        if (verification) {
            return res;
        } else {
            throw new Error('Response verification failed');
        }
    }

    async approveDelegation(){
        // {
        // "ixn": {"v": "KERI10JSON00013a_", "t": "ixn", "d": "EA4YpgJavlrjDRIE5UdkM44wiGTcCTfsTayrAViCDV4s", "i": "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose", "s": "1", "p": "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose", "a": [{"i": "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei", "s": "0", "d": "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"}]}, 
        // "sigs": ["AAD6nSSSGy_uO41clzL-g3czC8W0Ax-2M87NXA_Iu50ZdEhbekuv2k7dY0fjoO3su3aBRBx4EXryPc8x4uGfbVYG"]
        // }
        let sigs = this.controller.approveDelegation(this.agent!)

        let data = {
            ixn: this.controller.serder.ked,
            sigs: sigs
        }
        
        await fetch(this.url + "/agent/"+ this.controller.pre+"?type=ixn", {
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
}

class Identifier {
    public client: SignifyClient
    constructor(client: SignifyClient) {
        this.client = client
    }

    async list_identifiers() {
        let path = `/identifiers`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()
    }

    async get_identifier(name: string) {
        let path = `/identifiers/${name}`
        let data = null
        let method = 'GET'
        console.log('this.client', this.client)
        let res = await this.client.fetch(path, method, data)
        return await res.json()
    }

    async create(
                name: string, 
                transferable:boolean, 
                isith:string, 
                nsith:string, 
                wits:string[], 
                toad:string, 
                proxy:string, 
                delpre:string| undefined, 
                dcode:string, 
                data:Array<object>, 
                algo:Algos,
                ...kargs:any) {

        let keeper = this.client.manager!.new( algo, this.client.pidx,kargs)
        let [keys, ndigs] = keeper!.incept(transferable)
        wits = wits !== undefined ? wits : []
        let _data = data !== undefined ? [data] : []
        if (delpre == undefined){
            var serder = incept({ 
                keys: keys, 
                isith: isith, 
                ndigs: ndigs, 
                nsith: nsith, 
                toad: toad, 
                wits: wits, 
                cnfg: [], 
                data: _data, 
                version: Versionage, 
                kind: Serials.JSON, 
                code: dcode,
                intive: false, 
                delpre})
            
        } else {
            var serder = incept({ 
                keys: keys, 
                isith: isith, 
                ndigs: ndigs, 
                nsith: nsith, 
                toad: toad, 
                wits: wits, 
                cnfg: [], 
                data: _data, 
                version: Versionage, 
                kind: Serials.JSON, 
                code: dcode,
                intive: false, 
                delpre})
        }

        let sigs = keeper!.sign(b(serder.raw))
        var jsondata = {
            name: name,
            icp: serder.ked,
            sigs: sigs,
            proxy: proxy,
            salty: keeper.params()
            }
        // jsondata[algo.toString()] = keeper.params()

        this.client.pidx = this.client.pidx + 1
        let res = await this.client.fetch("/identifiers", "POST", jsondata)
        return res.json()

    //     if 'states' in kwargs:
    //         json['smids'] = [state['i'] for state in kwargs['states']]

    //     if 'rstates' in kwargs:
    //         json['rmids'] = [state['i'] for state in kwargs['rstates']]

    //     self.client.pidx = self.client.pidx + 1

    //     res = self.client.post("/identifiers", json=json)
    //     return res.json()

        }

}
