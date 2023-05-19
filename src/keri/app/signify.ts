import { Controller, Agent } from "./controller";
import { Tier } from "../core/salter";
import { Authenticater } from "../core/authing";
// import {Signage, signature} from "../end/ending";

class State {
    kel?: any;
    ridx?: number;
    pidx: number;

    constructor() {
        this.kel = {}
        this.pidx = 0
        this.ridx = 0
    }
}

export class SignifyClient {
    private _ctrl: Controller
    private url: string;
    private bran: string;
    private pidx: number;
    private agent: any;
    public authn: any;
    public session: any;

    constructor(url: string, bran: string) {
        this.url = url;
        if (bran.length < 21) {
            throw Error("bran must be 21 characters")
        }
        this.bran = bran;
        this.pidx = 0;
        this._ctrl = new Controller(bran, Tier.low)
        this.authn = null;

    }
    get controller() {
        return this._ctrl
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
        state.kel = data["kel"] ?? {};
        state.ridx = data["ridx"] ?? 0;
        state.pidx = data["pidx"] ?? 0;
        return state;
    }

    async connect() {
        let state = await this.state()
        this.pidx = state.pidx
        //Create controller representing local auth AID
        this.controller.ridx = state.ridx !== undefined ? state.ridx : 0
        // Create agent representing the AID of the cloud agent
        this.agent = new Agent({ kel: state.kel })

        if (this.agent.anchor != this.controller?.pre) {
            throw Error("commitment to controller AID missing in agent inception event")
        }
        this.authn = new Authenticater(this.controller.signer, this.agent)
        // this.session.auth = new SignifyAuth(this.authn)
    }

    async fetch(path: string, method: string, data: any) {
        //BEGIN Headers
        let headers = new Headers()
        // let _h = [{    "accept": "*/*"},
        // {    "accept-language": "en-US},en"},
        // {    "sec-fetch-dest": "empty"},
        // {    "sec-fetch-mode": "no-cors"},
        // {    "sec-fetch-site": "same-site"},
        // {    "sec-gpc": "1"},
        // {    "Referer": "http://localhost:5173/"},
        // {    "Referrer-Policy": "strict-origin-when-cross-origin"}]
        // _h.forEach(h => {
        //     let [k, v] = Object.entries(h)[0]
        //     headers.set(k, v??"")
        // })

        headers.set('Signify-Resource', this.controller.pre)
        headers.set('Signify-Timestamp', new Date().toISOString())
        //Access-Control-Allow-Origin: https://localhost:3000
        // headers.set('Access-Control-Allow-Origin', '*')
        if (data !== null) {
            headers.set('Content-Length', data.length)
        }
        else {
            headers.set('Content-Length', '0')
        }
        let signed_headers = this.authn.sign(headers, method, path)
        //END Headers
        //body is empty if method is GET else is data
        let _body = method == 'GET' ? null : JSON.stringify(data)
        let res = await fetch(this.url + path, {
            // mode: 'no-cors',
            method: method,
            body: _body,
            headers: signed_headers
        });



        //BEGIN Verification
        // if (res.status == 200) {
        //     console.log(res)
        // }
        // else {
        //     throw Error('response status not 200')
        // }
        // let verification = this.authn.verify(res.headers, res.body, "GET", path)
        // if (verification) {
        //     return res
        // }
        // else {
        //     throw Error('response verification failed')
        // }
        //END Verification
        return res

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
        console.log('this.client', this.client)
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
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }

    async resolve(oobi: string, alias?: string) {
        let path = `/oobis`
        let data: any = {
            oobi: oobi
        }
        if (alias !== undefined) {
            data['alias'] = alias
        }
        let method = 'POST'
        let res = await this.client.fetch(path, method, data)
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
        let res = await this.client.fetch(path, method, data)
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
        let res = await this.client.fetch(path, method, data)
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
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }

    async list(pres: [string]) {
        let path = `/states?${pres.map(pre => `pre=${pre}`).join('&')}`
        let data = null
        let method = 'GET'
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }

    async query(pre: string, sn?: string, anchor?: string) {
        let path = `/oobis`
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
        let res = await this.client.fetch(path, method, data)
        return await res.json()

    }
}