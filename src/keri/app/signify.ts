import { Controller, Agent } from "./controller"
import { Tier } from "../core/salter"
import { Authenticater } from "../core/authing"
// import {Signage, signature} from "../end/ending";

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
    private controller: Controller
    private url: string
    private bran: string
    private pidx: number
    private agent: Agent | null
    public authn: any
    public session: any

    constructor(url: string, bran: string) {
        this.url = url;
        if (bran.length < 21) {
            throw Error("bran must be 21 characters")
        }
        this.bran = bran;
        this.pidx = 0;
        this.controller = new Controller(bran, Tier.low)
        this.authn = null
        this.agent = null

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
        this.controller = new Controller(this.bran, Tier.low, 0, state.controller)
        this.controller.ridx = state.ridx !== undefined ? state.ridx : 0
        // Create agent representing the AID of the cloud agent
        this.agent = new Agent(state.agent)
        if (this.agent.anchor != this.controller.pre) {
            throw Error("commitment to controller AID missing in agent inception event")
        }

        if (this.controller.serder.ked.s == 0 ) {
            await this.approveDelegation()
        }

        this.authn = new Authenticater(this.controller.signer, this.agent.verfer!)
    }

    async fetch(path: string, method: string, data: any) {
        //BEGIN Headers
        let headers = new Headers()
        headers.set('Signify-Resource', this.controller.pre)
        headers.set('Signify-Timestamp', new Date().toISOString().replace('Z','000+00:00'))

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

        const verification = this.authn.verify(res.headers, 'GET', path);
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

    async rotate(new_bran : string, aids: any[]){
        let data = this.controller.rotate(new_bran, aids)
        let caid = this.controller?.pre;
        let resp = await this.fetch(`/agent/${caid}`, 'PUT', data)
        return resp.status == 204
    }

    async _save_old_salt(salt: string){
        let caid = this.controller?.pre;
        let data = {
            salt: salt
        }
        let resp = await this.fetch(`/agent/${caid}/salt`, 'PUT', data)
        return resp.status == 204
    }

    async _delete_old_salt(){
        let caid = this.controller?.pre;
        let resp = await this.fetch(`/agent/${caid}/salt`, 'DELETE', null)
        return resp.status == 204
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

    // def create(self, name, transferable=True, isith="1", nsith="1", wits=None, toad="0", proxy=None, delpre=None,
    //            dcode=MtrDex.Blake3_256, data=None, algo=Algos.salty, **kwargs):

    //     # Get the algo specific key params
    //     keeper = self.client.manager.new(algo, self.client.pidx, **kwargs)

    //     keys, ndigs = keeper.incept(transferable=transferable)

    //     wits = wits if wits is not None else []
    //     data = [data] if data is not None else []
    //     if delpre is not None:
    //         serder = eventing.delcept(delpre=delpre,
    //                                   keys=keys,
    //                                   isith=isith,
    //                                   nsith=nsith,
    //                                   ndigs=ndigs,
    //                                   code=dcode,
    //                                   wits=wits,
    //                                   toad=toad,
    //                                   data=data)
    //     else:
    //         serder = eventing.incept(keys=keys,
    //                                  isith=isith,
    //                                  nsith=nsith,
    //                                  ndigs=ndigs,
    //                                  code=dcode,
    //                                  wits=wits,
    //                                  toad=toad,
    //                                  data=data)

    //     sigs = keeper.sign(serder.raw)

    //     json = dict(
    //         name=name,
    //         icp=serder.ked,
    //         sigs=sigs,
    //         proxy=proxy)
    //     json[algo] = keeper.params()

    //     if 'states' in kwargs:
    //         json['smids'] = [state['i'] for state in kwargs['states']]

    //     if 'rstates' in kwargs:
    //         json['rmids'] = [state['i'] for state in kwargs['rstates']]

    //     self.client.pidx = self.client.pidx + 1

    //     res = self.client.post("/identifiers", json=json)
    //     return res.json()



}
