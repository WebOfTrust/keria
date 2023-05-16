import { Controller } from "./controller";
import { Tier } from "../core/salter";
import { Authenticater } from "../core/authing";

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
    private readonly _ctrl?: Controller
    private url: string;
    private bran: string;
    private pidx: number;
    private agent: any;
    private authn: any;
    private ctrl: any;

    constructor(url: string, bran: string) {
        this.url = url;
        if (bran.length != 21) {
            throw Error("bran must be 21 characters")
        }
        this.bran = bran;

        this.pidx = 0;
        this._ctrl = new Controller(bran, Tier.low)

    }

    async connect() {
        let state = await this.state()
        this.pidx = state.pidx
        //Create controller representing local auth AID
        this.ctrl.ridx = state.ridx != undefined ? state.ridx : 0

        // Create agent representing the AID of the cloud agent
        // this.agent = Agent(kel=state.kel)

        if (this.agent.anchor != this.ctrl.pre) {
            throw Error("commitment to controller AID missing in agent inception event")
        }

        this.authn = new Authenticater(this.agent, this.ctrl)
        // this.session.auth = new SignifyAuth(this.authn)

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
        console.log(data);
        let state = new State();
        state.kel = data["kel"]?? {};
        state.ridx = data["ridx"] ?? null;
        state.pidx = data["pidx"] ?? 0;
        return state;
    }
    get controller() {
        return this._ctrl
    }

    get data() {
        return [this.url, this.bran, this.pidx, this.authn]
    }
}