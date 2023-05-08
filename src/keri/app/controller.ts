import {SaltyCreator} from "../core/manager";
import {Salter, Tier} from "../core/salter";
import {MtrDex} from "../core/matter";
import {Diger} from "../core/diger";
import {incept} from "../core/eventing";
import {Serder} from "../core/serder";
import {Signer} from "../core/signer";
import {Verfer} from "../core/verfer";


export class Controller {
    /*
    *   Controller is responsible for managing signing keys for the client and agent.  The client
    *   signing key represents the Account for the client on the agent
    *
    */
    private bran: string;
    private stem: string;
    private salter: any;
    private signer: any;
    private nsigner: any;
    private serder: Serder;

    constructor(bran: string, tier: Tier, ridx: number = 0) {
        this.bran = MtrDex.Salt_128 + 'A' + bran.substring(0, 21)  // qb64 salt for seed
        this.stem = "signify:controller"

        this.salter = new Salter({qb64: this.bran})

        let creator = new SaltyCreator(this.salter.qb64, tier, this.stem)

        this.signer = creator.create(undefined, 1, MtrDex.Ed25519_Seed, true, 0, ridx, 0, false).signers.pop()
        this.nsigner = creator.create(undefined, 1, MtrDex.Ed25519_Seed, true, 0, ridx+1, 0, false).signers.pop()

        let verfers = Array.from(this.signer, (signer: Signer) => signer.verfer)
        let digers = Array.from(this.nsigner, (signer: Signer) => new Diger({code: MtrDex.Blake3_256}, signer.verfer.qb64b))

        let keys = Array.from(verfers, (verfer: Verfer) => verfer.qb64)
        let ndigs = Array.from(digers, (diger: Diger) => diger.qb64)

        this.serder = incept({
            keys: keys,
            isith: "1",
            nsith: "1",
            ndigs: ndigs,
            code: MtrDex.Blake3_256,
            toad: "0",
            wits: []})
        console.log(this.serder.ked)

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