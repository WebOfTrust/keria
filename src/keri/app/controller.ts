import { SaltyCreator } from "../core/manager";
import { Salter, Tier } from "../core/salter";
import { MtrDex } from "../core/matter";
import { Diger } from "../core/diger";
import { incept } from "../core/eventing";
import { Serder } from "../core/serder";
// import { Siger } from "../core/siger";
import { Tholder } from "../core/tholder";
import { Ilks } from "../core/core";
import { Verfer } from "../core/verfer";

export class Agent {
    pre: string;
    anchor: string;
    verfer: Verfer | null;
    serder: Serder | null;

    constructor(agent: any) {
        this.pre = "";
        this.anchor = "";
        this.verfer = null;
        this.serder = null;
        this.parse(agent);
    }

    parse(agent: any) {
        // if (kel.length < 1) {
        //     throw new Error("invalid empty KEL");
        // }

        let [serder, verfer, ] = this.event(agent);
        if (serder.ked['et'] !== Ilks.dip) {
            throw new Error(`invalid inception event type ${serder.ked['et']}`);
        }

        this.pre = serder.pre;
        if (!serder.ked['di']) {
            throw new Error("no anchor to controller AID");
        }

        this.anchor = serder.ked['di'];
        // for (let evt of kel.kel.slice(1)) {
        // for (let evt of state.controller.slice(1)) {
        //     let [rot, nverfer, ndiger] = this.event(evt);
        //     if (rot.ked['t'] !== Ilks.rot) {
        //         throw new Error(`invalid rotation event type ${serder.ked['t']}`);
        //     }

        //     if (new Diger({ qb64b: nverfer.qb64b }).qb64b !== diger.qb64b) {
        //         throw new Error(`next key mismatch error on rotation event ${serder}`);
        //     }

        //     verfer = nverfer;
        //     diger = ndiger;
        // }

        this.verfer = verfer
        this.serder = serder
    }

    event(evt: any): [Serder, Verfer, Diger] {
        let serder = new Serder(evt);
        // let siger = new Siger({ qb64: evt["sig"] });

        if (serder.verfers.length !== 1) {
            throw new Error(`agent inception event can only have one key`);
        }

        // if (!serder.verfers[0].verify(siger.raw, serder.raw)) {
        //     throw new Error(`invalid signature on evt ${serder.ked['d']}`);
        // }

        let verfer = serder.verfers[0];

        if (serder.digers.length !== 1) {
            throw new Error(`agent inception event can only have one next key`);
        }

        let diger = serder.digers[0];

        let tholder = new Tholder(serder.ked["kt"]);
        if (tholder.num !== 1) {
            throw new Error(`invalid threshold ${tholder.num}, must be 1`);
        }

        let ntholder = new Tholder(serder.ked["nt"]);
        if (ntholder.num !== 1) {
            throw new Error(`invalid next threshold ${ntholder.num}, must be 1`);
        }
        return [serder, verfer, diger];
    }
}
export class Controller {
    /*
    *   Controller is responsible for managing signing keys for the client and agent.  The client
    *   signing key represents the Account for the client on the agent
    *
    */
    private bran: string;
    public stem: string;
    public tier: Tier;
    public ridx: number;
    private salter: any;
    public signer: any;
    private nsigner: any;
    public serder: Serder;

    constructor(bran: string, tier: Tier, ridx: number = 0, state: any|null = null) {
        this.bran = MtrDex.Salt_128 + 'A' + bran.substring(0, 21)  // qb64 salt for seed
        this.stem = "signify:controller"
        this.tier = tier
        this.ridx = ridx

        this.salter = new Salter({ qb64: this.bran })

        let creator = new SaltyCreator(this.salter.qb64, tier, this.stem)

        this.signer = creator.create(undefined, 1, MtrDex.Ed25519_Seed, true, 0, this.ridx, 0, false).signers.pop()
        this.nsigner = creator.create(undefined, 1, MtrDex.Ed25519_Seed, true, 0, this.ridx + 1, 0, false).signers.pop()
        let keys = [this.signer.verfer.qb64]
        let ndigs = [new Diger({ code: MtrDex.Blake3_256 }, this.nsigner.verfer.qb64b).qb64]

        if (state == null || state['ee']['s'] == 0){
            this.serder = incept({
                keys: keys,
                isith: "1",
                nsith: "1",
                ndigs: ndigs,
                code: MtrDex.Blake3_256,
                toad: "0",
                wits: []
            })
        } else {
            this.serder = new Serder(state['ee'])
        }
    }

    approveDelegation(agent: Agent) {
        console.log(agent.pre)
        // TODO implement interact in eventing and seqner

        // seqner = coring.Seqner(sn=agent.sn)
        // anchor = dict(i=agent.pre, s=seqner.snh, d=agent.said)

        // self.serder = eventing.interact(pre=self.serder.pre, dig=self.serder.said, sn=self.serder.sn+1, data=[anchor])
        // return self.serder, [self.signer.sign(self.serder.raw, index=0).qb64]

        // FAKE SIGNATURE
        return ["AAD6nSSSGy_uO41clzL-g3czC8W0Ax-2M87NXA_Iu50ZdEhbekuv2k7dY0fjoO3su3aBRBx4EXryPc8x4uGfbVYG"]
    }

    get pre(): string {
        return this.serder.pre
    }

    get event() {
        let siger = this.signer.sign(this.serder.raw, 0)
        return [this.serder, siger]
    }

    get verfers(): [] {
        return this.signer.verfer()
    }
}